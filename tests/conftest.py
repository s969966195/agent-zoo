"""Pytest configuration and fixtures for Zoo Multi-Agent System tests."""

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator, Generator

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


# ==================== Path Fixtures ====================

@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def agents_dir(project_root: Path) -> Path:
    """Get the agents directory."""
    return project_root / "agents"


@pytest.fixture
def services_dir(project_root: Path) -> Path:
    """Get the services directory."""
    return project_root / "services"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ==================== Registry Fixtures ====================

@pytest.fixture
def clean_registry() -> Generator[None, None, None]:
    """Reset the global registry before and after each test."""
    from agents.registry import registry
    registry.clear_cache()
    yield
    registry.clear_cache()


@pytest.fixture
def mock_animal_service() -> MagicMock:
    """Create a mock AnimalService."""
    from agents.base import AnimalMessage
    
    service = MagicMock()
    service.animal_id = "test_animal"
    
    async def mock_invoke(prompt: str, thread_id: str):
        yield AnimalMessage(
            animal_id="test_animal",
            content=f"Response to: {prompt}",
            message_type="text"
        )
    
    service.invoke = mock_invoke
    return service


@pytest.fixture
def mock_animal_service_class() -> MagicMock:
    """Create a mock AnimalService class."""
    mock_instance = MagicMock()
    mock_instance.animal_id = "mock_animal"
    
    def mock_init(animal_id: str, config: dict):
        mock_instance.animal_id = animal_id
        mock_instance.config = config
        return mock_instance
    
    mock_class = MagicMock(return_value=mock_instance)
    mock_class.__name__ = "MockAnimalService"
    return mock_class


# ==================== WebSocket Fixtures ====================

@pytest.fixture
def mock_websocket() -> MagicMock:
    """Create a mock WebSocket connection."""
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.close = AsyncMock()
    websocket.raw_scope = {"time": 0.0}
    return websocket


@pytest.fixture
def mock_websocket_manager() -> MagicMock:
    """Create a mock WebSocketManager."""
    manager = MagicMock()
    manager.connect = AsyncMock(return_value="test-connection-id")
    manager.disconnect = AsyncMock()
    manager.broadcast_to_animal = AsyncMock(return_value=1)
    manager.broadcast_to_session = AsyncMock(return_value=1)
    manager.send_to_animal = AsyncMock(return_value=True)
    manager.close_all = AsyncMock()
    return manager


# ==================== CLI Spawner Fixtures ====================

@pytest.fixture
def mock_cli_spawner() -> MagicMock:
    """Create a mock CLISpawner."""
    spawner = MagicMock()
    spawner.spawn = AsyncMock()
    spawner.terminate = AsyncMock()
    spawner.is_running = MagicMock(return_value=False)
    return spawner


# ==================== Agent Dispatcher Fixtures ====================

@pytest.fixture
def agent_dispatcher(mock_websocket_manager: MagicMock) -> "AgentDispatcher":
    """Create an AgentDispatcher with mocked dependencies."""
    from services.agent_dispatcher import AgentDispatcher
    return AgentDispatcher(ws_manager=mock_websocket_manager)


# ==================== Event Loop ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==================== Identity/Soul Fixtures ====================

@pytest.fixture
def sample_identity_content() -> str:
    """Sample IDENTITY.md content for testing."""
    return """## Name
Test Animal

## Creature Type
Test Species

## Visual Description
A test animal for testing purposes.

## Vibe
Friendly and helpful.
"""


@pytest.fixture
def sample_soul_content() -> str:
    """Sample SOUL.md content for testing."""
    return """## Personality
- Friendly
- Helpful
- Curious

## Communication Style
- Clear
- Concise
- Professional

## Expertise
Deep knowledge: Python, Testing, Software Engineering
Working knowledge: JavaScript, Databases
"""


# ==================== Cache Cleanup ====================

@pytest.fixture(autouse=True)
def clear_identity_cache():
    """Clear identity/soul caches before and after each test."""
    from agents.identity import clear_cache
    clear_cache()
    yield
    clear_cache()