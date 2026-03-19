"""
Identity and Soul loader for Zoo Multi-Agent System.

Loads IDENTITY.md and SOUL.md files for each agent.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
import re


@dataclass
class AgentIdentity:
    """Represents an agent's identity information."""
    name: str
    creature_type: str
    visual_description: str
    vibe: str


@dataclass
class AgentSoul:
    """Represents an agent's soul/personality information."""
    personality: List[str] = field(default_factory=list)
    communication_style: List[str] = field(default_factory=list)
    expertise: Dict[str, List[str]] = field(default_factory=dict)


# Cache for loaded identities and souls
_identity_cache: Dict[str, AgentIdentity] = {}
_soul_cache: Dict[str, AgentSoul] = {}


def _parse_section(content: str, section_name: str) -> Optional[str]:
    """
    Extract section content from markdown.
    
    Args:
        content: Full markdown content
        section_name: Section header to find (e.g., "Name", "Creature Type")
        
    Returns:
        Section content or None if not found
    """
    # Match section headers with ## prefix
    pattern = rf'##\s+{re.escape(section_name)}\s*\n(.*?)(?=\n##\s+|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _parse_list_section(content: str, section_name: str) -> List[str]:
    """
    Extract list items from a markdown section.
    
    Args:
        content: Full markdown content
        section_name: Section header to find
        
    Returns:
        List of items (stripped of leading - or *)
    """
    section = _parse_section(content, section_name)
    if not section:
        return []
    
    items = []
    for line in section.split('\n'):
        line = line.strip()
        # Match list items starting with - or *
        if line.startswith('- ') or line.startswith('* '):
            items.append(line[2:].strip())
        elif line.startswith('-') or line.startswith('*'):
            items.append(line[1:].strip())
    
    return items


def _parse_expertise_section(content: str) -> Dict[str, List[str]]:
    """
    Parse expertise section with category: items format.
    
    Handles formats like:
    - Deep knowledge: Software architecture, Python
    - Working knowledge: DevOps, databases
    
    Returns:
        Dict mapping category to list of expertise items
    """
    section = _parse_section(content, "Expertise")
    if not section:
        return {}
    
    expertise: Dict[str, List[str]] = {}
    current_category = "general"
    
    for line in section.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Check for category pattern: "Category: items"
        category_match = re.match(r'^([^:]+):\s*(.+)$', line)
        if category_match:
            current_category = category_match.group(1).strip()
            items_str = category_match.group(2).strip()
            # Split by comma if multiple items on same line
            items = [item.strip() for item in items_str.split(',') if item.strip()]
            if items:
                expertise[current_category] = items
        elif line.startswith('- ') or line.startswith('* '):
            # List item under current category
            item = line[2:].strip()
            if current_category not in expertise:
                expertise[current_category] = []
            expertise[current_category].append(item)
    
    return expertise


def load_identity(agent_dir: Path) -> Optional[AgentIdentity]:
    """
    Load agent identity from IDENTITY.md file.
    
    Args:
        agent_dir: Path to agent directory containing IDENTITY.md
        
    Returns:
        AgentIdentity if file exists and is valid, None otherwise
    """
    if not isinstance(agent_dir, Path):
        agent_dir = Path(agent_dir)
    
    # Check cache
    cache_key = str(agent_dir.resolve())
    if cache_key in _identity_cache:
        return _identity_cache[cache_key]
    
    identity_path = agent_dir / "IDENTITY.md"
    if not identity_path.exists():
        return None
    
    try:
        content = identity_path.read_text(encoding='utf-8')
        
        name = _parse_section(content, "Name") or ""
        creature_type = _parse_section(content, "Creature Type") or ""
        visual_description = _parse_section(content, "Visual Description") or ""
        vibe = _parse_section(content, "Vibe") or ""
        
        identity = AgentIdentity(
            name=name,
            creature_type=creature_type,
            visual_description=visual_description,
            vibe=vibe,
        )
        
        _identity_cache[cache_key] = identity
        return identity
        
    except Exception:
        return None


def load_soul(agent_dir: Path) -> Optional[AgentSoul]:
    """
    Load agent soul from SOUL.md file.
    
    Args:
        agent_dir: Path to agent directory containing SOUL.md
        
    Returns:
        AgentSoul if file exists and is valid, None otherwise
    """
    if not isinstance(agent_dir, Path):
        agent_dir = Path(agent_dir)
    
    # Check cache
    cache_key = str(agent_dir.resolve())
    if cache_key in _soul_cache:
        return _soul_cache[cache_key]
    
    soul_path = agent_dir / "SOUL.md"
    if not soul_path.exists():
        return None
    
    try:
        content = soul_path.read_text(encoding='utf-8')
        
        personality = _parse_list_section(content, "Personality")
        communication_style = _parse_list_section(content, "Communication Style")
        expertise = _parse_expertise_section(content)
        
        soul = AgentSoul(
            personality=personality,
            communication_style=communication_style,
            expertise=expertise,
        )
        
        _soul_cache[cache_key] = soul
        return soul
        
    except Exception:
        return None


def clear_cache() -> None:
    """Clear the identity and soul cache. Useful for testing."""
    global _identity_cache, _soul_cache
    _identity_cache = {}
    _soul_cache = {}