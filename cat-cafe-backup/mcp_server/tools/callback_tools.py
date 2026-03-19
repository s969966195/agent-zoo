"""
Cat Café Multi-Agent System - MCP Callback Tools

Native MCP tool implementations for agents with Claude-style MCP support.

These tools can be registered as native MCP tools that agents can call directly.
"""

import os
import json
from typing import Optional, Dict, Any

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class CallbackConfig:
    """Configuration for callback endpoint access."""
    
    def __init__(
        self,
        api_url: str = "",
        invocation_id: str = "",
        callback_token: str = "",
    ):
        self.api_url = api_url.rstrip("/")
        self.invocation_id = invocation_id
        self.callback_token = callback_token
    
    @property
    def is_configured(self) -> bool:
        """Check if configuration is complete."""
        return bool(self.api_url and self.invocation_id and self.callback_token)
    
    @property
    def base_url(self) -> str:
        """Get the base API URL."""
        return self.api_url
    
    @property
    def post_message_url(self) -> str:
        """Get the post_message endpoint URL."""
        return f"{self.api_url}/api/callbacks/post-message"
    
    @property
    def thread_context_url(self) -> str:
        """Get the thread_context endpoint URL."""
        return f"{self.api_url}/api/callbacks/thread-context"
    
    @property
    def pending_mentions_url(self) -> str:
        """Get the pending_mentions endpoint URL."""
        return f"{self.api_url}/api/callbacks/pending-mentions"
    
    @property
    def update_task_url(self) -> str:
        """Get the update_task endpoint URL."""
        return f"{self.api_url}/api/callbacks/update-task"
    
    @property
    def request_permission_url(self) -> str:
        """Get the request_permission endpoint URL."""
        return f"{self.api_url}/api/callbacks/request-permission"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "api_url": self.api_url,
            "invocation_id": self.invocation_id,
            "callback_token": "***",
            "is_configured": self.is_configured,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string (with masked token)."""
        return json.dumps(self.to_dict())


def get_callback_config() -> Optional[CallbackConfig]:
    """
    Read callback credentials from environment variables.
    
    Expected environment variables:
    - CAT_CAFE_API_URL: Base URL for the Cat Café API (e.g., http://localhost:8000)
    - CAT_CAFE_INVOCATION_ID: Invocation ID for this agent session
    - CAT_CAFE_CALLBACK_TOKEN: Callback token for authentication
    
    Returns:
        CallbackConfig if all required variables are set, None otherwise
    """
    api_url = os.getenv("CAT_CAFE_API_URL")
    invocation_id = os.getenv("CAT_CAFE_INVOCATION_ID")
    callback_token = os.getenv("CAT_CAFE_CALLBACK_TOKEN")
    
    if not api_url or not invocation_id or not callback_token:
        return None
    
    return CallbackConfig(
        api_url=api_url,
        invocation_id=invocation_id,
        callback_token=callback_token,
    )


async def post_message_tool(
    content: str,
    message_type: str = "text",
) -> Dict[str, Any]:
    """
    MCP tool: post_message
    
    Posts a message to the chat room via HTTP callback.
    
    Use this tool when you want to:
    - Communicate with other agents
    - Share information with the thread
    - Request help from specific agents via @mentions
    
    Args:
        content: The message content to post
        message_type: Type of message (text, tool_call, tool_result, done)
    
    Returns:
        Dict with:
        - success: Whether the message was posted successfully
        - message_id: ID of the created message
        - error: Error message if failed
    
    Example:
        {"success": true, "message_id": "msg-123", "thread_id": "thread-abc"}
    """
    config = get_callback_config()
    if not config or not config.is_configured:
        return {
            "success": False,
            "error": "Callback not configured. Set CAT_CAFE_API_URL, CAT_CAFE_INVOCATION_ID, CAT_CAFE_CALLBACK_TOKEN",
        }
    
    if not HTTPX_AVAILABLE:
        return {
            "success": False,
            "error": "httpx not installed. Install with: pip install httpx",
        }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                config.post_message_url,
                json={
                    "invocation_id": config.invocation_id,
                    "callback_token": config.callback_token,
                    "content": content,
                    "message_type": message_type,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP error {e.response.status_code}: {e.response.text}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to post message: {str(e)}",
        }


async def get_thread_context_tool(limit: int = 50) -> Dict[str, Any]:
    """
    MCP tool: get_thread_context
    
    Requests recent messages from the current thread context.
    
    Use this tool to:
    - Get conversation history
    - Understand thread context before responding
    - Avoid repeating information already shared
    
    Args:
        limit: Maximum number of messages to return (default: 50)
    
    Returns:
        Dict with:
        - success: Whether the request was successful
        - thread_id: ID of the thread
        - messages: List of recent messages
        - message_count: Total number of messages returned
    
    Example:
        {
            "success": true,
            "thread_id": "thread-abc",
            "messages": [...],
            "message_count": 5
        }
    """
    config = get_callback_config()
    if not config or not config.is_configured:
        return {
            "success": False,
            "error": "Callback not configured. Set CAT_CAFE_API_URL, CAT_CAFE_INVOCATION_ID, CAT_CAFE_CALLBACK_TOKEN",
        }
    
    if not HTTPX_AVAILABLE:
        return {
            "success": False,
            "error": "httpx not installed. Install with: pip install httpx",
        }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                config.thread_context_url,
                params={
                    "invocation_id": config.invocation_id,
                    "callback_token": config.callback_token,
                    "limit": limit,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP error {e.response.status_code}: {e.response.text}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get thread context: {str(e)}",
        }


async def get_pending_mentions_tool() -> Dict[str, Any]:
    """
    MCP tool: get_pending_mentions
    
    Checks for @mentions targeting this agent that may require attention.
    
    Use this tool to:
    - Find messages where you were mentioned
    - Identify pending work assigned to you
    - See if other agents need your help
    
    Returns:
        Dict with:
        - success: Whether the request was successful
        - agent_id: This agent's ID
        - pending_count: Number of pending mentions
        - mentions: List of mention objects with source, content, timestamp
    
    Example:
        {
            "success": true,
            "agent_id": "bollumao",
            "pending_count": 2,
            "mentions": [
                {"source_agent": "mainemao", "content": "@布偶猫 help me...", "timestamp": "2024-01-15T10:30:00"}
            ]
        }
    """
    config = get_callback_config()
    if not config or not config.is_configured:
        return {
            "success": False,
            "error": "Callback not configured. Set CAT_CAFE_API_URL, CAT_CAFE_INVOCATION_ID, CAT_CAFE_CALLBACK_TOKEN",
        }
    
    if not HTTPX_AVAILABLE:
        return {
            "success": False,
            "error": "httpx not installed. Install with: pip install httpx",
        }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                config.pending_mentions_url,
                params={
                    "invocation_id": config.invocation_id,
                    "callback_token": config.callback_token,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP error {e.response.status_code}: {e.response.text}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get pending mentions: {str(e)}",
        }


async def update_task_tool(task_id: str, status: str, result: Optional[str] = None) -> Dict[str, Any]:
    """
    MCP tool: update_task
    
    Updates the status of a task or invocation.
    
    Use this tool to:
    - Mark tasks as completed
    - Report task progress
    - CANCEL or pause long-running tasks
    
    Args:
        task_id: ID of the task to update
        status: New status (completed, in_progress, cancelled, paused)
        result: Optional result or output of the task
    
    Returns:
        Dict with success status and task details
    """
    config = get_callback_config()
    if not config or not config.is_configured:
        return {
            "success": False,
            "error": "Callback not configured",
        }
    
    if not HTTPX_AVAILABLE:
        return {
            "success": False,
            "error": "httpx not installed. Install with: pip install httpx",
        }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                config.update_task_url,
                json={
                    "invocation_id": config.invocation_id,
                    "callback_token": config.callback_token,
                    "task_id": task_id,
                    "status": status,
                    "result": result,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP error {e.response.status_code}: {e.response.text}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update task: {str(e)}",
        }


async def request_permission_tool(
    task_description: str,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    MCP tool: request_permission
    
    Requests permission to perform a potentially expensive operation.
    
    Use this tool to:
    - Ask for permission before long-running tasks
    - Request access to restricted resources
    - Seek approval for significant changes
    
    Args:
        task_description: Description of what you want to do
        reason: Why you need to do this
    
    Returns:
        Dict with:
        - success: Whether the request was submitted
        - granted: Whether permission was granted
        - denied_reason: Reason if denied
        - instructions: Any additional instructions
    
    Example:
        {
            "success": true,
            "granted": true,
            "instructions": "Please proceed with caution"
        }
    """
    config = get_callback_config()
    if not config or not config.is_configured:
        return {
            "success": False,
            "error": "Callback not configured",
        }
    
    if not HTTPX_AVAILABLE:
        return {
            "success": False,
            "error": "httpx not installed. Install with: pip install httpx",
        }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                config.request_permission_url,
                json={
                    "invocation_id": config.invocation_id,
                    "callback_token": config.callback_token,
                    "task_description": task_description,
                    "reason": reason,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP error {e.response.status_code}: {e.response.text}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to request permission: {str(e)}",
        }


# Tool definitions for MCP registration
MCP_TOOLS = [
    {
        "name": "post_message",
        "description": "Post a message to the chat. Use this to communicate with other agents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The message content to post",
                },
                "message_type": {
                    "type": "string",
                    "enum": ["text", "tool_call", "tool_result", "done"],
                    "description": "Type of message",
                    "default": "text",
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "get_thread_context",
        "description": "Get recent messages from the current thread. Use this to understand context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of messages to return",
                    "default": 50,
                },
            },
        },
    },
    {
        "name": "get_pending_mentions",
        "description": "Check for @mentions targeting this agent. Use this to find work assigned to you.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "update_task",
        "description": "Update the status of a task. Use this to mark tasks as completed or cancel them.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "ID of the task"},
                "status": {
                    "type": "string",
                    "enum": ["completed", "in_progress", "cancelled", "paused"],
                    "description": "New status",
                },
                "result": {"type": "string", "description": "Optional result"},
            },
            "required": ["task_id", "status"],
        },
    },
    {
        "name": "request_permission",
        "description": "Request permission to perform an operation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_description": {"type": "string", "description": "What you want to do"},
                "reason": {"type": "string", "description": "Why you need to do it"},
            },
            "required": ["task_description"],
        },
    },
]


def get_mcp_tool_definitions() -> list:
    """Get all MCP tool definitions for registration."""
    return MCP_TOOLS


__all__ = [
    "CallbackConfig",
    "get_callback_config",
    "post_message_tool",
    "get_thread_context_tool",
    "get_pending_mentions_tool",
    "update_task_tool",
    "request_permission_tool",
    "MCP_TOOLS",
    "get_mcp_tool_definitions",
]
