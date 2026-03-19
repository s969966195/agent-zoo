"""
Cat Café Multi-Agent System - A2A Mention Parsing Utilities

Parses @mentions from agent responses for inter-agent routing.
"""

import re
from typing import Optional, List, Dict

# Agent configurations with name patterns
CAT_CONFIGS: Dict[str, Dict[str, str | List[str]]] = {
    'bollumao': {
        'name': '布偶猫',
        'patterns': ['@布偶', '@布偶猫', '@bollumao', '@bmu']
    },
    'mainemao': {
        'name': '缅因猫',
        'patterns': ['@缅因', '@缅因猫', '@mainemao', '@maine']
    },
    'xianluomao': {
        'name': '暹罗猫',
        'patterns': ['@暹罗', '@暹罗猫', '@xianluomao', '@siamese', '@xian']
    }
}

# Reverse mapping from mention text to agent_id
MENTION_TO_AGENT: Dict[str, str] = {}
for agent_id, config in CAT_CONFIGS.items():
    for pattern in config['patterns']:
        MENTION_TO_AGENT[pattern] = agent_id


def strip_code_blocks(text: str) -> str:
    """
    Remove Markdown code blocks from text.
    
    Handles both ```...``` and `...` code blocks.
    
    Args:
        text: Input text that may contain code blocks
        
    Returns:
        Text with code blocks removed
    """
    # Remove triple-backtick code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove inline code blocks (single backticks)
    text = re.sub(r'`[^`]+`', '', text)
    return text


def parse_a2a_mentions(text: str, current_agent: str, limit: Optional[int] = None) -> List[str]:
    """
    Parse @mentions from agent response.
    
    Rules:
    - Strip code blocks first (```...```)
    - Match at line start only (not mid-sentence)
    - Cannot mention self
    - Return first match only (or up to limit)
    
    Args:
        text: Agent response text to parse
        current_agent: Current agent's ID (to prevent self-mention)
        limit: Maximum mentions to return (None for no limit)
        
    Returns:
        List of agent IDs mentioned in the text
    """
    # Strip code blocks first
    text = strip_code_blocks(text)
    
    # Pattern: @mention at start of line (possibly with leading whitespace)
    # Line must start with optional whitespace followed by @
    line_start_pattern = r'^\s*(@[^\s@]+)'
    
    mentions: List[str] = []
    seen: set = set()
    
    for line in text.split('\n'):
        match = re.match(line_start_pattern, line)
        if match:
            mention_text = match.group(1).strip()
            agent_id = normalize_agent_id(mention_text)
            
            # Filter: must map to valid agent and not self
            if agent_id and agent_id != current_agent:
                if agent_id not in seen:
                    seen.add(agent_id)
                    mentions.append(agent_id)
                    
                    # Check limit
                    if limit is not None and len(mentions) >= limit:
                        return mentions
    
    return mentions


def normalize_agent_id(mention: str) -> Optional[str]:
    """
    Convert mention text to canonical agent_id.
    
    Args:
        mention: Mention text (e.g., "@布偶猫", "@bollumao")
        
    Returns:
        Canonical agent_id or None if not found
    """
    # Remove leading @ if present
    mention_text = mention.lstrip('@')
    
    # Try direct match first
    if mention_text in MENTION_TO_AGENT:
        return MENTION_TO_AGENT[mention_text]
    
    # Try lowercase variant
    mention_lower = mention_text.lower()
    if mention_lower in MENTION_TO_AGENT:
        return MENTION_TO_AGENT[mention_lower]
    
    # Try matching against all patterns
    for pattern, agent_id in MENTION_TO_AGENT.items():
        # Extract the mention part from the pattern (remove @)
        pattern_text = pattern.lstrip('@')
        if mention_text == pattern_text:
            return agent_id
        if mention_lower == pattern_text.lower():
            return agent_id
    
    return None


def get_agent_patterns(agent_id: str) -> List[str]:
    """
    Get all mention patterns for an agent.
    
    Args:
        agent_id: Agent ID (e.g., 'bollumao')
        
    Returns:
        List of mention patterns for this agent
    """
    config = CAT_CONFIGS.get(agent_id)
    if config:
        return list(config['patterns'])
    return []


def get_all_agent_ids() -> List[str]:
    """
    Get list of all valid agent IDs.
    
    Returns:
        List of agent IDs
    """
    return list(CAT_CONFIGS.keys())


def get_agent_name(agent_id: str) -> Optional[str]:
    """
    Get the display name for an agent.
    
    Args:
        agent_id: Agent ID
        
    Returns:
        Display name (e.g., '布偶猫') or None if not found
    """
    config = CAT_CONFIGS.get(agent_id)
    if config:
        return config['name']
    return None
