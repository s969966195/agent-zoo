"""
Cat Café Multi-Agent System - WebSocket Manager

Manages WebSocket connections for agent communication.
"""

import asyncio
import json
import uuid
import datetime
from typing import Optional, Set, Dict, Any, Callable
from collections import defaultdict
import threading

from core.models import AgentMessage
from core.config import settings


class WebSocketConnection:
    """Represents a WebSocket connection for an agent."""
    
    def __init__(self, websocket, agent_id: str):
        self.websocket = websocket
        self.agent_id = agent_id
        self.connected_at = datetime.datetime.utcnow()
        self.id = str(uuid.uuid4())
        self._send_lock = asyncio.Lock()
    
    async def send(self, message: AgentMessage) -> bool:
        """Send a message through the WebSocket."""
        try:
            data = message.model_dump_json()
            async with self._send_lock:
                await self.websocket.send_text(data)
            return True
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close the WebSocket connection."""
        await self.websocket.close()


class WebSocketManager:
    """
    Manages WebSocket connections for agent-to-agent communication.
    
    Supports:
    - Multiple agent connections
    - Broadcasting messages to specific agents or all agents
    - Connection tracking and cleanup
    - Callback hooks for connection events
    """
    
    def __init__(self):
        self._connections: Dict[str, WebSocketConnection] = {}  # agent_id -> connection
        self._connections_by_id: Dict[str, WebSocketConnection] = {}  # conn_id -> connection
        self._lock = threading.RLock()
        
        # Callbacks
        self._on_connect_callback = None
        self._on_disconnect_callback = None
        self._on_message_callback = None
    
    # Connection management
    async def connect(self, websocket, agent_id: str) -> Optional[WebSocketConnection]:
        """Establish a WebSocket connection for an agent."""
        with self._lock:
            # Disconnect existing connection if any
            if agent_id in self._connections:
                await self._connections[agent_id].close()
            
            connection = WebSocketConnection(websocket, agent_id)
            self._connections[agent_id] = connection
            self._connections_by_id[connection.id] = connection
            
            if self._on_connect_callback:
                await self._on_connect_callback(connection)
            
            return connection
    
    async def disconnect(self, agent_id: str) -> bool:
        """Disconnect an agent's WebSocket connection."""
        with self._lock:
            connection = self._connections.pop(agent_id, None)
            if connection:
                del self._connections_by_id[connection.id]
                await connection.close()
                
                if self._on_disconnect_callback:
                    await self._on_disconnect_callback(connection)
                
                return True
            return False
    
    def get_connection(self, agent_id: str) -> Optional[WebSocketConnection]:
        """Get connection for an agent."""
        with self._lock:
            return self._connections.get(agent_id)
    
    def get_all_connections(self) -> Dict[str, WebSocketConnection]:
        """Get all active connections."""
        with self._lock:
            return dict(self._connections)
    
    def get_active_agent_ids(self) -> Set[str]:
        """Get set of active agent IDs."""
        with self._lock:
            return set(self._connections.keys())
    
    # Message handling
    async def send_to_agent(self, agent_id: str, message: AgentMessage) -> bool:
        """Send message to a specific agent."""
        with self._lock:
            connection = self._connections.get(agent_id)
        
        if connection:
            return await connection.send(message)
        return False
    
    async def broadcast(self, message: AgentMessage, exclude: Optional[Set[str]] = None) -> Dict[str, bool]:
        """Broadcast message to all connected agents."""
        exclude = exclude or set()
        results = {}
        
        with self._lock:
            connections = dict(self._connections)
        
        for agent_id, connection in connections.items():
            if agent_id not in exclude:
                results[agent_id] = await connection.send(message)
        
        return results
    
    async def send_to_thread(self, thread_id: str, message: AgentMessage) -> Dict[str, bool]:
        """Send message to all agents participating in a thread."""
        # TODO: Implement thread-based routing when Thread model includes participants
        return await self.broadcast(message)
    
    # Callbacks
    def on_connect(self, callback):
        """Register callback for new connections."""
        self._on_connect_callback = callback
        return callback
    
    def on_disconnect(self, callback):
        """Register callback for disconnections."""
        self._on_disconnect_callback = callback
        return callback
    
    def on_message(self, callback):
        """Register callback for incoming messages."""
        self._on_message_callback = callback
        return callback
    
    # Utility
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        with self._lock:
            return {
                "total_connections": len(self._connections),
                "agent_ids": list(self._connections.keys()),
            }
    
    async def close_all(self) -> None:
        """Close all WebSocket connections."""
        with self._lock:
            connections = list(self._connections.values())
        
        for connection in connections:
            try:
                await connection.close()
            except Exception:
                pass
        
        with self._lock:
            self._connections.clear()
            self._connections_by_id.clear()


class MessageRouter:
    """
    Routes messages between agents using WebSocket connections.
    
    Handles message type dispatching and callback processing.
    """
    
    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager
        self._message_handlers: Dict[str, Callable] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self) -> None:
        """Set up default message handlers."""
        self.register_handler("text", self._handle_text_message)
        self.register_handler("tool_call", self._handle_tool_call)
        self.register_handler("tool_result", self._handle_tool_result)
        self.register_handler("session_init", self._handle_session_init)
        self.register_handler("done", self._handle_done_message)
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a custom message handler."""
        self._message_handlers[message_type] = handler
    
    async def route_message(self, message: AgentMessage) -> bool:
        """Route a message to the appropriate handler."""
        handler = self._message_handlers.get(message.type)
        if handler:
            return await handler(message)
        return False
    
    async def _handle_text_message(self, message: AgentMessage) -> bool:
        """Handle text messages."""
        # Broadcast to all agents in the thread
        return await self.ws_manager.send_to_thread(message.thread_id, message)
    
    async def _handle_tool_call(self, message: AgentMessage) -> bool:
        """Handle tool call messages."""
        # Route to target agent
        target_agent = message.metadata.get("target_agent")
        if target_agent:
            return await self.ws_manager.send_to_agent(target_agent, message)
        return False
    
    async def _handle_tool_result(self, message: AgentMessage) -> bool:
        """Handle tool result messages."""
        # Return result to caller
        caller_agent = message.metadata.get("caller_agent")
        if caller_agent:
            return await self.ws_manager.send_to_agent(caller_agent, message)
        return False
    
    async def _handle_session_init(self, message: AgentMessage) -> bool:
        """Handle session initialization messages."""
        # Broadcast to all connected agents
        return await self.ws_manager.broadcast(message)
    
    async def _handle_done_message(self, message: AgentMessage) -> bool:
        """Handle done messages."""
        # Broadcast completion
        return await self.ws_manager.broadcast(message)


# Global instances
ws_manager = WebSocketManager()
message_router = MessageRouter(ws_manager)


def get_ws_manager() -> WebSocketManager:
    """Get the WebSocket manager instance."""
    return ws_manager


def get_message_router() -> MessageRouter:
    """Get the message router instance."""
    return message_router


__all__ = [
    "WebSocketManager",
    "MessageRouter",
    "get_ws_manager",
    "get_message_router",
]
