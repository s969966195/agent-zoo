"""Cat Café multi-agent system - Abstract base class for agent services."""

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    import subprocess


class AgentMessage(BaseModel):
    """Unified message format for all cat agents."""
    
    role: str
    content: str
    thread_id: str
    session_id: Optional[str] = None
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentService(ABC):
    """Abstract base for all cat agents."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.process: Optional["subprocess.Popen[Any]"] = None
        self._current_task_id: Optional[str] = None
    
    @abstractmethod
    async def invoke(
        self,
        prompt: str,
        thread_id: str,
        session_id: Optional[str] = None,
        callback_env: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[AgentMessage, None]:
        """Invoke agent and stream response messages.
        
        Args:
            prompt: User prompt to send to the agent
            thread_id: Thread identifier for conversation context
            session_id: Optional session identifier for multi-turn conversations
            callback_env: Optional environment variables for callbacks
            
        Yields:
            AgentMessage objects streaming from the agent
        """
    
    @abstractmethod
    def get_cli_command(self) -> tuple[str, list[str]]:
        """Return (command, args) for spawning CLI.
        
        Returns:
            Tuple of (command_path, list_of_arguments)
        """
    
    @abstractmethod
    def transform_event(self, event: Dict[str, Any]) -> Optional[AgentMessage]:
        """Transform CLI-specific NDJSON event to unified AgentMessage.
        
        Args:
            event: Raw event dictionary from CLI output
            
        Returns:
            AgentMessage if event is a message, None if it's a control event
        """
    
    async def cancel(self) -> None:
        """Cancel active invocation."""
        if self.process is not None:
            try:
                self.process.terminate()
            except ProcessLookupError:
                pass  # Process already terminated
            except Exception:
                # Fallback to force kill
                try:
                    self.process.kill()
                except Exception:
                    pass


# Import subprocess after class definition
import subprocess
