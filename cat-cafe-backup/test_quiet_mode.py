"""Test quiet mode with minimal logging."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.config import settings
from core.models import AgentMessage, Session
from core.session_manager import get_session_manager


def test_quiet_mode():
    """Test system with minimal logging (quiet mode)."""
    settings.log_level = "CRITICAL"
    logging.basicConfig(level=logging.CRITICAL, force=True)

    manager = get_session_manager()
    session = manager.create_session(session_id="quiet-test-1", thread_id="thread-1")

    message = AgentMessage(
        type="text",
        agent_id="bollumao",
        content="Quiet mode test",
        thread_id="thread-1"
    )
    manager.add_message_to_session(session.id, message)

    assert len(session.messages) == 1
    assert session.messages[0].content == "Quiet mode test"
    assert session.messages[0].thread_id == "thread-1"

    print("✓ Quiet mode test passed")


if __name__ == "__main__":
    test_quiet_mode()
