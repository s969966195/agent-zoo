# Cat Café Multi-Agent System

A multi-agent collaboration system inspired by the Cat Café tutorials, where three AI "cats" communicate via WebSocket and HTTP callbacks to collaborate on tasks.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cat Café System                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Bollumao   │  │  Mainemao    │  │  Xianluomao  │      │
│  │    (Boba)    │  │   (Mochi)    │  │  (Mochi)     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │                │
│         └─────────────────┴─────────────────┘                │
│                           │                                  │
│                   ┌───────┴───────┐                          │
│                   │   WebSocket   │                          │
│                   │   Manager     │                          │
│                   └───────┬───────┘                          │
│                           │                                  │
│       ┌───────────────────┼───────────────────┐             │
│       │                   │                   │             │
│  ┌────▼────┐       ┌──────▼──────┐      ┌────▼────┐        │
│  │ Session │       │ Invocation  │      │  Thread │        │
│  │ Manager │       │  Manager    │      │Manager  │        │
│  └────┬────┘       └──────┬──────┘      └────┬────┘        │
│       │                   │                   │             │
│       └───────────────────┼───────────────────┘             │
│                           │                                  │
│              ┌────────────┴────────────┐                    │
│              │      Storage Layer      │                    │
│              ├─────────────────────────┤                    │
│              │   Redis (cache)         │                    │
│              │   SQLAlchemy (db)       │                    │
│              └─────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Core (`core/`)
- **models.py**: Pydantic models for messages, sessions, invocations, and threads
- **config.py**: Configuration management with pydantic-settings
- **session_manager.py**: Session lifecycle management
- **websocket_manager.py**: WebSocket connection management

### Storage (`storage/`)
- **redis_client.py**: Redis connection wrapper with in-memory fallback
- **database.py**: SQLAlchemy ORM for persistent storage

## Directory Structure

```
cat-cafe/
├── core/
│   ├── __init__.py
│   ├── models.py          # Pydantic models for AgentMessage, Session, InvocationRecord, Thread
│   ├── config.py          # Configuration management with pydantic-settings
│   ├── session_manager.py # Session lifecycle management
│   └── websocket_manager.py # WebSocket connection management
├── storage/
│   ├── __init__.py
│   ├── redis_client.py    # Redis connection wrapper
│   └── database.py        # SQLite/Postgres ORM with SQLAlchemy
├── config/
│   └── settings.yaml      # Default configuration
├── requirements.txt
└── README.md
```

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/cat-cafe.git
cd cat-cafe

# Install dependencies
pip install -r requirements.txt

# Create a .env file (optional)
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Configuration is loaded from:
1. Environment variables (highest priority)
2. `config/settings.yaml` file
3. Default values (lowest priority)

### Environment Variables

```bash
CAT_CAFE_APP_NAME="Cat Café"
CAT_CAFE_DEBUG=false
CAT_CAFE_REDIS_HOST=localhost
CAT_CAFE_REDIS_PORT=6379
CAT_CAFE_DATABASE_URL=sqlite:///./cat-cafe.db
```

### YAML Configuration

See `config/settings.yaml` for all configurable options.

## Usage

```python
from core.models import AgentMessage, Session
from core.config import settings
from core.session_manager import get_session_manager
from storage.redis_client import redis_client
from storage.database import db_engine

# Create a new session
manager = get_session_manager()
session = manager.create_session(
    session_id="session-123",
    thread_id="thread-abc"
)

# Create and add a message
message = AgentMessage(
    type="text",
    agent_id="bollumao",
    content="Hello, world!",
    thread_id="thread-abc"
)
manager.add_message_to_session(session.id, message)

# Use Redis for caching
redis_client.set_json("session:123", session.model_dump())

# Query persistent database
sessions = db_engine.get_all_sessions()
```

##_MODULES

### AgentMessage
Represents messages exchanged between agents with support for:
- Multiple message types: text, tool_call, tool_result, session_init, done
- Agent identification
- Thread association
- Metadata and mentions

### Session
Manages conversation sessions with:
- Automatic timestamp tracking
- Agent session mapping
- Message history

### InvocationRecord
Tracks tool invocations between agents:
- Status tracking (pending, active, completed, cancelled)
- Callback token verification
- Caller/target agent tracking

### Thread
Manages discussion threads:
- Participant agent tracking
- Message history
- Invocation state

## Development

```bash
# Run type checking
mypy .

# Run linter
pylint core/ storage/

# Run tests
pytest

# Format code
black core/ storage/
isort core/ storage/
```

## Deployment

### With Redis and PostgreSQL

```bash
# Set environment variables
export CAT_CAFE_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/catcafe
export CAT_CAFE_REDIS_URL=redis://localhost:6379/0

# Update settings.yaml
cat config/settings.yaml
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## API Reference

See `docs/` for detailed API documentation.

## License

MIT

## Acknowledgments

Inspired by the [Cat Café tutorials](https://github.com/zts212653/cat-cafe-tutorials) project.
