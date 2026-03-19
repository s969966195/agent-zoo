"""Cat Café multi-agent system - CLI process management with NDJSON parsing."""

import asyncio
import json
import signal
import subprocess
import sys
from typing import Any, AsyncGenerator, Dict, Optional

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias


ProcessHandle: TypeAlias = "subprocess.Popen[bytes]"


class CliSpawner:
    """Spawn and manage CLI subprocesses for AI agents.
    
    Provides async subprocess management with NDJSON output parsing
    and graceful termination handling.
    """
    
    def __init__(self, default_timeout: float = 30.0):
        """Initialize CliSpawner.
        
        Args:
            default_timeout: Default timeout for operations (default: 30.0 seconds)
        """
        self.default_timeout = default_timeout
        self._processes: Dict[str, ProcessHandle] = {}
    
    async def spawn_agent(
        self,
        command: str,
        args: list[str],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        process_id: Optional[str] = None,
    ) -> ProcessHandle:
        """Spawn a CLI process and return handle.
        
        Args:
            command: Path to the executable command
            args: List of command-line arguments
            env: Optional environment variables dict
            cwd: Optional working directory
            process_id: Optional ID to track this process
            
        Returns:
            Subprocess.Popen handle for the spawned process
        """
        full_env = {**env} if env else {}
        if "PYTHONUNBUFFERED" not in full_env:
            full_env["PYTHONUNBUFFERED"] = "1"
        
        process = await asyncio.to_thread(
            subprocess.Popen,
            [command] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=full_env,
            cwd=cwd,
            bufsize=1,  # Line buffered
        )
        
        if process_id:
            self._processes[process_id] = process
        
        return process
    
    async def read_ndjson_stream(
        self,
        process: ProcessHandle,
        timeout: Optional[float] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Parse NDJSON output stream from CLI.
        
        Handles partial lines, JSON decode errors, and timeouts.
        
        Args:
            process: The subprocess handle to read from
            timeout: Optional timeout per line (default: instance default)
            
        Yields:
            Parsed JSON objects from NDJSON stream
            
        Raises:
            TimeoutError: If no data received within timeout
            json.JSONDecodeError: If line cannot be parsed as JSON
        """
        if timeout is None:
            timeout = self.default_timeout
        
        buffer = ""
        
        async def read_chunk() -> Optional[str]:
            """Read a chunk from stdout with timeout."""
            loop = asyncio.get_event_loop()
            try:
                chunk = await asyncio.wait_for(
                    loop.run_in_executor(None, process.stdout.readline),
                    timeout=timeout,
                )
                return chunk
            except asyncio.TimeoutError:
                raise TimeoutError("Timeout reading from process stdout")
        
        try:
            while True:
                chunk = await read_chunk()
                if not chunk:
                    break
                
                buffer += chunk
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    try:
                        event = json.loads(line)
                        yield event
                    except json.JSONDecodeError as e:
                        # Log and skip malformed JSON
                        print(f"Warning: Failed to parse NDJSON: {e}")
                        print(f"  Line: {line}")
                        continue
                        
        except (TimeoutError, GeneratorExit):
            pass
        finally:
            # Clean up any remaining buffer
            if buffer.strip():
                try:
                    event = json.loads(buffer.strip())
                    yield event
                except json.JSONDecodeError:
                    pass
    
    async def send_input(
        self,
        process: ProcessHandle,
        input_data: str,
        timeout: Optional[float] = None,
    ) -> None:
        """Send input to process stdin.
        
        Args:
            process: The subprocess handle to write to
            input_data: String data to send
            timeout: Optional timeout for write operation
            
        Raises:
            TimeoutError: If write operation times out
            BrokenPipeError: If process stdin is closed
        """
        if process.stdin is None:
            raise BrokenPipeError("Process stdin not available")
        
        if timeout is None:
            timeout = self.default_timeout
        
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, process.stdin.write, input_data),
                timeout=timeout,
            )
            await asyncio.wait_for(
                loop.run_in_executor(None, process.stdin.flush),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise TimeoutError("Timeout writing to process stdin")
    
    async def terminate(
        self,
        process: ProcessHandle,
        timeout: float = 5.0,
    ) -> None:
        """Gracefully terminate process with fallback to kill.
        
        Sends SIGTERM, waits for graceful exit, then SIGKILL if needed.
        
        Args:
            process: The subprocess handle to terminate
            timeout: Seconds to wait for graceful termination (default: 5.0)
            
        Raises:
            TimeoutError: If process doesn't terminate within timeout
        """
        if process.poll() is not None:
            # Process already terminated
            return
        
        # Send SIGTERM for graceful shutdown
        try:
            process.terminate()
        except ProcessLookupError:
            # Process already gone
            return
        
        # Wait for graceful termination
        try:
            await asyncio.wait_for(
                asyncio.to_thread(process.wait),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            # Force kill
            try:
                process.kill()
            except ProcessLookupError:
                pass
    
    async def cleanup_all(self, timeout: float = 5.0) -> None:
        """Terminate all tracked processes.
        
        Args:
            timeout: Seconds to wait for each process termination
        """
        for process_id, process in list(self._processes.items()):
            if process.poll() is None:
                try:
                    await self.terminate(process, timeout)
                except Exception:
                    pass
            del self._processes[process_id]
    
    def get_process(self, process_id: str) -> Optional[ProcessHandle]:
        """Get tracked process by ID.
        
        Args:
            process_id: ID of the process to retrieve
            
        Returns:
            Process handle if tracked, None otherwise
        """
        return self._processes.get(process_id)
    
    def remove_process(self, process_id: str) -> Optional[ProcessHandle]:
        """Remove process from tracking without terminating.
        
        Args:
            process_id: ID of the process to remove
            
        Returns:
            Process handle if removed, None otherwise
        """
        return self._processes.pop(process_id, None)
