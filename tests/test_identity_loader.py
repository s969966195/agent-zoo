"""Tests for identity and soul loading functions."""

import pytest
from pathlib import Path

import agents.identity as identity_module
from agents.identity import (
    AgentIdentity,
    AgentSoul,
    load_identity,
    load_soul,
    clear_cache,
)


class TestLoadIdentity:
    """Tests for load_identity function."""
    
    def test_load_identity_from_file(self, temp_dir: Path, sample_identity_content: str) -> None:
        """Load IDENTITY.md file correctly."""
        # Create IDENTITY.md file
        identity_path = temp_dir / "IDENTITY.md"
        identity_path.write_text(sample_identity_content, encoding='utf-8')
        
        # Load identity
        identity = load_identity(temp_dir)
        
        assert identity is not None
        assert identity.name == "Test Animal"
        assert identity.creature_type == "Test Species"
        assert "test animal" in identity.visual_description.lower()
        assert "friendly" in identity.vibe.lower()
    
    def test_load_identity_missing_file_returns_none(self, temp_dir: Path) -> None:
        """Missing IDENTITY.md should return None."""
        identity = load_identity(temp_dir)
        
        assert identity is None
    
    def test_load_identity_cache_cleared_on_clear_cache(self, temp_dir: Path, sample_identity_content: str) -> None:
        """Cache should be cleared when clear_cache is called."""
        # Create IDENTITY.md file
        identity_path = temp_dir / "IDENTITY.md"
        identity_path.write_text(sample_identity_content, encoding='utf-8')
        
        # Load identity (caches it)
        identity1 = load_identity(temp_dir)
        
        # Verify it's cached
        cache_key = str(temp_dir.resolve())
        assert cache_key in identity_module._identity_cache
        
        # Clear cache
        clear_cache()
        
        # Verify cache is empty
        assert len(identity_module._identity_cache) == 0
    
    def test_load_identity_uses_cache(self, temp_dir: Path, sample_identity_content: str) -> None:
        """Loading identity twice should use cache."""
        # Create IDENTITY.md file
        identity_path = temp_dir / "IDENTITY.md"
        identity_path.write_text(sample_identity_content, encoding='utf-8')
        
        # Load identity twice
        identity1 = load_identity(temp_dir)
        identity2 = load_identity(temp_dir)
        
        # Should be same object (cached)
        assert identity1 is identity2
    
    def test_load_identity_with_string_path(self, temp_dir: Path, sample_identity_content: str) -> None:
        """load_identity should accept string path."""
        # Create IDENTITY.md file
        identity_path = temp_dir / "IDENTITY.md"
        identity_path.write_text(sample_identity_content, encoding='utf-8')
        
        # Load with string path
        identity = load_identity(str(temp_dir))
        
        assert identity is not None


class TestLoadSoul:
    """Tests for load_soul function."""
    
    def test_load_soul_from_file(self, temp_dir: Path, sample_soul_content: str) -> None:
        """Load SOUL.md file correctly."""
        # Create SOUL.md file
        soul_path = temp_dir / "SOUL.md"
        soul_path.write_text(sample_soul_content, encoding='utf-8')
        
        # Load soul
        soul = load_soul(temp_dir)
        
        assert soul is not None
        assert "Friendly" in soul.personality
        assert "Helpful" in soul.personality
        assert "Clear" in soul.communication_style
        assert "Deep knowledge" in soul.expertise
    
    def test_load_soul_missing_file_returns_none(self, temp_dir: Path) -> None:
        """Missing SOUL.md should return None."""
        soul = load_soul(temp_dir)
        
        assert soul is None
    
    def test_load_soul_expertise_parsing(self, temp_dir: Path) -> None:
        """Expertise section should be parsed correctly."""
        # Create SOUL.md with expertise
        soul_content = """## Personality
- Friendly

## Communication Style
- Clear

## Expertise
Deep knowledge: Python, Testing, Architecture
Working knowledge: JavaScript, DevOps
"""
        soul_path = temp_dir / "SOUL.md"
        soul_path.write_text(soul_content, encoding='utf-8')
        
        soul = load_soul(temp_dir)
        
        assert soul is not None
        assert "Deep knowledge" in soul.expertise
        assert "Python" in soul.expertise["Deep knowledge"]
        assert "Testing" in soul.expertise["Deep knowledge"]
        assert "Working knowledge" in soul.expertise
        assert "JavaScript" in soul.expertise["Working knowledge"]
    
    def test_load_soul_uses_cache(self, temp_dir: Path, sample_soul_content: str) -> None:
        """Loading soul twice should use cache."""
        # Create SOUL.md file
        soul_path = temp_dir / "SOUL.md"
        soul_path.write_text(sample_soul_content, encoding='utf-8')
        
        # Load soul twice
        soul1 = load_soul(temp_dir)
        soul2 = load_soul(temp_dir)
        
        # Should be same object (cached)
        assert soul1 is soul2


class TestAgentIdentity:
    """Tests for AgentIdentity dataclass."""
    
    def test_agent_identity_creation(self) -> None:
        """Create AgentIdentity with all fields."""
        identity = AgentIdentity(
            name="Test Animal",
            creature_type="Test Species",
            visual_description="A test animal",
            vibe="Friendly",
        )
        
        assert identity.name == "Test Animal"
        assert identity.creature_type == "Test Species"
        assert identity.visual_description == "A test animal"
        assert identity.vibe == "Friendly"


class TestAgentSoul:
    """Tests for AgentSoul dataclass."""
    
    def test_agent_soul_creation(self) -> None:
        """Create AgentSoul with all fields."""
        soul = AgentSoul(
            personality=["Friendly", "Helpful"],
            communication_style=["Clear", "Concise"],
            expertise={"Python": ["FastAPI", "Pytest"]},
        )
        
        assert soul.personality == ["Friendly", "Helpful"]
        assert soul.communication_style == ["Clear", "Concise"]
        assert "Python" in soul.expertise
    
    def test_agent_soul_defaults(self) -> None:
        """AgentSoul should have default empty collections."""
        soul = AgentSoul()
        
        assert soul.personality == []
        assert soul.communication_style == []
        assert soul.expertise == {}