"""
Cat Café Multi-Agent System - Session Manager

Manages the lifecycle of conversation sessions in the Cat Café system.
"""

import uuid
import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict
import threading

from core.models import Session, AgentMessage, Thread
from core.config import settings
from storage.redis_client import redis_client


class SessionManager:
    """
    Manages session lifecycle including creation, persistence, and cleanup.
    
    Uses Redis for session caching with SQLite/PostgreSQL for persistence.
    """
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._threads: Dict[str, Thread] = {}
        self._lock = threading.RLock()
        self._session_created_callback = None
        self._session_closed_callback = None
    
    # Session management
    def create_session(
        self,
        session_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> Session:
        """Create a new session with optional thread association."""
        session_id = session_id or str(uuid.uuid4())
        
        with self._lock:
            session = Session(
                id=session_id,
                created_at=datetime.datetime.utcnow(),
                last_active=datetime.datetime.utcnow(),
            )
            self._sessions[session_id] = session
            
            if thread_id:
                thread = self.get_thread(thread_id)
                if thread:
                    session.agent_sessions = {
                        agent: session_id for agent in thread.participant_agents
                    }
            
            if self._session_created_callback:
                self._session_created_callback(session)
            
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        with self._lock:
            return self._sessions.get(session_id)
    
    def get_session_by_agent(self, agent_id: str) -> Optional[Session]:
        """Get session for a specific agent."""
        with self._lock:
            for session in self._sessions.values():
                if agent_id in session.agent_sessions.values():
                    return session
        return None
    
    def list_sessions(self) -> List[Session]:
        """List all active sessions."""
        with self._lock:
            return list(self._sessions.values())
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions.pop(session_id)
                if self._session_closed_callback:
                    self._session_closed_callback(session)
                return True
            return False
    
    def add_message_to_session(
        self,
        session_id: str,
        message: AgentMessage,
    ) -> bool:
        """Add a message to a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.add_message(message)
                return True
            return False
    
    # Thread management
    def create_thread(
        self,
        thread_id: Optional[str] = None,
        title: str = "New Discussion",
        participants: Optional[List[str]] = None,
    ) -> Thread:
        """Create a new discussion thread."""
        thread_id = thread_id or str(uuid.uuid4())
        participants = participants or []
        
        with self._lock:
            thread = Thread(
                id=thread_id,
                title=title,
                participant_agents=participants,
            )
            self._threads[thread_id] = thread
            return thread
    
    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        with self._lock:
            return self._threads.get(thread_id)
    
    def add_message_to_thread(
        self,
        thread_id: str,
        message: AgentMessage,
    ) -> bool:
        """Add a message to a thread."""
        with self._lock:
            thread = self._threads.get(thread_id)
            if thread:
                thread.add_message(message.timestamp)
                # Update session last_active
                for agent_id in thread.participant_agents:
                    for session in self._sessions.values():
                        if session.get_agent_session_id(agent_id):
                            session.last_active = datetime.datetime.utcnow()
                return True
            return False
    
    def list_threads(self) -> List[Thread]:
        """List all active threads."""
        with self._lock:
            return list(self._threads.values())
    
    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread."""
        with self._lock:
            if thread_id in self._threads:
                del self._threads[thread_id]
                return True
            return False
    
    # Callbacks
    def on_session_created(self, callback):
        """Register callback for session creation."""
        self._session_created_callback = callback
        return callback
    
    def on_session_closed(self, callback):
        """Register callback for session closing."""
        self._session_closed_callback = callback
        return callback
    
    # Serialization
    def to_dict(self) -> Dict[str, Any]:
        """Convert session manager state to dictionary."""
        with self._lock:
            return {
                "sessions": {
                    sid: session.model_dump() for sid, session in self._sessions.items()
                },
                "threads": {
                    tid: thread.model_dump() for tid, thread in self._threads.items()
                },
            }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionManager":
        """Create session manager from dictionary."""
        manager = cls()
        
        with manager._lock:
            for sid, session_data in data.get("sessions", {}).items():
                manager._sessions[sid] = Session(**session_data)
            
            for tid, thread_data in data.get("threads", {}).items():
                manager._threads[tid] = Thread(**thread_data)
        
        return manager


# Global singleton instance
session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    return session_manager


__all__ = [
    "SessionManager",
    "get_session_manager",
]
