"""
Cat Café Multi-Agent System - Redis Client

Redis connection wrapper with fallback to in-memory storage.
"""

import asyncio
import json
import pickle
from typing import Optional, Any, Dict, List
from contextlib import contextmanager
import threading

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from core.config import get_redis_config


class RedisClient:
    """
    Redis client wrapper for Cat Café with automatic fallback.
    
    Provides same interface whether using Redis or in-memory fallback.
    """
    
    def __init__(self):
        self._client = None
        self._memory_store: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._use_redis = False
        self._initialized = False
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Redis connection or fallback mode."""
        if self._initialized:
            return
        
        if not REDIS_AVAILABLE:
            self._use_redis = False
            self._initialized = True
            return
        
        try:
            config = get_redis_config()
            
            if "url" in config:
                self._client = redis.from_url(config["url"])
            else:
                self._client = redis.Redis(
                    host=config["host"],
                    port=config["port"],
                    db=config["db"],
                    password=config.get("password"),
                    decode_responses=True,
                )
            
            # Test connection
            self._client.ping()
            self._use_redis = True
        except (redis.ConnectionError, Exception) as e:
            # Fallback to in-memory
            self._use_redis = False
            self._client = None
        
        self._initialized = True
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._use_redis and self._client is not None
    
    # Key operations
    def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if self._use_redis:
            try:
                return self._client.get(key)
            except Exception:
                return None
        else:
            with self._lock:
                return self._memory_store.get(key)
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set value with optional expiration (seconds)."""
        if self._use_redis:
            try:
                if ex:
                    return self._client.set(key, value, ex=ex)
                return self._client.set(key, value)
            except Exception:
                return False
        else:
            with self._lock:
                self._memory_store[key] = value
                return True
    
    def delete(self, key: str) -> bool:
        """Delete a key."""
        if self._use_redis:
            try:
                return bool(self._client.delete(key))
            except Exception:
                return False
        else:
            with self._lock:
                if key in self._memory_store:
                    del self._memory_store[key]
                    return True
                return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if self._use_redis:
            try:
                return bool(self._client.exists(key))
            except Exception:
                return False
        else:
            return key in self._memory_store
    
    # List operations
    def rpush(self, key: str, value: str) -> int:
        """Push value to end of list."""
        if self._use_redis:
            try:
                return self._client.rpush(key, value)
            except Exception:
                return 0
        else:
            with self._lock:
                if key not in self._memory_store:
                    self._memory_store[key] = []
                self._memory_store[key].append(value)
                return len(self._memory_store[key])
    
    def lrange(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """Get range of list elements."""
        if self._use_redis:
            try:
                return self._client.lrange(key, start, end)
            except Exception:
                return []
        else:
            with self._lock:
                items = self._memory_store.get(key, [])
                return items[start:end + 1]
    
    def llen(self, key: str) -> int:
        """Get list length."""
        if self._use_redis:
            try:
                return self._client.llen(key)
            except Exception:
                return 0
        else:
            with self._lock:
                return len(self._memory_store.get(key, []))
    
    # Hash operations
    def hset(self, key: str, field: str, value: str) -> bool:
        """Set hash field."""
        if self._use_redis:
            try:
                return bool(self._client.hset(key, field, value))
            except Exception:
                return False
        else:
            with self._lock:
                if key not in self._memory_store:
                    self._memory_store[key] = {}
                self._memory_store[key][field] = value
                return True
    
    def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field."""
        if self._use_redis:
            try:
                return self._client.hget(key, field)
            except Exception:
                return None
        else:
            with self._lock:
                hash_dict = self._memory_store.get(key)
                if hash_dict:
                    return hash_dict.get(field)
                return None
    
    def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields."""
        if self._use_redis:
            try:
                return self._client.hgetall(key)
            except Exception:
                return {}
        else:
            with self._lock:
                return dict(self._memory_store.get(key, {}))
    
    def hdel(self, key: str, field: str) -> bool:
        """Delete hash field."""
        if self._use_redis:
            try:
                return bool(self._client.hdel(key, field))
            except Exception:
                return False
        else:
            with self._lock:
                hash_dict = self._memory_store.get(key)
                if hash_dict and field in hash_dict:
                    del hash_dict[field]
                    return True
                return False
    
    # Serialization helpers
    def set_json(self, key: str, data: dict, ex: Optional[int] = None) -> bool:
        """Set JSON-serialized data."""
        return self.set(key, json.dumps(data), ex=ex)
    
    def get_json(self, key: str) -> Optional[dict]:
        """Get and parse JSON data."""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    def set_pickle(self, key: str, obj: Any, ex: Optional[int] = None) -> bool:
        """Set pickled object."""
        data = pickle.dumps(obj)
        return self.set(key, data.hex(), ex=ex)
    
    def get_pickle(self, key: str) -> Optional[Any]:
        """Get and unpickle object."""
        value = self.get(key)
        if value:
            try:
                return pickle.loads(bytes.fromhex(value))
            except Exception:
                return None
        return None
    
    # Cleanup
    def close(self) -> None:
        """Close connection and cleanup."""
        if self._use_redis and self._client:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        self._memory_store.clear()
    
    def clear_all(self) -> None:
        """Clear all stored data."""
        if self._use_redis:
            try:
                self._client.flushdb()
            except Exception:
                pass
        with self._lock:
            self._memory_store.clear()


# Global instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Get the Redis client instance."""
    return redis_client


@contextmanager
def redis_context():
    """Context manager for Redis operations."""
    try:
        yield redis_client
    finally:
        pass


__all__ = [
    "RedisClient",
    "redis_client",
    "get_redis",
    "redis_context",
]
