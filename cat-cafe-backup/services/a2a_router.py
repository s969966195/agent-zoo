"""
Cat Café Multi-Agent System - A2A Router

Routes @mentions between agents for inter-agent communication.
"""

import uuid
import datetime
import sys
if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

from typing import (
    Optional,
    List,
    Dict,
    Set,
    Callable,
    AsyncGenerator,
    Any
)

from core.models import AgentMessage
from agents.base import AgentService
from services.invocation_tracker import (
    InvocationTracker,
    AbortController,
    AbortSignal,
    ActiveInvocation,
    get_invocation_tracker
)
from services.route_strategies import RouteStrategies
from utils.a2a_mentions import parse_a2a_mentions, normalize_agent_id


InvokeFn: TypeAlias = 'Callable[[str], AsyncGenerator[AgentMessage, None]]'


class ThreadWorklistRegistry:
    """Per-thread worklist for A2A routing."""
    
    def __init__(self):
        self._registry: Dict[str, Dict[str, List[str]]] = {}
    
    def register(self, thread_id: str) -> Dict[str, List[str]]:
        """Create new worklist reference for thread."""
        if thread_id not in self._registry:
            self._registry[thread_id] = {"list": []}
        return self._registry[thread_id]
    
    def get(self, thread_id: str) -> Optional[Dict[str, List[str]]]:
        """Get worklist reference."""
        return self._registry.get(thread_id)
    
    def delete(self, thread_id: str) -> None:
        """Remove worklist reference."""
        if thread_id in self._registry:
            del self._registry[thread_id]
    
    def enqueue_targets(
        self,
        thread_id: str,
        targets: List[str]
    ) -> bool:
        """Add targets to worklist (with deduplication)."""
        if thread_id not in self._registry:
            self.register(thread_id)
        
        current = self._registry[thread_id]["list"]
        added = False
        for target in targets:
            if target not in current:
                current.append(target)
                added = True
        return added
    
    def dequeue_targets(
        self,
        thread_id: str,
        count: int = 1
    ) -> List[str]:
        """Remove and return targets from worklist."""
        if thread_id not in self._registry:
            return []
        
        current = self._registry[thread_id]["list"]
        result = current[:count]
        self._registry[thread_id]["list"] = current[count:]
        return result
    
    def clear(self, thread_id: str) -> int:
        """Clear worklist for thread."""
        if thread_id in self._registry:
            count = len(self._registry[thread_id]["list"])
            self._registry[thread_id]["list"] = []
            return count
        return 0


