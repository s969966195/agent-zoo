"""
Cat Café Multi-Agent System - MCP Callback Router

HTTP callback handler for agents to post messages and interact with the chat.
"""

import re
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from core.models import AgentMessage
from core.types import CallbackToken
from core.invocation_registry import get_invocation_registry, InvocationRegistry
from core.websocket_manager import WebSocketManager, get_ws_manager


class McpCallbackRouter:
    """
    Handle HTTP callbacks from agents to post messages and interact with the chat.
    
    Provides HTTP endpoints for agents to:
    - Post messages to the chat
    - Request thread context
    - Check for pending @mentions
    """
    
    def __init__(
        self,
        invocation_registry: InvocationRegistry,
        websocket_manager: WebSocketManager
    ):
        self.invocation_registry = invocation_registry
        self.websocket_manager = websocket_manager
        self.thread_worklist_registry: Dict[str, List[str]] = {}  # For A2A routing
    
    async def post_message(
        self,
        invocation_id: str,
        callback_token: str,
        content: str,
        agent_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        message_type: str = "text",
    ) -> Dict[str, Any]:
        """
        Agent posts a message to the chat.
        
        Args:
            invocation_id: ID of the active invocation
            callback_token: Token for authentication
            content: Message content
            agent_id: Agent ID (if not provided, extracted from invocation)
            thread_id: Thread ID (if not provided, extracted from invocation)
            message_type: Type of message (text, tool_call, tool_result, done)
        
        Returns:
            Dict with success status and message details
        """
        # Validate token
        is_valid = self.invocation_registry.validate_token(invocation_id, callback_token)
        if not is_valid:
            return {
                "success": False,
                "error": "Invalid or expired callback token",
                "code": "invalid_token",
            }
        
        # Get invocation details
        invocation = self.invocation_registry.get_invocation(invocation_id)
        if not invocation:
            return {
                "success": False,
                "error": "Invocation not found",
                "code": "not_found",
            }
        
        # Extract agent_id and thread_id from invocation if not provided
        effective_agent_id = agent_id or invocation.target_agent
        effective_thread_id = thread_id or invocation.thread_id
        
        # Create AgentMessage
        mentions = self.parse_mentions(content, effective_agent_id)
        message = AgentMessage(
            id=str(uuid.uuid4()),
            type=message_type,
            agent_id=effective_agent_id,
            content=content,
            thread_id=effective_thread_id,
            timestamp=datetime.utcnow(),
            mentions=mentions,
        )
        
        # Broadcast via WebSocket - the existing ws_manager uses Pydantic models
        # We use a string-based broadcast wrapper
        try:
            # Broadcast to all connected agents - simple string broadcast
            await self.websocket_manager.broadcast(content)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to broadcast message: {str(e)}",
                "code": "broadcast_error",
            }
        
        # Check for @mentions and enqueue A2A targets
        if mentions:
            self.enqueue_a2a_targets(effective_thread_id, content, effective_agent_id)
        
        # Complete the invocation
        self.invocation_registry.complete_invocation(invocation_id)
        
        return {
            "success": True,
            "message_id": message.id,
            "thread_id": effective_thread_id,
            "mentions": mentions,
            "content_preview": content[:100] if len(content) > 100 else content,
        }
    
    async def get_thread_context(
        self,
        invocation_id: str,
        callback_token: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Agent requests recent thread messages.
        
        Args:
            invocation_id: ID of the active invocation
            callback_token: Token for authentication
            limit: Maximum number of messages to return
        
        Returns:
            Dict with thread messages and metadata
        """
        # Validate token
        is_valid = self.invocation_registry.validate_token(invocation_id, callback_token)
        if not is_valid:
            return {
                "success": False,
                "error": "Invalid or expired callback token",
                "code": "invalid_token",
            }
        
        # Get invocation details
        invocation = self.invocation_registry.get_invocation(invocation_id)
        if not invocation:
            return {
                "success": False,
                "error": "Invocation not found",
                "code": "not_found",
            }
        
        # TODO: In Phase 4, fetch messages from storage
        # For now, return empty context
        return {
            "success": True,
            "thread_id": invocation.thread_id,
            "limit": limit,
            "messages": [],
            "message_count": 0,
        }
    
    async def get_pending_mentions(
        self,
        invocation_id: str,
        callback_token: str,
    ) -> Dict[str, Any]:
        """
        Agent checks for @mentions targeting it.
        
        Args:
            invocation_id: ID of the active invocation
            callback_token: Token for authentication
        
        Returns:
            Dict with pending mentions and their messages
        """
        # Validate token
        is_valid = self.invocation_registry.validate_token(invocation_id, callback_token)
        if not is_valid:
            return {
                "success": False,
                "error": "Invalid or expired callback token",
                "code": "invalid_token",
            }
        
        # Get invocation details
        invocation = self.invocation_registry.get_invocation(invocation_id)
        if not invocation:
            return {
                "success": False,
                "error": "Invocation not found",
                "code": "not_found",
            }
        
        # TODO: In Phase 4, fetch pending mentions from storage
        # For now, check thread worklist registry
        mentions = []
        thread_id = invocation.thread_id
        worklist = self.thread_worklist_registry.get(thread_id, [])
        
        if worklist and invocation.target_agent in worklist:
            # Agent has pending work
            mentions = [{
                "source_agent": "system",
                "content": "You have pending work in this thread",
                "timestamp": datetime.utcnow().isoformat(),
            }]
        
        return {
            "success": True,
            "agent_id": invocation.target_agent,
            "pending_count": len(mentions),
            "mentions": mentions,
        }
    
    def parse_mentions(self, content: str, source_agent: str) -> List[str]:
        """
        Parse @mentions from message content.
        
        Supports patterns like:
        - @布偶猫
        - @缅因猫
        - @暹罗猫
        
        Args:
            content: Message content to parse
            source_agent: ID of the agent sending the message
        
        Returns:
            List of agent IDs mentioned in the content
        """
        # Pattern for Chinese agent mentions: @拼音 or @Chinese name
        # Matches patterns like @布偶猫, @缅因猫, @暹罗猫
        mention_pattern = r"@([^\s@]+)"
        
        mentions = []
        for match in re.finditer(mention_pattern, content):
            mentioned_name = match.group(1).strip()
            
            # Map mention names to agent IDs
            agent_id = self._name_to_agent_id(mentioned_name)
            if agent_id and agent_id != source_agent:
                mentions.append(agent_id)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_mentions = []
        for mention in mentions:
            if mention not in seen:
                seen.add(mention)
                unique_mentions.append(mention)
        
        return unique_mentions
    
    def _name_to_agent_id(self, name: str) -> Optional[str]:
        """
        Convert mention name to agent ID.
        
        Args:
            name: Mentioned name (e.g., "布偶猫" or "bollumao")
        
        Returns:
            Agent ID or None if not found
        """
        # Direct agent ID mapping
        agent_map = {
            "bollumao": "bollumao",
            "布偶猫": "bollumao",
            "bmu": "bollumao",
            
            "mainemao": "mainemao",
            "缅因猫": "mainemao",
            "maine": "mainemao",
            
            "xianluomao": "xianluomao",
            "暹罗猫": "xianluomao",
            "siamese": "xianluomao",
            "xian": "xianluomao",
        }
        
        return agent_map.get(name.lower())
    
    def enqueue_a2a_targets(
        self,
        thread_id: str,
        content: str,
        source_agent: str,
    ) -> List[str]:
        """
        Queue A2A targets for worklist routing.
        
        When an agent is mentioned, it gets added to the worklist
        for that thread to be notified of pending work.
        
        Args:
            thread_id: Thread ID
            content: Message content (for parsing mentions)
            source_agent: Agent that sent the message
        
        Returns:
            List of enqueued agent IDs
        """
        mentions = self.parse_mentions(content, source_agent)
        
        # Add to thread worklist
        if thread_id not in self.thread_worklist_registry:
            self.thread_worklist_registry[thread_id] = []
        
        for mentioned_agent in mentions:
            if mentioned_agent not in self.thread_worklist_registry[thread_id]:
                self.thread_worklist_registry[thread_id].append(mentioned_agent)
        
        return mentions
    
    def clear_worklist(self, thread_id: str) -> int:
        """
        Clear or reduce worklist for a thread.
        
        Args:
            thread_id: Thread ID
        
        Returns:
            Number of entries cleared
        """
        if thread_id in self.thread_worklist_registry:
            count = len(self.thread_worklist_registry[thread_id])
            del self.thread_worklist_registry[thread_id]
            return count
        return 0
    
    def get_worklist(self, thread_id: str) -> List[str]:
        """
        Get current worklist for a thread.
        
        Args:
            thread_id: Thread ID
        
        Returns:
            List of agent IDs with pending work
        """
        return self.thread_worklist_registry.get(thread_id, [])
    
    def create_callback_token(
        self,
        agent_id: str,
        thread_id: str,
        ttl_seconds: int = 300,
        max_uses: int = 1,
    ) -> Dict[str, Any]:
        """
        Create a callback token for agent use.
        
        Args:
            agent_id: Agent ID
            thread_id: Thread ID
            ttl_seconds: Token validity in seconds
            max_uses: Maximum uses before expiration
        
        Returns:
            Dict with token and metadata
        """
        token = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=ttl_seconds)
        
        callback_token = CallbackToken(
            token=token,
            agent_id=agent_id,
            thread_id=thread_id,
            created_at=now,
            expires_at=expires_at,
            max_uses=max_uses,
        )
        
        # Store in registry (simplified)
        # In production, this would be in a proper token store
        return {
            "token": token,
            "agent_id": agent_id,
            "thread_id": thread_id,
            "expires_at": expires_at.isoformat(),
            "max_uses": max_uses,
        }


# Global singleton
_mcp_callback_router: Optional['McpCallbackRouter'] = None


def get_mcp_callback_router() -> McpCallbackRouter:
    """Get or create the global MCP callback router instance."""
    global _mcp_callback_router
    
    if _mcp_callback_router is None:
        ws_mgr = get_ws_manager()
        _mcp_callback_router = McpCallbackRouter(
            invocation_registry=get_invocation_registry(),
            websocket_manager=ws_mgr,
        )
    
    return _mcp_callback_router


__all__ = [
    "McpCallbackRouter",
    "get_mcp_callback_router",
]
