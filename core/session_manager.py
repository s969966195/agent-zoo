"""Session management for Zoo Multi-Agent System."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from core.config import get_config
from core.models import (
    AnimalMessage,
    AnimalSession,
    AnimalType,
    InvocationRecord,
    Session,
    Thread,
)


class SessionManager:
    """Manages multi-animal sessions and threads."""

    def __init__(self):
        self.config = get_config()
        self.sessions: Dict[str, Session] = {}
        self.threads: Dict[str, Thread] = {}
        self.invocations: Dict[str, InvocationRecord] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, title: str = "") -> Session:
        """Create a new multi-animal session."""
        async with self._lock:
            session = Session(title=title)
            self.sessions[session.id] = session
            # Initialize animal sessions
            for animal_id in AnimalType:
                session.animal_sessions[animal_id] = AnimalSession(
                    animal_id=animal_id,
                    session_id=session.id
                )
            return session

    async def add_message(self, message: AnimalMessage) -> None:
        """Add a message to the appropriate session and thread."""
        async with self._lock:
            if message.thread_id not in self.threads:
                # Create thread if it doesn't exist
                self.threads[message.thread_id] = Thread(
                    id=message.thread_id,
                    participant_animals=[message.animal_id]
                )

            thread = self.threads[message.thread_id]
            thread.last_message_at = datetime.utcnow()
            thread.messages.append(message)

            # Update session
            session_id = message.thread_id
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.messages.append(message)
                session.updated_at = datetime.utcnow()

                # Update animal session
                if message.animal_id in session.animal_sessions:
                    animal_session = session.animal_sessions[message.animal_id]
                    animal_session.messages.append(message)
                    animal_session.last_activity = datetime.utcnow()

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        return self.threads.get(thread_id)

    async def create_invocation(
        self,
        caller: AnimalType,
        target: AnimalType,
        request_data: Optional[Dict] = None
    ) -> InvocationRecord:
        """Create an invocation record."""
        async with self._lock:
            callback_token = str(uuid4())
            record = InvocationRecord(
                caller_animal=caller,
                target_animal=target,
                callback_token=callback_token,
                request_data=request_data or {}
            )
            self.invocations[record.id] = record
            return record

    async def complete_invocation(
        self,
        invocation_id: str,
        response_data: Dict,
        status: str = "completed"
    ) -> Optional[InvocationRecord]:
        """Mark an invocation as completed."""
        async with self._lock:
            if invocation_id in self.invocations:
                record = self.invocations[invocation_id]
                record.status = status
                record.completed_at = datetime.utcnow()
                record.response_data = response_data
                return record
            return None

    async def get_active_invocations(self, animal_id: AnimalType) -> List[InvocationRecord]:
        """Get all pending invocations for an animal."""
        async with self._lock:
            return [
                record for record in self.invocations.values()
                if record.target_animal == animal_id and record.status == "pending"
            ]

    async def clear_session(self, session_id: str) -> bool:
        """Clear a session and its related data."""
        async with self._lock:
            if session_id in self.sessions:
                session = self.sessions.pop(session_id)
                # Also clear thread
                if session_id in self.threads:
                    del self.threads[session_id]
                return True
            return False

    async def get_all_sessions(self) -> Dict[str, Session]:
        """Get all active sessions."""
        return self.sessions.copy()

    async def get_all_threads(self) -> Dict[str, Thread]:
        """Get all active threads."""
        return self.threads.copy()


# Global session manager instance
_session_manager: Optional[SessionManager] = None


async def get_session_manager() -> SessionManager:
    """Get or create the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


async def reset_session_manager() -> None:
    """Reset the global session manager (for testing)."""
    global _session_manager
    _session_manager = None
