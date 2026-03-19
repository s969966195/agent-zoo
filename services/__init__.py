"""
Zoo Multi-Agent System - Phase 3-4: MCP Callback + A2A Routing

This module provides the complete implementation for:
1. MCP HTTP callback handling
2. Animal-to-Animal routing via @mentions
3. Non-native MCP agent support via prompt injection

FILES CREATED:
- utils/a2a_mentions.py: Mention parsing and animal config
- services/invocation_tracker.py: Active invocation tracking with AbortController
- services/mcp_callback_router.py: HTTP callback handlers
- services/mcp_prompt_injector.py: Callback instructions for non-native MCP
- services/route_strategies.py: Serial and dynamic worklist strategies
- services/a2a_router.py: @mention routing with depth limit enforcement
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.a2a_mentions import ANIMAL_CONFIGS, parse_a2a_mentions
    from services.invocation_tracker import (
        InvocationTracker,
        InvocationRecord,
        AbortController,
        AbortSignal,
        get_invocation_tracker,
    )
    from services.mcp_callback_router import (
        MCPHTTPCallbackRouter,
        CallbackResponse,
        post_message,
        get_thread_context,
        get_pending_mentions,
        get_callback_router,
    )
    from services.mcp_prompt_injector import (
        MCPPromptInjector,
        get_mcp_injector,
        inject_for_animal,
        get_curl_commands,
    )
    from services.route_strategies import (
        RouteStrategy,
        SerialRouteStrategy,
        DynamicWorklistStrategy,
        AdaptiveStrategy,
        create_strategy,
        RouteTask,
        RouteResult,
        DEFAULT_DEPTH_LIMIT,
    )
    from services.a2a_router import (
        A2ARouter,
        A2AMessage,
        RoutingDecision,
        get_a2a_router,
        route_mentions,
        route_message_to_animal,
        cancel_routing,
    )
    from services.agent_dispatcher import (
        AgentDispatcher,
        DispatchResult,
    )

__all__ = [
    # utils
    "ANIMAL_CONFIGS",
    "parse_a2a_mentions",
    # services
    "InvocationTracker",
    "InvocationRecord",
    "AbortController",
    "AbortSignal",
    "get_invocation_tracker",
    "MCPHTTPCallbackRouter",
    "CallbackResponse",
    "post_message",
    "get_thread_context",
    "get_pending_mentions",
    "get_callback_router",
    "MCPPromptInjector",
    "get_mcp_injector",
    "inject_for_animal",
    "get_curl_commands",
    "RouteStrategy",
    "SerialRouteStrategy",
    "DynamicWorklistStrategy",
    "AdaptiveStrategy",
    "create_strategy",
    "RouteTask",
    "RouteResult",
    "DEFAULT_DEPTH_LIMIT",
    "A2ARouter",
    "A2AMessage",
    "RoutingDecision",
    "get_a2a_router",
    "route_mentions",
    "route_message_to_animal",
    "cancel_routing",
    # agent dispatcher
    "AgentDispatcher",
    "DispatchResult",
]

__version__ = "1.0.0"
PHASE = "Phase 3-4"
DESCRIPTION = "MCP Callback + A2A Routing for Zoo Multi-Agent System"
