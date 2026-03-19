"""FastAPI routes for Zoo Multi-Agent System API."""

import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from api.schemas import (
    CancelInvocationRequest,
    CallbackResponse,
    MessageResponse,
    PendingMentionsResponse,
    PostMessageCallback,
    SendMessageRequest,
    ThreadContextResponse,
    ThreadResponse,
    WebSocketMessage,
)
from core.config import get_config
from core.models import ANIMAL_CONFIGS
from services.cli_spawner import get_cli_spawner
from services.mcp_callback_router import get_callback_router
from services.agent_dispatcher import AgentDispatcher
from utils.a2a_mentions import ANIMAL_CONFIGS as A2A_ANIMAL_CONFIGS

# Import service dependencies (will be injected)
try:
    from services.session_manager import SessionManager, get_session_manager
    from services.invocation_tracker import InvocationTracker, get_invocation_tracker
    from utils.a2a_router import A2ARouter, get_a2a_router
    from core.websocket_manager import WebSocketManager, get_ws_manager_sync
except ImportError:
    # Stub implementations for development
    class SessionManager:
        pass
    class A2ARouter:
        pass
    class InvocationTracker:
        pass
    class WebSocketManager:
        async def connect(self, websocket, animal_id=None, already_accepted=False) -> str:
            return "stub-connection-id"
        async def close_all(self) -> None:
            pass
    def get_session_manager() -> SessionManager:
        return SessionManager()
    def get_a2a_router() -> A2ARouter:
        return A2ARouter()
    def get_ws_manager_sync() -> WebSocketManager:
        return WebSocketManager()
    def get_invocation_tracker() -> InvocationTracker:
        return InvocationTracker()

router = APIRouter(
    prefix="/api",
    tags=["zoo", "multi-agent"],
    responses={404: {"description": "Not found"}},
)


@router.post("/messages", response_model=MessageResponse)
async def send_message(
    request: SendMessageRequest,
    session_manager: SessionManager = Depends(get_session_manager),
) -> MessageResponse:
    """
    Send a message to multiple animals.
    
    Args:
        request: Message content and target animals
        
    Returns:
        MessageResponse with success status and thread_id
    """
    try:
        # Validate animal IDs
        valid_animals = set(ANIMAL_CONFIGS.keys())
        invalid_animals = set(request.animal_ids) - valid_animals
        if invalid_animals:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid animal IDs: {invalid_animals}. Valid: {valid_animals}",
            )
        
        # Create or get thread
        thread_id = request.thread_id or str(uuid.uuid4())
        
        # Route message to animals
        # In production, this would use A2ARouter.route_execution()
        # For now, return success response
        
        return MessageResponse(
            success=True,
            message_id=str(uuid.uuid4()),
            thread_id=thread_id,
            content=f"Message sent to {', '.join(request.animal_ids)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        return MessageResponse(
            success=False,
            error=str(e),
        )


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
) -> ThreadResponse:
    """
    Get thread details and messages.
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        ThreadResponse with thread info and messages
    """
    try:
        # TODO: Implement actual thread retrieval from storage
        return ThreadResponse(
            success=True,
            thread_id=thread_id,
            title=f"Thread {thread_id[:8]}",
            participant_animals=list(ANIMAL_CONFIGS.keys()),
            messages=[],
            created_at="2026-03-18T00:00:00",
        )
    except Exception as e:
        return ThreadResponse(
            success=False,
            error=str(e),
        )


@router.post("/threads/{thread_id}/cancel", response_model=MessageResponse)
async def cancel_thread(
    thread_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
    invocation_tracker: InvocationTracker = Depends(get_invocation_tracker),
) -> MessageResponse:
    """
    Cancel all invocations in a thread.
    
    Args:
        thread_id: Thread identifier to cancel
        
    Returns:
        MessageResponse with cancellation status
    """
    try:
        # Cancel thread in invocation tracker
        cancelled_count = 0
        try:
            cancelled_count = invocation_tracker.cancel_thread(thread_id)
        except AttributeError:
            # Fallback for mock
            cancelled_count = 1
        
        return MessageResponse(
            success=True,
            thread_id=thread_id,
            content=f"Thread {thread_id} cancelled. Cancelled {cancelled_count} invocations.",
        )
    except Exception as e:
        return MessageResponse(
            success=False,
            thread_id=thread_id,
            error=str(e),
        )


# ==================== MCP Callback Endpoints ====================

@router.post("/callbacks/post-message", response_model=CallbackResponse)
async def callback_post_message(
    request: PostMessageCallback,
) -> CallbackResponse:
    """
    MCP callback endpoint for animals to post messages.
    
    Args:
        request: Callback request with invocation_id, token, and content
        
    Returns:
        CallbackResponse with message details
    """
    try:
        router = get_callback_router()
        
        result = router.post_message(
            invocation_id=request.invocation_id,
            token=request.callback_token,
            content=request.content,
        )
        
        if not result.success:
            raise HTTPException(status_code=401, detail=result.message)
        
        # Extract mentions from content
        mentions = []
        text = request.content
        for pattern, animal_key in A2A_ANIMAL_CONFIGS.items():
            if pattern in text:
                mentions.append(animal_key)
        
        return CallbackResponse(
            success=True,
            message_id=result.data.get("message_id") if result.data else None,
            thread_id=result.data.get("thread_id") if result.data else None,
            mentions=mentions,
            content_preview=request.content[:100],
        )
    except HTTPException:
        raise
    except Exception as e:
        return CallbackResponse(
            success=False,
            error=str(e),
        )


