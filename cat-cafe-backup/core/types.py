"""
Cat Café Multi-Agent System - Core Types and Utilities
"""

import uuid
import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class CallbackToken:
    """Represents a token for callback authentication."""
    token: str
    agent_id: str
    thread_id: str
    created_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    expires_at: Optional[datetime.datetime] = None
    max_uses: Optional[int] = None
    current_uses: int = 0
    active: bool = True
    
    def is_valid(self) -> bool:
        """Check if token is still valid."""
        if not self.active:
            return False
        if self.expires_at and datetime.datetime.utcnow() > self.expires_at:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True
    
    def use(self) -> bool:
        """Mark token as used. Returns False if limit exceeded."""
        if not self.is_valid():
            return False
        self.current_uses += 1
        return True


@dataclass
class InvocationRecord:
    """
    Tracks tool invocation requests between agents.
    
    When one agent needs another agent to execute a tool,
    an InvocationRecord is created to track the request.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    caller_agent: Optional[str] = None
    target_agent: str = ""
    thread_id: str = ""
    callback_token: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"  # pending, active, completed, cancelled
    
    def complete(self) -> None:
        """Mark invocation as completed."""
        self.status = "completed"
    
    def cancel(self) -> None:
        """Cancel the invocation."""
        self.status = "cancelled"
    
    def activate(self) -> None:
        """Mark invocation as active (tool execution started)."""
        self.status = "active"


@dataclass
class AgentMessage:
    """
    Represents a message sent between agents in the Cat Café system.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""  # text, tool_call, tool_result, session_init, done
    agent_id: Optional[str] = None
    content: Optional[str] = None
    thread_id: str = ""
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    mentions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebSocketMessage:
    """Message sent via WebSocket."""
    type: str  # message, notification, system
    agent_id: Optional[str] = None
    content: Optional[str] = None
    thread_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
