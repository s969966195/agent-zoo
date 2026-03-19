"""
Cat Café Multi-Agent System - Invocation Tracker

Tracks active agent invocations for cancellation and thread management.
"""

import uuid
import datetime
import asyncio
from typing import Optional, Dict, Set, List
from dataclasses import dataclass, field


class AbortController:
    """AbortController for cancelling operations."""
    
    def __init__(self):
        self._aborted = False
        self._reason: Optional[str] = None
    
    @property
    def signal(self) -> 'AbortSignal':
        """Get the abort signal."""
        return AbortSignal(self)
    
    def abort(self, reason: Optional[str] = None) -> None:
        """Abort the operation."""
        self._aborted = True
        self._reason = reason


class AbortSignal:
    """Signal object that indicates whether an operation has been aborted."""
    
    def __init__(self, controller: AbortController):
        self._controller = controller
    
    @property
    def aborted(self) -> bool:
        """Check if operation has been aborted."""
        return self._controller._aborted
    
    def throw_if_aborted(self) -> None:
        """Raise an exception if operation has been aborted."""
        if self._controller._aborted:
            raise asyncio.CancelledError(
                f"Operation cancelled: {self._controller._reason or 'Unknown reason'}"
            )


@dataclass
class ActiveInvocation:
    """Represents an active agent invocation."""
    id: str
    thread_id: str
    agent_id: str
    controller: AbortController
    start_time: datetime.datetime
    parent_id: Optional[str] = None
    child_ids: Set[str] = field(default_factory=set)


class InvocationTracker:
    """Track active agent invocations for cancellation."""
    
    def __init__(self):
        self._active: Dict[str, ActiveInvocation] = {}
        self._by_thread: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
    
    async def start(
        self,
        thread_id: str,
        agent_id: str,
        parent_id: Optional[str] = None
    ) -> AbortController:
        """Register new invocation and return AbortController."""
        async with self._lock:
            invocation_id = str(uuid.uuid4())
            controller = AbortController()
            
            invocation = ActiveInvocation(
                id=invocation_id,
                thread_id=thread_id,
                agent_id=agent_id,
                controller=controller,
                start_time=datetime.datetime.utcnow(),
                parent_id=parent_id,
            )
            
            self._active[invocation_id] = invocation
            
            if thread_id not in self._by_thread:
                self._by_thread[thread_id] = set()
            self._by_thread[thread_id].add(invocation_id)
            
            if parent_id and parent_id in self._active:
                self._active[parent_id].child_ids.add(invocation_id)
            
            return controller
    
    async def cancel(self, invocation_id: str) -> bool:
        """Cancel specific invocation."""
        async with self._lock:
            if invocation_id not in self._active:
                return False
            
            invocation = self._active[invocation_id]
            invocation.controller.abort("Cancelled by user")
            
            for child_id in list(invocation.child_ids):
                if child_id in self._active:
                    self._active[child_id].controller.abort(
                        f"Parent {invocation_id} cancelled"
                    )
            
            thread_invocations = self._by_thread.get(invocation.thread_id)
            if thread_invocations:
                thread_invocations.discard(invocation_id)
                if not thread_invocations:
                    del self._by_thread[invocation.thread_id]
            
            del self._active[invocation_id]
            
            return True
    
    async def cancel_thread(self, thread_id: str) -> int:
        """Cancel all invocations in thread."""
        async with self._lock:
            cancelled_count = 0
            
            if thread_id not in self._by_thread:
                return 0
            
            invocation_ids = list(self._by_thread[thread_id])
            
            for invocation_id in invocation_ids:
                if await self.cancel(invocation_id):
                    cancelled_count += 1
            
            return cancelled_count
    
    async def has(self, thread_id: str) -> bool:
        """Check if thread has active invocations."""
        async with self._lock:
            return thread_id in self._by_thread and len(self._by_thread[thread_id]) > 0
    
    async def get_active_cats(self, thread_id: str) -> Set[str]:
        """Get set of active agent IDs in thread."""
        async with self._lock:
            if thread_id not in self._by_thread:
                return set()
            
            agent_ids: Set[str] = set()
            for invocation_id in self._by_thread[thread_id]:
                if invocation_id in self._active:
                    agent_ids.add(self._active[invocation_id].agent_id)
            
            return agent_ids
    
    async def get_all_active(self) -> Dict[str, ActiveInvocation]:
        """Get all active invocations."""
        async with self._lock:
            return dict(self._active)
    
    async def get_active_by_thread(self, thread_id: str) -> List[ActiveInvocation]:
        """Get all active invocations for a thread."""
        async with self._lock:
            result: List[ActiveInvocation] = []
            
            if thread_id not in self._by_thread:
                return result
            
            for invocation_id in self._by_thread[thread_id]:
                if invocation_id in self._active:
                    result.append(self._active[invocation_id])
            
            return result
    
    async def get_invocation(self, invocation_id: str) -> Optional[ActiveInvocation]:
        """Get specific invocation by ID."""
        async with self._lock:
            return self._active.get(invocation_id)
    
    async def get_child_invocations(self, parent_id: str) -> List[ActiveInvocation]:
        """Get all child invocations of a parent."""
        async with self._lock:
            result: List[ActiveInvocation] = []
            
            if parent_id not in self._active:
                return result
            
            parent = self._active[parent_id]
            for child_id in parent.child_ids:
                if child_id in self._active:
                    result.append(self._active[child_id])
            
            return result
    
    async def clear_all(self) -> None:
        """Cancel all active invocations."""
        async with self._lock:
            for invocation in self._active.values():
                invocation.controller.abort("System shutdown")
            
            self._active.clear()
            self._by_thread.clear()


_invocation_tracker: Optional[InvocationTracker] = None


def get_invocation_tracker() -> InvocationTracker:
    """Get or create the global invocation tracker instance."""
    global _invocation_tracker
    
    if _invocation_tracker is None:
        _invocation_tracker = InvocationTracker()
    
    return _invocation_tracker
