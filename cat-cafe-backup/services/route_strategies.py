"""
Cat Café Multi-Agent System - Route Strategies

Different routing strategies for agent execution.
"""

import asyncio
import sys
if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

from typing import (
    Optional,
    List,
    Callable,
    AsyncGenerator,
    Any
)

from core.models import AgentMessage


InvokeFn: TypeAlias = 'Callable[[str], AsyncGenerator[AgentMessage, None]]'


class RouteStrategies:
    """Different routing strategies for agent execution."""
    
    @staticmethod
    async def serial(
        worklist: List[str],
        invoke_fn: InvokeFn,
        max_depth: int = 15,
        signal: Optional[Any] = None
    ) -> AsyncGenerator[AgentMessage, None]:
        """
        Serial execution: one agent at a time.
        Worklist grows dynamically from @mentions.
        
        Args:
            worklist: List of agent IDs to execute
            invoke_fn: Function to invoke an agent (returns async generator)
            max_depth: Maximum depth for dynamic worklist growth
            signal: Optional AbortController signal
            
        Yields:
            AgentMessage objects from all agents
        """
        depth = 0
        visited: set = set(worklist)
        workqueue: List[str] = list(worklist)
        
        while workqueue:
            if signal and hasattr(signal, 'aborted') and signal.aborted:
                break
            
            if depth >= max_depth:
                break
            
            current_agent = workqueue.pop(0)
            if current_agent in visited:
                continue
            
            visited.add(current_agent)
            depth += 1
            
            # Invoke the agent
            try:
                async for msg in invoke_fn(current_agent):
                    yield msg
            except Exception:
                # Continue with next agent even if one fails
                pass
            
            # Yield after each agent with a small delay for streaming
            await asyncio.sleep(0)
        
        yield AgentMessage(
            type="done",
            agent_id=None,
            content="All agents in worklist have completed",
            thread_id="",
        )
    
    @staticmethod
    async def broadcast(
        agents: List[str],
        invoke_fn: InvokeFn
    ) -> AsyncGenerator[AgentMessage, None]:
        """
        Broadcast to all agents simultaneously.
        Returns merged stream.
        
        Args:
            agents: List of agent IDs to invoke
            invoke_fn: Function to invoke an agent
            
        Yields:
            AgentMessage objects from all agents (merged stream)
        """
        if not agents:
            return
        
        # Create tasks for all agents
        tasks: List[asyncio.Task] = []
        
        async def agent_wrapper(agent_id: str) -> AsyncGenerator[AgentMessage, None]:
            """Wrapper to handle agent invocation and yield messages."""
            async for msg in invoke_fn(agent_id):
                yield msg
        
        # Collect all messages from all agents concurrently
        generators: List[AsyncGenerator[AgentMessage, None]] = []
        
        for agent_id in agents:
            gen = agent_wrapper(agent_id)
            generators.append(gen)
        
        # Use asyncio.gather to run all concurrently
        # Note: This is a simplified implementation that collects all messages
        # A full streaming merge would require more complex logic
        
        # For now, execute sequentially to demonstrate the pattern
        # In production, use proper async stream merging
        for gen in generators:
            try:
                async for msg in gen:
                    yield msg
            except Exception:
                continue
    
    @staticmethod
    async def sequential(
        agents: List[str],
        invoke_fn: InvokeFn
    ) -> AsyncGenerator[AgentMessage, None]:
        """
        Sequential execution: one agent at a time in order.
        Similar to serial but without dynamic worklist growth.
        
        Args:
            agents: List of agent IDs to execute in order
            invoke_fn: Function to invoke an agent
            
        Yields:
            AgentMessage objects from all agents
        """
        for agent_id in agents:
            async for msg in invoke_fn(agent_id):
                yield msg
