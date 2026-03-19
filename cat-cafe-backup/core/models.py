"""
Cat Café Multi-Agent System - Core Models

Pydantic models for Cat Café's message passing and session management system.
"""

import uuid
import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """
    Represents a message sent between agents in the Cat Café system.
    
    Messages can be:
    - 'text': Normal text communication
    - 'tool_call': Request to execute a tool
    - 'tool_result': Result of tool execution
    - 'session_init': Session initialization message
    - 'done': Signal that agent has completed its task
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(..., description="Message type: text, tool_call, tool_result, session_init, done")
    agent_id: Optional[str] = Field(None, description="Sender agent ID: bollumao, mainemao, xianluomao")
    content: Optional[str] = Field(None, description="Message content for text messages")
    thread_id: str = Field(..., description="Thread ID this message belongs to")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    mentions: List[str] = Field(default_factory=list, description="List of agent IDs mentioned in this message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg-123",
                "type": "text",
                "agent_id": "bollumao",
                "content": "Hello, I'm Bollumao!",
                "thread_id": "thread-abc",
                "mentions": [],
                "metadata": {"priority": "normal"}
            }
        }


class Session(BaseModel):
    """
    Represents a conversation session in the Cat Café system.
    
    A session contains all messages exchanged between agents during
    a collaborative task and tracks CLI sessions for each participant.
    """
    id: str = Field(..., description="Unique session identifier")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, description="Session creation time")
    last_active: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, description="Last activity timestamp")
    messages: List[AgentMessage] = Field(default_factory=list, description="Messages in this session")
    agent_sessions: Dict[str, str] = Field(default_factory=dict, description="Mapping of agent_id to CLI session_id")
    
    def add_message(self, message: AgentMessage) -> None:
        """Add a message to the session and update last_active."""
        self.messages.append(message)
        self.last_active = datetime.datetime.utcnow()
    
    def get_agent_session_id(self, agent_id: str) -> Optional[str]:
        """Get the CLI session ID for an agent."""
        return self.agent_sessions.get(agent_id)
    
    def set_agent_session_id(self, agent_id: str, session_id: str) -> None:
        """Set the CLI session ID for an agent."""
        self.agent_sessions[agent_id] = session_id
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "session-123",
                "created_at": "2024-01-15T10:00:00Z",
                "last_active": "2024-01-15T10:05:00Z",
                "messages": [],
                "agent_sessions": {
                    "bollumao": "cli-session-bollumao-1",
                    "mainemao": "cli-session-mainemao-1"
                }
            }
        }


class InvocationRecord(BaseModel):
    """
    Tracks tool invocation requests between agents.
    
    When one agent needs another agent to execute a tool,
    an InvocationRecord is created to track the request.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caller_agent: Optional[str] = Field(None, description="Agent that initiated the invocation")
    target_agent: str = Field(..., description="Agent expected to execute the tool")
    thread_id: str = Field(..., description="Thread ID where this invocation occurs")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    callback_token: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Token for callback verification")
    status: str = Field(default="pending", description="Invocation status: pending, active, completed, cancelled")
    
    def complete(self) -> None:
        """Mark invocation as completed."""
        self.status = "completed"
    
    def cancel(self) -> None:
        """Cancel the invocation."""
        self.status = "cancelled"
    
    def activate(self) -> None:
        """Mark invocation as active (tool execution started)."""
        self.status = "active"
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "invocation-123",
                "caller_agent": "bollumao",
                "target_agent": "mainemao",
                "thread_id": "thread-abc",
                "callback_token": "token-xyz",
                "status": "pending"
            }
        }


class Thread(BaseModel):
    """
    Represents a discussion thread where multiple agents collaborate.
    
    A thread is the primary unit of collaboration - it contains all
    messages, invocations, and state for a specific topic or task.
    """
    id: str = Field(..., description="Unique thread identifier")
    title: str = Field(..., description="Thread title/description")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    last_message_at: Optional[datetime.datetime] = Field(None, description="Timestamp of last message")
    status: str = Field(default="active", description="Thread status: active, completed, archived")
    participant_agents: List[str] = Field(default_factory=list, description="List of agent IDs participating")
    current_invocation: Optional[str] = Field(None, description="ID of current active invocation, if any")
    
    def add_participant(self, agent_id: str) -> None:
        """Add an agent to the thread participants."""
        if agent_id not in self.participant_agents:
            self.participant_agents.append(agent_id)
    
    def remove_participant(self, agent_id: str) -> None:
        """Remove an agent from thread participants."""
        if agent_id in self.participant_agents:
            self.participant_agents.remove(agent_id)
    
    def update_last_message(self, timestamp: datetime.datetime) -> None:
        """Update the last message timestamp."""
        self.last_message_at = timestamp
    
    def activate_invocation(self, invocation_id: str) -> None:
        """Set the current active invocation."""
        self.current_invocation = invocation_id
    
    def clear_invocation(self) -> None:
        """Clear the current invocation."""
        self.current_invocation = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "thread-abc",
                "title": " Lunch Planning Discussion",
                "participant_agents": ["bollumao", "mainemao", "xianluomao"],
                "status": "active"
            }
        }


__all__ = [
    "AgentMessage",
    "Session",
    "InvocationRecord",
    "Thread"
]