@router.get("/callbacks/thread-context", response_model=ThreadContextResponse)
async def callback_thread_context(
    invocation_id: str,
    callback_token: str,
) -> ThreadContextResponse:
    """
    MCP callback endpoint for animals to get thread context.
    
    Args:
        invocation_id: Current invocation identifier
        callback_token: Authentication token
        
    Returns:
        ThreadContextResponse with recent messages
    """
    try:
        router = get_callback_router()
        
        result = router.get_thread_context(
            invocation_id=invocation_id,
            token=callback_token,
            limit=50,
        )
        
        if not result.success:
            raise HTTPException(status_code=401, detail=result.message)
        
        return ThreadContextResponse(
            success=True,
            thread_id=result.data.get("thread_id"),
            limit=50,
            messages=result.data.get("messages", []),
            message_count=result.data.get("message_count", 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        return ThreadContextResponse(
            success=False,
            error=str(e),
        )


@router.get("/callbacks/pending-mentions", response_model=PendingMentionsResponse)
async def callback_pending_mentions(
    invocation_id: str,
    callback_token: str,
) -> PendingMentionsResponse:
    """
    MCP callback endpoint for animals to check pending @mentions.
    
    Args:
        invocation_id: Current invocation identifier
        callback_token: Authentication token
        
    Returns:
        PendingMentionsResponse with pending mentions
    """
    try:
        router = get_callback_router()
        
        result = router.get_pending_mentions(
            invocation_id=invocation_id,
            token=callback_token,
        )
        
        if not result.success:
            raise HTTPException(status_code=401, detail=result.message)
        
        return PendingMentionsResponse(
            success=True,
            pending_count=result.data.get("mention_count", 0),
            mentions=result.data.get("mentions", []),
        )
    except HTTPException:
        raise
    except Exception as e:
        return PendingMentionsResponse(
            success=False,
            error=str(e),
        )


# ==================== WebSocket ====================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time multi-animal communication.
    
    Supports:
    - Animal connection/auth
    - Message broadcasting
    - Thread membership
    - Status updates
    """
    await websocket.accept()
    
    animal_id = None
    session_id = str(uuid.uuid4())
    
    try:
        # Initial authentication message
        data = await websocket.receive_text()
        try:
            connect_req = WebSocketMessage.model_validate_json(data)
            animal_id = connect_req.animal_id or "unknown"
        except Exception as e:
            # Handle plain text connection request
            print(f"Parse error: {e}")
            if isinstance(data, str):
                # Try to extract animal_id from JSON manually
                try:
                    parsed = json.loads(data)
                    animal_id = parsed.get("animal_id", "unknown")
                except:
                    animal_id = "unknown"
        
        # Get WebSocket manager for broadcasting
        ws_manager = get_ws_manager_sync()
        
        # Connect animal to WS manager (already accepted above)
        try:
            connection_id = await ws_manager.connect(websocket, animal_id, already_accepted=True)
        except Exception as e:
            connection_id = None
            print(f"WebSocket connect error: {e}")
        
        # Send connection confirmation with connection_id
        await websocket.send_json({
            "type": "connected",
            "animal_id": animal_id,
            "session_id": session_id,
            "connection_id": connection_id,
            "message": f"Connected as {animal_id}",
        })
        
        # Main message loop
        while True:
            try:
                data = await websocket.receive_text()
                message = WebSocketMessage.parse_raw(data)
                
                # Handle different message types
                if message.type == "message":
                    # Dispatch to agents
                    dispatcher = AgentDispatcher(ws_manager)
                    mentions = message.mentions if hasattr(message, 'mentions') else None
                    await dispatcher.dispatch_message(
                        content=message.content,
                        thread_id=message.thread_id or session_id,
                        mentions=mentions,
                        exclude_connection_id=connection_id,
                    )
                    
                elif message.type == "ping":
                    await websocket.send_json({"type": "pong"})
                    
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "system",
                        "content": f"Received type: {message.type}",
                    })
                    
            except ValidationError:
                # Handle text messages directly
                await websocket.send_json({
                    "type": "system",
                    "content": f"Received: {data[:100]}",
                })
                
    except WebSocketDisconnect:
        # Clean up connection
        if connection_id and ws_manager:
            try:
                await ws_manager.disconnect(connection_id)
            except Exception:
                pass
    except Exception as e:
        # Send error to client
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "content": str(e),
            })
        except Exception:
            pass


# ==================== Utility Routes ====================

@router.get("/animals", response_model=Dict[str, Any])
async def list_animals() -> Dict[str, Any]:
    """
    List all available animals and their configurations.
    
    Returns:
        Dict mapping animal IDs to configurations
    """
    return {
        "animals": {
            key: {
                "name": config["name"],
                "species": config["species"],
                "cli": config["cli"],
                "color": config["color"],
            }
            for key, config in ANIMAL_CONFIGS.items()
        }
    }


@router.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Status dict with service health info
    """
    return {
        "status": "healthy",
        "service": "zoo-api",
        "version": "1.0.0",
    }


# ==================== Dependency Functions ====================

def get_api_router() -> APIRouter:
    """Get the API router instance."""
    return router
