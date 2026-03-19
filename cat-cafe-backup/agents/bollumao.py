"""Cat Café multi-agent system - Bollumao (Claude) agent implementation."""

import json
import subprocess
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, Optional

from agents.base import AgentMessage, AgentService

if TYPE_CHECKING:
    ProcessHandle = subprocess.Popen[Any]


class Bollumao(AgentService):
    """Claude agent via CLI.
    
    CLI command: claude -p "{prompt}" --output-format stream-json --allowedTools Read,Edit,Glob,Grep
    """
    
    def __init__(self, agent_id: str = "bollumao", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config or {})
        self.process: Optional[subprocess.Popen] = None
    
    def get_cli_command(self) -> tuple[str, list[str]]:
        """Return (command, args) for spawning Claude CLI."""
        return ("claude", ["--output-format", "stream-json", "--allowedTools", "Read,Edit,Glob,Grep"])
    
    def transform_event(self, event: Dict[str, Any]) -> Optional[AgentMessage]:
        """Transform Claude NDJSON event to unified AgentMessage.
        
        Claude stream-json format contains various event types:
        - { "type": "message", "role": "assistant", "content": [...] }
        - { "type": "message_start", ... }
        - { "type": "content_block_start", ... }
        - { "type": "content_block_delta", ... }
        - { "type": "message_delta", ... }
        """
        event_type = event.get("type", "")
        
        if event_type == "message":
            # Full message event
            content = self._extract_content(event)
            return AgentMessage(
                role=event.get("role", "assistant"),
                content=content,
                thread_id=event.get("thread_id", ""),
                session_id=event.get("session_id"),
            )
        elif event_type == "content_block_delta":
            # Delta event - content chunk
            content = ""
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                content = delta.get("text", "")
            # For deltas, we don't return a message - they're accumulated
            return None
        elif event_type == "message_start":
            # Message start - we could return metadata but skip for now
            return None
        elif event_type == "message_delta":
            # Message end - could return usage info
            return None
        else:
            # Unknown event type - return as-is
            return AgentMessage(
                role="system",
                content=json.dumps(event),
                thread_id="",
            )
    
    def _extract_content(self, event: Dict[str, Any]) -> str:
        """Extract text content from Claude event."""
        content_blocks = event.get("content", [])
        texts = []
        for block in content_blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
        return "\n".join(texts)
    
    async def invoke(
        self,
        prompt: str,
        thread_id: str,
        session_id: Optional[str] = None,
        callback_env: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[AgentMessage, None]:
        """Invoke Claude CLI and stream responses.
        
        Args:
            prompt: User prompt to send to Claude
            thread_id: Thread identifier for conversation context
            session_id: Optional session identifier
            callback_env: Environment variables for callbacks
            
        Yields:
            AgentMessage objects streaming from Claude
        """
        command, args = self.get_cli_command()
        full_prompt = f"{prompt}"
        
        # Build command with prompt
        full_args = ["-p", full_prompt] + args
        
        # Set up environment
        env = callback_env or {}
        if self.config.get("api_key"):
            env["ANTHROPIC_API_KEY"] = self.config["api_key"]
        
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
        """Read and parse NDJSON from Claude CLI output.
        
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
