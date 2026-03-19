"""
A2A Router for Zoo Multi-Agent System.

Routes @mentions between animals using:
- Worklist pattern for execution
- Depth limit enforcement
- Support for @雪球 @六六 @小黄
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from utils.a2a_mentions import (
    ANIMAL_CONFIGS,
    PATTERN_TO_ANIMAL,
    parse_a2a_mentions,
    get_animal_patterns,
)
from services.invocation_tracker import (
    InvocationTracker,
    InvocationRecord,
    AbortController,
    AbortSignal,
    get_invocation_tracker,
)
from services.mcp_callback_router import (
    get_callback_router,
    CallbackResponse,
)
from services.route_strategies import (
    RouteStrategy,
    SerialRouteStrategy,
    DynamicWorklistStrategy,
    create_strategy,
    RouteTask,
    RouteResult,
)


@dataclass
class A2AMessage:
    """Message for A2A routing."""
    content: str
    from_animal: str
    to_animals: List[str]
    invocation_id: str
    thread_id: str
    depth: int
    timestamp: datetime
    
    @classmethod
    def create(
        cls,
        content: str,
        from_animal: str,
        to_animals: List[str],
        invocation_id: str,
        thread_id: str,
        depth: int = 0,
    ) -> "A2AMessage":
        """Create an A2AMessage."""
        return cls(
            content=content,
            from_animal=from_animal,
            to_animals=to_animals,
            invocation_id=invocation_id,
            thread_id=thread_id,
            depth=depth,
            timestamp=datetime.now(),
        )


@dataclass
class RoutingDecision:
    """Result of a routing decision."""
    task: RouteTask
    handler: Optional[Callable]
    reason: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class A2ARouter:
    """
    Router for Animal-to-Animal messaging.
    
    Handles @mention parsing, worklist management, and depth-limited routing.
    """
    
    def __init__(
        self,
        depth_limit: int = 15,
        strategy: Optional[RouteStrategy] = None,
        tracker: Optional[InvocationTracker] = None,
    ):
        """
        Initialize the A2A router.
        
        Args:
            depth_limit: Maximum nesting depth for routing
            strategy: Strategy for executing routes
            tracker: Invocation tracker instance
        """
        self.depth_limit = depth_limit
        self.strategy = strategy or DynamicWorklistStrategy()
        self.tracker = tracker or get_invocation_tracker()
        
        self._handlers: Dict[str, Callable] = {}
        self._message_history: Dict[str, List[A2AMessage]] = {}
        self._pending_routes: Dict[str, List[RouteTask]] = {}
    
    def register_handler(
        self,
        animal_key: str,
        handler: Callable[[A2AMessage], Any],
    ) -> None:
        """Register a message handler for an animal."""
        self._handlers[animal_key] = handler
    
    def register_default_handler(
        self,
        handler: Callable[[A2AMessage], Any],
    ) -> None:
        """Register a default handler for animals without specific handlers."""
        self._handlers["_default"] = handler
    
    def route_message(
        self,
        content: str,
        from_animal: str,
        invocation_id: str,
        thread_id: str,
    ) -> List[RouteTask]:
        """
        Parse message and create routing tasks.
        
        Args:
            content: Message content with potential @mentions
            from_animal: Source animal key
            invocation_id: Current invocation ID
            thread_id: Thread ID
            
        Returns:
            List of routing tasks for mentioned animals
        """
        # Parse mentions from content
        to_animals = parse_a2a_mentions(content, from_animal)
        
        if not to_animals:
            return []
        
        # Get current depth
        current_depth = self.tracker.get_thread_depth(thread_id)
        
        # Check depth limit
        if current_depth >= self.depth_limit:
            return []  # Depth exceeded
        
        # Create routing tasks
        tasks = []
        for animal_key in to_animals:
            task = RouteTask(
                animal_key=animal_key,
                content=content,
                depth=current_depth + 1,
            )
            tasks.append(task)
        
        return tasks
    
    async def execute_routes(
        self,
        tasks: List[RouteTask],
        execute_fn: Optional[Callable[[RouteTask], Any]] = None,
    ) -> List[RouteResult]:
        """
        Execute routing tasks using configured strategy.
        
        Args:
            tasks: Tasks to execute
            execute_fn: Optional override execute function
            
        Returns:
            List of results
        """
        if not tasks:
            return []
        
        # Bind execute function if not provided
        execute_func = execute_fn or self._default_execute
        
        return await self.strategy.execute(tasks, execute_func)
    
    async def _default_execute(self, task: RouteTask) -> RouteResult:
        """Default execution handler."""
        # Check abort signal
        abort_controller = self.tracker.get_abort_controller(task.animal_key)
        if abort_controller and abort_controller.is_aborted():
            return RouteResult(
                animal_key=task.animal_key,
                success=False,
                error="Invocation aborted",
            )
        
        # Look up handler
        handler = self._handlers.get(task.animal_key)
        if not handler:
            handler = self._handlers.get("_default")
        
        if not handler:
            return RouteResult(
                animal_key=task.animal_key,
                success=False,
                error="No handler registered",
            )
        
        # Create message
        message = A2AMessage.create(
            content=task.content,
            from_animal="router",  # Router is source for internal routing
            to_animals=[task.animal_key],
            invocation_id=_generate_invocation_id(task.animal_key),
            thread_id=_extract_thread_id(task.animal_key),
            depth=task.depth,
        )
        
        try:
            # Execute handler
            result = handler(message)
            
            # Await if async
            if asyncio.iscoroutine(result):
                result = await result
            
            return RouteResult(
                animal_key=task.animal_key,
                success=True,
                response=str(result),
            )
        except Exception as e:
            return RouteResult(
                animal_key=task.animal_key,
                success=False,
                error=str(e),
            )
    
    async def route_with_callback(
        self,
        content: str,
        from_animal: str,
        invocation_id: str,
        thread_id: str,
        token: str,
    ) -> List[RouteResult]:
        """
        Route message and post responses via MCP callback.
        
        Args:
            content: Message content with @mentions
            from_animal: Source animal key
            invocation_id: Current invocation ID
            thread_id: Thread ID
            token: Authentication token
            
        Returns:
            List of routing results
        """
        # Create routing tasks
        tasks = self.route_message(
            content=content,
            from_animal=from_animal,
            invocation_id=invocation_id,
            thread_id=thread_id,
        )
        
        if not tasks:
            return []
        
        # Update thread depth
        max_depth = max(t.depth for t in tasks)
        self.tracker.update_thread_depth(thread_id, max_depth)
        
        # Execute routes
        results = await self.execute_routes(tasks)
        
        # Post results via callback
        callback_router = get_callback_router()
        
        for result in results:
            if result.success and result.response:
                callback_router.post_message(
                    invocation_id=invocation_id,
                    token=token,
                    content=(
                        f"[{result.animal_key}] {result.response}"
                    ),
                    role="assistant",
                    animal_sender=result.animal_key,
                )
        
        return results
    
    def cancel_invocation(self, invocation_id: str) -> bool:
        """Cancel an ongoing invocation."""
        # Find animals involved in this invocation
        animals = set()
        for record in self.tracker.get_all_invocations().values():
            if record.invocation_id == invocation_id:
                animals.update(record.animals_involved)
        
        # Abort each animal's invocation
        success = False
        for animal in animals:
            controller = self.tracker.get_abort_controller(animal)
            if controller:
                controller.abort(f"Invocation {invocation_id} cancelled")
                success = True
        
        return success
    
    def get_pending_routes(self, thread_id: str) -> List[RouteTask]:
        """Get pending routes for a thread."""
        return self._pending_routes.get(thread_id, [])
    
    def clear_pending_routes(self, thread_id: str) -> None:
        """Clear pending routes for a thread."""
        self._pending_routes.pop(thread_id, None)


def _generate_invocation_id(animal_key: str) -> str:
    """Generate invocation ID from animal key."""
    import hashlib
    hash_val = hashlib.md5(animal_key.encode()).hexdigest()[:8]
    return f"inv_{hash_val}"


def _extract_thread_id(animal_key: str) -> str:
    """Extract thread ID from animal key."""
    import hashlib
    hash_val = hashlib.md5(animal_key.encode()).hexdigest()[:8]
    return f"thread_{hash_val}"


# Global router instance
_default_router: Optional[A2ARouter] = None


def get_a2a_router(
    depth_limit: int = 15,
    strategy_name: str = "dynamic_worklist",
) -> A2ARouter:
    """Get or create global A2A router instance."""
    global _default_router
    
    if _default_router is None:
        strategy = create_strategy(strategy_name)
        _default_router = A2ARouter(
            depth_limit=depth_limit,
            strategy=strategy,
        )
    
    return _default_router


# Convenience functions for animals to use
async def route_mentions(
    content: str,
    from_animal: str,
    invocation_id: str,
    thread_id: str,
    token: str,
) -> List[RouteResult]:
    """Route @mentions in a message."""
    router = get_a2a_router()
    return await router.route_with_callback(
        content=content,
        from_animal=from_animal,
        invocation_id=invocation_id,
        thread_id=thread_id,
        token=token,
    )


async def route_message_to_animal(
    content: str,
    from_animal: str,
    to_animal: str,
    invocation_id: str,
    thread_id: str,
    token: str,
) -> RouteResult:
    """Route message to a specific animal."""
    router = get_a2a_router()
    
    # Create minimal task
    task = RouteTask(
        animal_key=to_animal,
        content=content,
        depth=0,
    )
    
    results = await router.execute_routes([task])
    return results[0] if results else RouteResult(
        animal_key=to_animal,
        success=False,
        error="No results returned",
    )


def cancel_routing(invocation_id: str) -> bool:
    """Cancel a routing operation."""
    router = get_a2a_router()
    return router.cancel_invocation(invocation_id)


def get_routing_status(thread_id: str) -> Dict[str, Any]:
    """Get routing status for a thread."""
    router = get_a2a_router()
    pending = router.get_pending_routes(thread_id)
    
    return {
        "thread_id": thread_id,
        "pending_count": len(pending),
        "pending_tasks": [{
            "animal_key": t.animal_key,
            "depth": t.depth,
            "content": t.content[:50] + "..." if len(t.content) > 50 else t.content,
        } for t in pending],
    }
