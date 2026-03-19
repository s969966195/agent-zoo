"""
MCP Callback Router for Zoo Multi-Agent System.

Handles HTTP callbacks from animals for:
- post_message: Send messages via MCP callback
- get_thread_context: Retrieve conversation context
- get_pending_mentions: Check for @mentions addressed to current animal
"""

import re
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from utils.a2a_mentions import ANIMAL_CONFIGS, PATTERN_TO_ANIMAL, parse_a2a_mentions


@dataclass
class MessageEntry:
    """A message in the thread context."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    animal_sender: Optional[str] = None


@dataclass
class CallbackResponse:
    """Response from MCP callback."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class MCPHTTPCallbackRouter:
    """
    Router for MCP HTTP callbacks from animals.
    
    Handles callback authentication, message storage, and context retrieval.
    """
    
    def __init__(
        self,
        callback_url: str = "http://localhost:8000/mcp/callback",
        token_validator: Optional[Callable[[str], bool]] = None,
        max_thread_context: int = 100,
    ):
        """
        Initialize the MCP callback router.
        
        Args:
            callback_url: Base URL for MCP callbacks
            token_validator: Optional callable to validate tokens
            max_thread_context: Maximum messages to keep in thread context
        """
        self.callback_url = callback_url
        self.token_validator = token_validator or (lambda t: True)
        self.max_thread_context = max_thread_context
        
        self._lock = threading.RLock()
        self._thread_context: Dict[str, List[MessageEntry]] = {}
        self._pending_mentions: Dict[str, List[Dict[str, Any]]] = {}
        self._invocation_callbacks: Dict[str, Callable] = {}
    
    def post_message(
        self,
        invocation_id: str,
        token: str,
        content: str,
        role: str = "assistant",
        animal_sender: Optional[str] = None,
    ) -> CallbackResponse:
        """
        Handle post_message callback from an animal.
        
        Args:
            invocation_id: ID of the current invocation
            token: Authentication token
            content: Message content to post
            role: Message role (user, assistant, system)
            animal_sender: Animal key that sent the message
            
        Returns:
            CallbackResponse with success status
        """
        # Validate token
        if not self.token_validator(token):
            return CallbackResponse(
                success=False,
                message="Invalid or expired token",
            )
        
        with self._lock:
            # Get or create thread context
            thread_id = _extract_thread_id(invocation_id)
            if thread_id not in self._thread_context:
                self._thread_context[thread_id] = []
            
            # Create message entry
            message = MessageEntry(
                role=role,
                content=content,
                timestamp=datetime.now(),
                animal_sender=animal_sender,
            )
            
            # Store message
            self._thread_context[thread_id].append(message)
            
            # Enforce max context size
            if len(self._thread_context[thread_id]) > self.max_thread_context:
                self._thread_context[thread_id] = (
                    self._thread_context[thread_id][-self.max_thread_context:]
                )
            
            # Check for @mentions in the message
            if role in ("user", "assistant"):
                self._process_mentions(thread_id, message)
            
            return CallbackResponse(
                success=True,
                message="Message posted successfully",
                data={
                    "message_id": f"{thread_id}_{len(self._thread_context[thread_id]) - 1}",
                    "timestamp": message.timestamp.isoformat(),
                },
            )
    
    def get_thread_context(
        self,
        invocation_id: str,
        token: str,
        limit: int = 10,
    ) -> CallbackResponse:
        """
        Get thread context via MCP callback.
        
        Args:
            invocation_id: ID of the current invocation
            token: Authentication token
            limit: Maximum number of messages to return
            
        Returns:
            CallbackResponse with thread context
        """
        # Validate token
        if not self.token_validator(token):
            return CallbackResponse(
                success=False,
                message="Invalid or expired token",
            )
        
        with self._lock:
            thread_id = _extract_thread_id(invocation_id)
            messages = self._thread_context.get(thread_id, [])
            
            # Apply limit (most recent first)
            if limit > 0 and len(messages) > limit:
                messages = messages[-limit:]
            
            # Format for return
            context = [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "animal_sender": m.animal_sender,
                }
                for m in messages
            ]
            
            return CallbackResponse(
                success=True,
                message="Thread context retrieved",
                data={
                    "thread_id": thread_id,
                    "message_count": len(messages),
                    "messages": context,
                },
            )
    
    def get_pending_mentions(
        self,
        invocation_id: str,
        token: str,
    ) -> CallbackResponse:
        """
        Get pending @mentions for the current animal.
        
        Args:
            invocation_id: ID of the current invocation
            token: Authentication token
            
        Returns:
            CallbackResponse with pending mentions
        """
        # Validate token
        if not self.token_validator(token):
            return CallbackResponse(
                success=False,
                message="Invalid or expired token",
            )
        
        with self._lock:
            thread_id = _extract_thread_id(invocation_id)
            
            # Find mentions for this thread
            mentions = self._pending_mentions.get(thread_id, [])
            
            return CallbackResponse(
                success=True,
                message="Pending mentions retrieved",
                data={
                    "thread_id": thread_id,
                    "mention_count": len(mentions),
                    "mentions": mentions,
                },
            )
    
    def register_callback(
        self,
        invocation_id: str,
        callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        """
        Register a callback for invocation completion.
        
        Args:
            invocation_id: ID to register callback for
            callback: Callback function
        """
        self._invocation_callbacks[invocation_id] = callback
    
    def unregister_callback(self, invocation_id: str) -> None:
        """Unregister callback for invocation."""
        self._invocation_callbacks.pop(invocation_id, None)
    
    def _process_mentions(self, thread_id: str, message: MessageEntry) -> None:
        """Process @mentions in a message."""
        # Parse mentions (excluding code blocks already stripped)
        text = message.content
        
        # Find all @mentions
        mention_keys = []
        for pattern in PATTERN_TO_ANIMAL.keys():
            if pattern in text:
                mention_keys.append(PATTERN_TO_ANIMAL[pattern])
        
        # Add to pending mentions for each mentioned animal
        for animal_key in mention_keys:
            mention_record = {
                "invocation_id": _generate_invocation_id(thread_id),
                "thread_id": thread_id,
                "mentioned_animal": animal_key,
                "source_content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "status": "pending",
            }
            
            if thread_id not in self._pending_mentions:
                self._pending_mentions[thread_id] = []
            self._pending_mentions[thread_id].append(mention_record)
    
    def clear_pending_mentions(self, thread_id: str, animal_key: str) -> None:
        """Clear processed mentions for an animal in a thread."""
        with self._lock:
            if thread_id in self._pending_mentions:
                self._pending_mentions[thread_id] = [
                    m for m in self._pending_mentions[thread_id]
                    if not (m["mentioned_animal"] == animal_key and m["status"] == "pending")
                ]


def _extract_thread_id(invocation_id: str) -> str:
    """Extract thread ID from invocation ID."""
    # In real implementation, this would extract from actual invocation data
    # For now, use a simple hash-based derivation
    import hashlib
    hash_val = hashlib.md5(invocation_id.encode()).hexdigest()[:8]
    return f"thread_{hash_val}"


def _generate_invocation_id(thread_id: str) -> str:
    """Generate invocation ID from thread ID."""
    import hashlib
    hash_val = hashlib.md5(thread_id.encode()).hexdigest()[:8]
    return f"inv_{hash_val}"


# Global singleton
_callback_router = MCPHTTPCallbackRouter()


def get_callback_router() -> MCPHTTPCallbackRouter:
    """Get global callback router instance."""
    return _callback_router


# Convenience functions for animals to use
def post_message(invocation_id: str, token: str, content: str) -> CallbackResponse:
    """Convenience function to post a message."""
    return get_callback_router().post_message(invocation_id, token, content)


def get_thread_context(invocation_id: str, token: str, limit: int = 10) -> CallbackResponse:
    """Convenience function to get thread context."""
    return get_callback_router().get_thread_context(invocation_id, token, limit)


def get_pending_mentions(invocation_id: str, token: str) -> CallbackResponse:
    """Convenience function to get pending mentions."""
    return get_callback_router().get_pending_mentions(invocation_id, token)