class A2ARouter:
    """Route @mentions between agents."""
    
    def __init__(
        self,
        agent_services: Dict[str, AgentService],
        invocation_tracker: InvocationTracker,
        websocket_manager: Any
    ):
        self.agent_services = agent_services
        self.invocation_tracker = invocation_tracker
        self.websocket_manager = websocket_manager
        self.max_depth: int = 15
        self.thread_worklist_registry = ThreadWorklistRegistry()
        self._invocations: Dict[str, AsyncGenerator[AgentMessage, None]] = {}
    
    async def route_execution(
        self,
        thread_id: str,
        initial_agents: List[str],
        prompt: str,
        signal: Optional[AbortController] = None
    ) -> AsyncGenerator[AgentMessage, None]:
        """
        Execute agents in worklist, detecting @mentions in responses.
        
        Yields messages in real-time.
        Supports dynamic worklist growth from @mentions.
        """
        # Initialize worklist
        worklist: List[str] = list(initial_agents)
        depth = 0
        
        while worklist:
            # Check abort signal
            if signal and signal.aborted:
                yield AgentMessage(
                    type="done",
                    agent_id=None,
                    content="Execution cancelled by user",
                    thread_id=thread_id,
                )
                return
            
            # Check depth limit
            if depth >= self.max_depth:
                yield AgentMessage(
                    type="done",
                    agent_id=None,
                    content=f"Maximum depth ({self.max_depth}) reached",
                    thread_id=thread_id,
                )
                return
            
            # Get next agent from worklist
            agent_id = worklist.pop(0)
            
            if agent_id not in self.agent_services:
                continue
            
            # Invoke the agent
            async for msg in self.invoke_single_cat(
                agent_id=agent_id,
                thread_id=thread_id,
                prompt=prompt,
                parent_invocation_id=None
            ):
                # Check abort signal during streaming
                if signal and signal.aborted:
                    yield msg
                    yield AgentMessage(
                        type="done",
                        agent_id=None,
                        content="Execution cancelled by user",
                        thread_id=thread_id,
                    )
                    return
                
                yield msg
                
                # Parse mentions after completion (for text messages)
                if msg.type == "text" and msg.content:
                    mentions = parse_a2a_mentions(
                        text=msg.content,
                        current_agent=agent_id,
                        limit=2
                    )
                    
                    # Add mentioned agents to worklist
                    for mention in mentions:
                        if mention not in worklist and mention in self.agent_services:
                            worklist.append(mention)
            
            depth += 1
        
        yield AgentMessage(
            type="done",
            agent_id=None,
            content="All agents completed execution",
            thread_id=thread_id,
        )
    
    async def invoke_single_cat(
        self,
        agent_id: str,
        thread_id: str,
        prompt: str,
        parent_invocation_id: Optional[str] = None
    ) -> AsyncGenerator[AgentMessage, None]:
        """Invoke single agent with proper tracking."""
        agent_service = self.agent_services.get(agent_id)
        if not agent_service:
            yield AgentMessage(
                type="text",
                agent_id=agent_id,
                content=f"Error: Agent '{agent_id}' not found",
                thread_id=thread_id,
            )
            return
        
        # Register invocation
        controller = await self.invocation_tracker.start(
            thread_id=thread_id,
            agent_id=agent_id,
            parent_id=parent_invocation_id,
        )
        
        try:
            # Invoke agent
            async for msg in agent_service.invoke(
                prompt=prompt,
                thread_id=thread_id,
                callback_env={
                    "THREAD_ID": thread_id,
                    "AGENT_ID": agent_id,
                }
            ):
                yield msg
        except asyncio.CancelledError:
            yield AgentMessage(
                type="text",
                agent_id=agent_id,
                content="Agent invocation was cancelled",
                thread_id=thread_id,
            )
        except Exception as e:
            yield AgentMessage(
                type="text",
                agent_id=agent_id,
                content=f"Error: {str(e)}",
                thread_id=thread_id,
            )
        finally:
            # Mark invocation as complete (will be cleaned up by cleanup_thread)
            pass
    
    async def cancel_thread(self, thread_id: str) -> int:
        """Cancel all invocations in a thread."""
        return await self.invocation_tracker.cancel_thread(thread_id)
    
    async def complete_invocation(self, invocation_id: str) -> bool:
        """Mark invocation as complete."""
        return await self.invocation_tracker.cancel(invocation_id)
    
    def parse_mentions(self, content: str, current_agent: str) -> List[str]:
        """Parse @mentions from content."""
        return parse_a2a_mentions(
            text=content,
            current_agent=current_agent,
            limit=2
        )
    
    def get_active_agents(self, thread_id: str) -> Set[str]:
        """Get set of active agent IDs in thread."""
        agents = set()
        for agent_id, service in self.agent_services.items():
            # Check if this agent has active invocations
            if hasattr(self, '_invocations'):
                if agent_id in self._invocations:
                    agents.add(agent_id)
        return agents


# Global router instance
_router: Optional[A2ARouter] = None


def get_a2a_router(
    agent_services: Optional[Dict[str, AgentService]] = None,
    invocation_tracker: Optional[InvocationTracker] = None,
    websocket_manager: Optional[Any] = None
) -> A2ARouter:
    """Get or create the A2A router instance."""
    global _router
    
    if _router is None:
        if agent_services is None:
            raise ValueError("agent_services must be provided for initial creation")
        if invocation_tracker is None:
            invocation_tracker = get_invocation_tracker()
        
        _router = A2ARouter(
            agent_services=agent_services,
            invocation_tracker=invocation_tracker,
            websocket_manager=websocket_manager or None,
        )
    
    return _router


def reset_a2a_router() -> None:
    """Reset the global router (for testing)."""
    global _router
    _router = None
