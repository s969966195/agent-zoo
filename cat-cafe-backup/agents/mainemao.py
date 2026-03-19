"""Cat Café multi-agent system - Mainemao (Codex) agent implementation."""

import json
import subprocess
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, Optional

from agents.base import AgentMessage, AgentService

if TYPE_CHECKING:
    ProcessHandle = subprocess.Popen[Any]


class Mainemao(AgentService):
    """Codex agent via CLI.
    
    CLI command: codex exec "{prompt}" --json
    """
    
    def __init__(self, agent_id: str = "mainemao", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config or {})
        self.process: Optional[subprocess.Popen] = None
        self._current_message: Optional[Dict[str, Any]] = None
    
    def get_cli_command(self) -> tuple[str, list[str]]:
        """Return (command, args) for spawning Codex CLI."""
        return ("codex", ["exec", "--json"])
    
    def transform_event(self, event: Dict[str, Any]) -> Optional[AgentMessage]:
        """Transform Codex NDJSON event to unified AgentMessage.
        
        Codex JSON output format for 'exec --json':
        - { "type": "message", "content": "...", "role": "assistant" }
        - { "type": "tool", "name": "..." }
        - { "type": "status", "status": "..." }
        """
        event_type = event.get("type", "")
        
        if event_type == "message":
            return AgentMessage(
                role=event.get("role", "assistant"),
                content=event.get("content", ""),
                thread_id=event.get("thread_id", ""),
                session_id=event.get("session_id"),
            )
        elif event_type == "tool":
            # Tool execution event - could return as metadata
            content = f"[Tool: {event.get('name', 'unknown')}]"
            return AgentMessage(
                role="system",
                content=content,
                thread_id=event.get("thread_id", ""),
                session_id=event.get("session_id"),
                metadata={"tool": event.get("name")},
            )
        elif event_type == "status":
            # Status update - not a message, skip
            return None
        else:
            # Unknown event type - wrap in message
            return AgentMessage(
                role="system",
                content=json.dumps(event),
                thread_id="",
            )
    
    async def invoke(
        self,
        prompt: str,
        thread_id: str,
        session_id: Optional[str] = None,
        callback_env: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[AgentMessage, None]:
        """Invoke Codex CLI and stream responses.
        
        Args:
            prompt: User prompt to send to Codex
            thread_id: Thread identifier for conversation context
            session_id: Optional session identifier
            callback_env: Environment variables for callbacks
            
        Yields:
            AgentMessage objects streaming from Codex
        """
        command, args = self.get_cli_command()
        
        # Build command with prompt as argument
        full_args = [prompt] + list(args)
        
        # Set up environment
        env = callback_env or {}
        if self.config.get("api_key"):
            env["CODEX_API_KEY"] = self.config["api_key"]
        
        # Spawn process
        import asyncio
        
        self.process = await asyncio.to_thread(
            subprocess.Popen,
            [command] + full_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**env, "PYTHONUNBUFFERED": "1"},
        )
        
        try:
            # Read and parse NDJSON output
            async for event in self._read_ndjson_stream():
                message = self.transform_event(event)
                if message is not None:
                    yield message
        finally:
            if self.process:
                try:
                    self.process.terminate()
                except Exception:
                    pass
                self.process = None
    
    async def _read_ndjson_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Read and parse NDJSON from Codex CLI output.
        
        Handles partial lines and JSON decode errors.
        """
        import asyncio
        
        if self.process is None:
            return
        
        buffer = ""
        
        async def read_stdout():
            loop = asyncio.get_event_loop()
            while True:
                chunk = await loop.run_in_executor(None, self.process.stdout.readline)
                if not chunk:
                    break
                yield chunk
        
        async for chunk in read_stdout():
            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    yield event
                except json.JSONDecodeError:
                    # Skip malformed JSON lines
                    continue
