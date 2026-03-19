"""Zoo Multi-Agent System API Layer (Phase 5).

Provides FastAPI routes, Pydantic schemas, and dependency injection
for the multi-animal collaboration system.
"""

from api.schemas import (
    SendMessageRequest,
    PostMessageCallback,
    CancelInvocationRequest,
    MessageResponse,
    ThreadResponse,
    CancelResponse,
    CallbackResponse,
    ThreadContextResponse,
    PendingMentionsResponse,
    WebSocketMessage,
    WebSocketConnect,
    WebsocketStatusResponse,
)
from api.routes import get_api_router, router
from api.dependencies import (
    get_session_manager,
    get_invocation_tracker,
    get_a2a_router,
    get_callback_router,
    get_websocket_manager,
    get_animal_config,
    get_all_animals,
)

__all__ = [
    # Schemas
    "SendMessageRequest",
    "PostMessageCallback",
    "CancelInvocationRequest",
    "MessageResponse",
    "ThreadResponse",
    "CancelResponse",
    "CallbackResponse",
    "ThreadContextResponse",
    "PendingMentionsResponse",
    "WebSocketMessage",
    "WebSocketConnect",
    "WebsocketStatusResponse",
    # Routes
    "get_api_router",
    "router",
    # Dependencies
    "get_session_manager",
    "get_invocation_tracker",
    "get_a2a_router",
    "get_callback_router",
    "get_websocket_manager",
    "get_animal_config",
    "get_all_animals",
]
