"""
Invocation Tracker for Zoo Multi-Agent System.

Tracks active invocations with AbortController support for cancellation.
Provides per-thread tracking and invocation lifecycle management.
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Set


class InvocationStatus(Enum):
    """Status of an invocation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class InvocationRecord:
    """Record of a single invocation."""
    invocation_id: str
    token: str
    thread_id: str
    status: InvocationStatus
    created_at: float
    updated_at: float
    animals_involved: Set[str] = field(default_factory=set)
    depth: int = 0
    error: Optional[str] = None
    result: Optional[str] = None


class AbortController:
    """
    AbortController for signal-based cancellation.
    Similar to JavaScript's AbortController API.
    """
    
    def __init__(self):
        self._aborted = False
        self._reason: Optional[str] = None
        self._listeners: Set[str] = set()
    
    def abort(self, reason: str = "Aborted by user") -> None:
        """Abort the invocation."""
        self._aborted = True
        self._reason = reason
    
    def signal(self) -> "AbortSignal":
        """Get the abort signal."""
        return AbortSignal(self)
    
    def is_aborted(self) -> bool:
        """Check if aborted."""
        return self._aborted
    
    def get_reason(self) -> Optional[str]:
        """Get abort reason."""
        return self._reason


class AbortSignal:
    """Abort signal for cancellation."""
    
    def __init__(self, controller: AbortController):
        self._controller = controller
    
    def aborted(self) -> bool:
        """Check if signal is aborted."""
        return self._controller.is_aborted()
    
    def reason(self) -> Optional[str]:
        """Get abort reason."""
        return self._controller.get_reason()


class InvocationTracker:
    """
    Tracks all active invocations across threads.
    Thread-safe with per-thread tracking.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._invocations: Dict[str, InvocationRecord] = {}
        self._thread_invocations: Dict[str, Set[str]] = {}
        self._thread_depths: Dict[str, int] = {}
        self._abort_controllers: Dict[str, AbortController] = {}
    
    def create_invocation(
        self,
        token: str,
        thread_id: str,
        depth: int = 0,
        animals: Optional[Set[str]] = None,
    ) -> str:
        """
        Create a new invocation record.
        
        Args:
            token: Authentication token
            thread_id: Thread/conversation ID
            depth: Initial depth (0 for root)
            animals: Set of animal keys involved
            
        Returns:
            invocation_id
        """
        invocation_id = str(uuid.uuid4())
        now = time.time()
        
        with self._lock:
            record = InvocationRecord(
                invocation_id=invocation_id,
                token=token,
                thread_id=thread_id,
                status=InvocationStatus.PENDING,
                created_at=now,
                updated_at=now,
                animals_involved=animals or set(),
                depth=depth,
            )
            self._invocations[invocation_id] = record
            
            # Track by thread
            if thread_id not in self._thread_invocations:
                self._thread_invocations[thread_id] = set()
            self._thread_invocations[thread_id].add(invocation_id)
            
            # Initialize abort controller
            self._abort_controllers[invocation_id] = AbortController()
        
        return invocation_id
    
    def start_invocation(self, invocation_id: str) -> bool:
        """Mark invocation as in progress."""
        with self._lock:
            record = self._invocations.get(invocation_id)
            if record and record.status == InvocationStatus.PENDING:
                record.status = InvocationStatus.IN_PROGRESS
                record.updated_at = time.time()
                return True
        return False
    
    def complete_invocation(
        self,
        invocation_id: str,
        result: str,
    ) -> bool:
        """Mark invocation as completed."""
        with self._lock:
            record = self._invocations.get(invocation_id)
            if record and record.status == InvocationStatus.IN_PROGRESS:
                record.status = InvocationStatus.COMPLETED
                record.updated_at = time.time()
                record.result = result
                return True
        return False
    
    def fail_invocation(
        self,
        invocation_id: str,
        error: str,
    ) -> bool:
        """Mark invocation as failed."""
        with self._lock:
            record = self._invocations.get(invocation_id)
            if record and record.status == InvocationStatus.IN_PROGRESS:
                record.status = InvocationStatus.FAILED
                record.updated_at = time.time()
                record.error = error
                return True
        return False
    
    def abort_invocation(
        self,
        invocation_id: str,
        reason: str = "Aborted by user",
    ) -> bool:
        """
        Abort an invocation via its controller.
        
        Args:
            invocation_id: The invocation to abort
            reason: Abort reason
            
        Returns:
            True if invocation was in progress, False otherwise
        """
        with self._lock:
            record = self._invocations.get(invocation_id)
            if record and record.status == InvocationStatus.IN_PROGRESS:
                record.status = InvocationStatus.ABORTED
                record.updated_at = time.time()
                record.error = reason
                return True
        return False
    
    def get_invocation(self, invocation_id: str) -> Optional[InvocationRecord]:
        """Get invocation record by ID."""
        with self._lock:
            return self._invocations.get(invocation_id)
    
    def get_thread_invocations(self, thread_id: str) -> Set[str]:
        """Get all invocation IDs for a thread."""
        with self._lock:
            return self._thread_invocations.get(thread_id, set()).copy()
    
    def get_thread_depth(self, thread_id: str) -> int:
        """Get max depth for a thread."""
        with self._lock:
            return self._thread_depths.get(thread_id, 0)
    
    def update_thread_depth(self, thread_id: str, depth: int) -> None:
        """Update max depth for a thread."""
        with self._lock:
            current = self._thread_depths.get(thread_id, 0)
            self._thread_depths[thread_id] = max(current, depth)
    
    def get_thread_max_depth(self, thread_id: str) -> int:
        """Get max depth across all active invocations in thread."""
        with self._lock:
            max_depth = 0
            for inv_id in self._thread_invocations.get(thread_id, set()):
                record = self._invocations.get(inv_id)
                if record and record.depth > max_depth:
                    max_depth = record.depth
            return max_depth
    
    def is_aborted(self, invocation_id: str) -> bool:
        """Check if invocation is aborted."""
        with self._lock:
            controller = self._abort_controllers.get(invocation_id)
            if controller:
                return controller.is_aborted()
            record = self._invocations.get(invocation_id)
            return record and record.status == InvocationStatus.ABORTED
    
    def get_abort_controller(self, invocation_id: str) -> Optional[AbortController]:
        """Get abort controller for invocation."""
        with self._lock:
            return self._abort_controllers.get(invocation_id)
    
    def cleanup_thread(self, thread_id: str) -> None:
        """Clean up all invocations for a thread."""
        with self._lock:
            inv_ids = self._thread_invocations.pop(thread_id, set())
            for inv_id in inv_ids:
                self._invocations.pop(inv_id, None)
                self._abort_controllers.pop(inv_id, None)
    
    def get_active_count(self) -> int:
        """Get count of active (pending/in_progress) invocations."""
        with self._lock:
            return sum(
                1 for r in self._invocations.values()
                if r.status in (InvocationStatus.PENDING, InvocationStatus.IN_PROGRESS)
            )
    
    def get_all_invocations(self) -> Dict[str, InvocationRecord]:
        """Get all invocation records."""
        with self._lock:
            return self._invocations.copy()


# Global singleton
_invocation_tracker = InvocationTracker()


def get_invocation_tracker() -> InvocationTracker:
    """Get global invocation tracker instance."""
    return _invocation_tracker
