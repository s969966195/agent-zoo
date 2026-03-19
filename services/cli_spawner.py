"""
CLI Spawner Service for Zoo Multi-Agent System.

Handles spawning and managing CLI processes for different animal agents.
Supports line-buffered output and NDJSON parsing.
"""

import asyncio
import json
import shlex
from asyncio.subprocess import Process
from asyncio.streams import StreamReader
from typing import Dict, Any, Optional, AsyncGenerator, Tuple, Callable


class CLISpawner:
    """Spawns and manages CLI processes for animal agents."""
    
    def __init__(self, timeout: float = 300.0):
        self.timeout = timeout
        self.processes: Dict[str, asyncio.Task] = {}
    
    async def spawn_cli_process(
        self,
        command: str,
        args: list[str],
        animal_id: str,
        on_line: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> asyncio.Task:
        """
        Spawn a CLI process and stream output.
        
        Args:
            command: The CLI command to run
            args: List of arguments
            animal_id: Unique identifier for the animal
            on_line: Callback for each output line
            on_error: Callback for error lines
            
        Returns:
            Task that completes when process exits
        """
        full_cmd = [command] + args
        
        process = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        task = asyncio.create_task(
            self._stream_process_output(
                process, animal_id, on_line, on_error
            )
        )
        
        self.processes[animal_id] = task
        return task
    
    async def _stream_process_output(
        self,
        process: Process,
        animal_id: str,
        on_line: Optional[Callable],
        on_error: Optional[Callable],
    ) -> None:
        """Stream output from process with line buffering."""
        try:
            async with asyncio.timeout(self.timeout):
                await self._read_lines(
                    process.stdout, animal_id, on_line, is_stderr=False
                )
                await self._read_lines(
                    process.stderr, animal_id, on_error, is_stderr=True
                )
        except asyncio.TimeoutError:
            await self.terminate(animal_id)
            raise TimeoutError(f"Process for {animal_id} timed out")
        except asyncio.CancelledError:
            await self.terminate(animal_id)
            raise
        finally:
            if animal_id in self.processes:
                del self.processes[animal_id]
    
    async def _read_lines(
        self,
        reader: Optional[StreamReader],
        animal_id: str,
        callback: Optional[Callable],
        is_stderr: bool = False,
    ) -> None:
        """Read lines from StreamReader with NDJSON support."""
        if reader is None:
            return
        async for raw_line in reader:
            line = raw_line.decode("utf-8").rstrip()
            if not line:
                continue
            
            if callback:
                if is_stderr:
                    callback(line, is_error=True)
                else:
                    # Try NDJSON parsing for stdout
                    parsed = self._try_parse_ndjson(line)
                    callback(line, parsed=parsed)
    
    def _try_parse_ndjson(self, line: str) -> Optional[Dict[str, Any]]:
        """Try to parse a line as NDJSON."""
        try:
            if line.startswith("{") and line.endswith("}"):
                return json.loads(line)
        except json.JSONDecodeError:
            pass
        return None
    
    async def terminate(self, animal_id: str) -> None:
        """Gracefully terminate a process."""
        if animal_id in self.processes:
            task = self.processes[animal_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    async def terminate_all(self) -> None:
        """Terminate all managed processes."""
        for animal_id in list(self.processes.keys()):
            await self.terminate(animal_id)


def create_cli_spawner(timeout: float = 300.0) -> CLISpawner:
    """Factory function to create a CLI spawner instance."""
    return CLISpawner(timeout=timeout)


def get_cli_spawner(timeout: float = 300.0) -> CLISpawner:
    """Alias for create_cli_spawner for backward compatibility."""
    return create_cli_spawner(timeout=timeout)
