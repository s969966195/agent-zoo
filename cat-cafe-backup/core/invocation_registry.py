"""
Cat Café Multi-Agent System - Invocation Registry

Tracks tool invocations between agents for callback verification.
"""

import uuid
import datetime
from typing import Optional, Dict, List
from collections import defaultdict
import threading

from core.types import InvocationRecord, CallbackToken


class InvocationRegistry:
    """
    Manages invocations and their associated callback tokens.
    
    Tracks which agents are waiting for responses and validates
    callback requests from agents.
    """
    
    def __init__(self):
        self._invocations: Dict[str, InvocationRecord] = {}
        self._tokens: Dict[str, CallbackToken] = {}
        self._invocations_by_agent: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def create_invocation(
        self,
        caller_agent: Optional[str],
        target_agent: str,
        thread_id: str,
        ttl_seconds: int = 300,
    ) -> InvocationRecord:
        """Create a new invocation for agent callback."""
        with self._lock:
            invocation = InvocationRecord(
                id=str(uuid.uuid4()),
                caller_agent=caller_agent,
                target_agent=target_agent,
                thread_id=thread_id,
                callback_token=str(uuid.uuid4()),
            )
            
            # Create callback token
            token = CallbackToken(
                token=invocation.callback_token,
                agent_id=target_agent,
                thread_id=thread_id,
                created_at=datetime.datetime.utcnow(),
                expires_at=datetime.datetime.utcnow() + datetime.timedelta(seconds=ttl_seconds),
                max_uses=1,
            )
            
            self._invocations[invocation.id] = invocation
            self._tokens[invocation.callback_token] = token
            self._invocations_by_agent[target_agent].append(invocation.id)
            
            return invocation
    
    def get_invocation(self, invocation_id: str) -> Optional[InvocationRecord]:
        """Get an invocation by ID."""
        with self._lock:
            return self._invocations.get(invocation_id)
    
    def get_invocation_by_token(self, token: str) -> Optional[InvocationRecord]:
        """Get invocation by callback token."""
        with self._lock:
            callback_token = self._tokens.get(token)
            if callback_token:
                return self._invocations.get(callback_token.token)
            return None
    
    def validate_token(self, invocation_id: str, callback_token: str) -> bool:
        """Validate callback token for invocation."""
        with self._lock:
            invocation = self._invocations.get(invocation_id)
            if not invocation:
                return False
            
            if invocation.callback_token != callback_token:
                return False
            
            token_entry = self._tokens.get(callback_token)
            if not token_entry or not token_entry.is_valid():
                return False
            
            # Mark token as used
            token_entry.use()
            return True
    
    def complete_invocation(self, invocation_id: str) -> bool:
        """Mark invocation as completed."""
        with self._lock:
            invocation = self._invocations.get(invocation_id)
            if invocation:
                invocation.complete()
                return True
            return False
    
    def cancel_invocation(self, invocation_id: str) -> bool:
        """Cancel an invocation."""
        with self._lock:
            invocation = self._invocations.get(invocation_id)
            if invocation:
                invocation.cancel()
                return True
            return False
    
    def get_pending_invocations(self, agent_id: str) -> List[InvocationRecord]:
        """Get pending invocations for an agent."""
        with self._lock:
            result = []
            for inv_id in self._invocations_by_agent.get(agent_id, []):
                inv = self._invocations.get(inv_id)
                if inv and inv.status == "pending":
                    result.append(inv)
            return result
    
    def get_active_invocation(self, agent_id: str) -> Optional[InvocationRecord]:
        """Get active (in-progress) invocation for agent."""
        with self._lock:
            for inv_id in self._invocations_by_agent.get(agent_id, []):
                inv = self._invocations.get(inv_id)
                if inv and inv.status == "active":
                    return inv
            return None
    
    def clear_expired_tokens(self) -> int:
        """Remove expired tokens. Returns count of removed."""
        with self._lock:
            now = datetime.datetime.utcnow()
            expired_tokens = [
                token_id
                for token_id, token in self._tokens.items()
                if not token.is_valid()
            ]
            for token_id in expired_tokens:
                del self._tokens[token_id]
            return len(expired_tokens)
    
    def to_dict(self) -> Dict:
        """Serialize registry state."""
        with self._lock:
            return {
                "invocations": {
                    k: {
                        "id": v.id,
                        "caller_agent": v.caller_agent,
                        "target_agent": v.target_agent,
                        "thread_id": v.thread_id,
                        "callback_token": v.callback_token,
                        "status": v.status,
                    }
                    for k, v in self._invocations.items()
                },
                "tokens": {
                    k: {
                        "token": v.token,
                        "agent_id": v.agent_id,
                        "thread_id": v.thread_id,
                        "active": v.active,
                        "current_uses": v.current_uses,
                    }
                    for k, v in self._tokens.items()
                },
            }


# Global singleton
invocation_registry = InvocationRegistry()


def get_invocation_registry() -> InvocationRegistry:
    """Get the global invocation registry instance."""
    return invocation_registry


__all__ = [
    "InvocationRegistry",
    "InvocationRecord",
    "CallbackToken",
    "get_invocation_registry",
]
