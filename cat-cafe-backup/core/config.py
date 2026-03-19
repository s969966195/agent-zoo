"""
Cat Café Multi-Agent System - Configuration Management

Configuration loading using pydantic-settings with YAML file and environment variable support.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache
import yaml

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and YAML config.
    
    Priority (highest to lowest):
    1. Environment variables
    2. YAML config file
    3. Default values
    """
    model_config = SettingsConfigDict(
        env_prefix="CAT_CAFE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application settings
    app_name: str = "Cat Café Multi-Agent System"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # CLI tool paths
    bollumao_cli_path: str = "./cli/bollumao.sh"
    mainemao_cli_path: str = "./cli/mainemao.sh"
    xianluomao_cli_path: str = "./cli/xianluomao.sh"
    
    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_url: Optional[str] = None
    
    # Database configuration
    database_url: str = "sqlite:///./cat-cafe.db"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    # WebSocket configuration
    websocket_host: str = "0.0.0.0"
    websocket_port: int = 8765
    websocket_heartbeat_interval: int = 30
    websocket_max_connections: int = 100
    
    # Session configuration
    session_ttl_seconds: int = 3600  # 1 hour
    message_retention_days: int = 30
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Optional: Load from YAML file if specified
    config_file: Optional[str] = None
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return upper_v


@lru_cache
def get_settings() -> Settings:
    """
    Get cached Settings instance.
    
    Uses LRU cache to ensure single configuration loading.
    """
    settings = Settings()
    
    # Override with YAML file if specified
    if settings.config_file:
        _load_yaml_config(settings, settings.config_file)
    
    return settings


def _load_yaml_config(settings: Settings, config_path: str) -> None:
    """Load configuration from YAML file and override settings."""
    try:
        path = Path(config_path)
        if not path.exists():
            return
        
        with open(path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f)
        
        if not yaml_config:
            return
        
        # Apply YAML config to settings
        for key, value in yaml_config.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
    except Exception as e:
        # Log warning but don't fail - use defaults
        print(f"Warning: Failed to load config file: {e}")


def get_cli_path(agent_id: str) -> str:
    """Get the CLI path for a specific agent."""
    settings = get_settings()
    paths = {
        "bollumao": settings.bollumao_cli_path,
        "mainemao": settings.mainemao_cli_path,
        "xianluomao": settings.xianluomao_cli_path,
    }
    return paths.get(agent_id, f"./cli/{agent_id}.sh")


# Create singleton settings instance
settings = get_settings()


def get_redis_config() -> Dict[str, Any]:
    """Get Redis connection configuration as a dictionary."""
    settings = get_settings()
    
    if settings.redis_url:
        return {"url": settings.redis_url}
    
    return {
        "host": settings.redis_host,
        "port": settings.redis_port,
        "db": settings.redis_db,
        "password": settings.redis_password,
    }


def get_database_config() -> Dict[str, Any]:
    """Get database connection configuration as a dictionary."""
    settings = get_settings()
    return {
        "database_url": settings.database_url,
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
    }


__all__ = [
    "Settings",
    "get_settings",
    "settings",
    "get_cli_path",
    "get_redis_config",
    "get_database_config",
]
