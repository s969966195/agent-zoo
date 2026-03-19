"""
Agent Configuration Dataclass for Zoo Multi-Agent System.

Defines the configuration schema for animal agents.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AgentConfig:
    """Configuration for an animal agent."""
    
    animal_id: str
    name: str
    species: str
    cli_path: str
    cli_args: List[str] = field(default_factory=list)
    color: str = "#4A90E2"
    mention_patterns: List[str] = field(default_factory=list)
    enabled: bool = True