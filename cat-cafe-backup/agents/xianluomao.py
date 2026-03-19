"""Cat Café multi-agent system - Xianluomao (Gemini) agent implementation.

Supports dual adapter: CLI + HTTP callback (for future Phase 3).
"""

import json
import subprocess
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, Optional

from agents.base import AgentMessage, AgentService

if TYPE_CHECKING:
    ProcessHandle = subprocess.Popen[Any]


class Xianluomao(AgentService):
    """Gemini agent via CLI.
    
    CLI command: gemini chat "{prompt}"
    
    Supports dual adapter模式 - CLI for basic operations, HTTP for callback operations.
    """
    
    def __init__(self, agent_id: str = "xianluomao", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config or {})
        self.process: Optional[subprocess.Popen] = None
        self._use_http = self.config.get("use_http", False)
        self._http_url = self.config.get("http_url", "http://localhost:8080")
    
    def get_cli_command(self) -> tuple[str, list[str]]:
        """Return (command, args) for spawning Gemini CLI."""
        return ("gemini", ["chat"])
    
    def transform_event(self, event: Dict[str, Any]) -> Optional[AgentMessage]:
        """Transform Gemini NDJSON event to unified AgentMessage.
        
        Gemini chat output format:
        - Plain text responses (not NDJSON by default)
        - With --json flag: { "message": "...", "role": "model" }
        
        This implementation handles both plain text and JSON modes.
        """
        if not isinstance(event, dict):
            # Plain text response (Gemini default without --json)
            return AgentMessage(
                role="assistant",
                content=str(event),
                thread_id="",
            )
        
        event_type = event.get("type", event.get("role", ""))
        
        if event_type in ("assistant", "model", "response"):
            return AgentMessage(
                role=event_type,
                content=event.get("message", event.get("content", "")),
                thread_id=event.get("thread_id", ""),
                session_id=event.get("session_id"),
                metadata=event.get("metadata"),
            )
        elif event_type in ("user", "input"):
            # User message - could be returned for tracking
            return AgentMessage(
                role="user",
                content=event.get("message", event.get("content", "")),
                thread_id=event.get("thread_id", ""),
            )
        elif event_type == "system":
            # System event - return as metadata
            return AgentMessage(
                role="system",
                content=event.get("message", ""),
                thread_id="",
                metadata=event,
            )
        else:
            # Generic event
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
        """Invoke Gemini CLI and stream responses.
        
        Args:
            prompt: User prompt to send to Gemini
            thread_id: Thread identifier for conversation context
            session_id: Optional session identifier
            callback_env: Environment variables for callbacks
            
        Yields:
            AgentMessage objects streaming from Gemini
        """
        if self._use_http:
            # HTTP callback mode (Phase 3 placeholder)
            async for message in self._invoke_http(prompt, thread_id, session_id, callback_env):
                yield message
            return
        
        command, args = self.get_cli_command()
        
        # Build command with prompt as argument
        full_args = [f'"{prompt}"'] + list(args)
        
        # Set up environment
        env = callback_env or {}
        if self.config.get("api_key"):
            env["GEMINI_API_KEY"] = self.config["api_key"]
        
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
            # Read and parse output (handles both plain text and NDJSON)
            async for event in self._read_stream():
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
    
    async def _read_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Read and parse output from Gemini CLI.
        
        Handles both plain text and NDJSON modes.
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
                
                # Try to parse as JSON first
                try:
                    event = json.loads(line)
                    yield event
                except json.JSONDecodeError:
                    # Plain text response
                    yield line
    
    async def _invoke_http(
        self,
        prompt: str,
        thread_id: str,
        session_id: Optional[str],
        callback_env: Optional[Dict[str, str]]
    ) -> AsyncGenerator[AgentMessage, None]:
        """HTTP callback mode for Phase 3.
        
        This is a placeholder for future HTTP implementation.
        Currently falls back to CLI mode.
        """
        # Fallback to CLI for now
        import warnings
        warnings.warn("HTTP callback mode not yet implemented, using CLI mode")
        
        # Re-implement CLI invoke here for now
        command, args = self.get_cli_command()
        full_args = [f'"{prompt}"'] + list(args)
        
        import asyncio
        
        self.process = await asyncio.to_thread(
            subprocess.Popen,
            [command] + full_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=callback_env,
        )
        
        try:
            async for event in self._read_stream():
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
