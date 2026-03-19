# Cat Café Multi-Agent System - Phase 1 Foundation

This directory contains the core infrastructure for the Cat Café multi-agent system.

## Phase 1 Components

### Core (`core/`)
- **models.py**: Pydantic models for AgentMessage, Session, InvocationRecord, Thread
- **config.py**: Configuration management with pydantic-settings
- **session_manager.py**: Session lifecycle management
- **websocket_manager.py**: WebSocket connection management

### Storage (`storage/`)
- **redis_client.py**: Redis connection wrapper with in-memory fallback
- **database.py**: SQLAlchemy ORM for persistent storage (SQLite/PostgreSQL)

### Configuration
- **config/settings.yaml**: Default YAML configuration

## How It Works

### Core Models
All domain models are defined in `core/models.py`:
- **AgentMessage**: Represents messages between agents with types (text, tool_call, tool_result, etc.)
- **Session**: Manages conversation sessions with message history and agent sessions
- **InvocationRecord**: Tracks tool invocations between agents with status tracking
- **Thread**: Manages discussion threads with participant tracking

### Configuration
Loaded from environment variables and YAML file with priority:
1. Environment variables (`CAT_CAFE_` prefix)
2. `config/settings.yaml`
3. Default values

### Session Manager
Manages session lifecycle using Redis for caching and SQLite/PostgreSQL for persistence.

### WebSocket Manager
Handles WebSocket connections for agent communication with:
- Connection tracking
- Message broadcasting
- Callback hooks

### Storage Layer
Two-tier storage approach:
- **Redis**: Fast caching and session management
- **SQLAlchemy**: Persistent storage with migration support

## Verification

Run `python3 -c "import sys; sys.path.insert(0, '.'); from core.models import AgentMessage, Session, InvocationRecord, Thread; from core.config import settings; from core.session_manager import session_manager; from core.websocket_manager import ws_manager; from storage.redis_client import redis_client; from storage.database import db_engine; print('All imports successful')"`
