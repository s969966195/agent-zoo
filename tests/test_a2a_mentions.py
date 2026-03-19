"""Tests for A2A mentions parsing."""

import pytest

from utils.a2a_mentions import (
    parse_a2a_mentions,
    get_animal_names,
    get_animal_patterns,
    ANIMAL_CONFIGS,
    PATTERN_TO_ANIMAL,
)


class TestParseMentions:
    """Tests for parse_a2a_mentions function."""
    
    def test_parse_mentions_single(self) -> None:
        """Parse a single @mention."""
        text = "Hello @雪球, how are you?"
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        assert targets == ["xueqiu"]
    
    def test_parse_mentions_multiple(self) -> None:
        """Parse multiple @mentions."""
        text = "@雪球 and @六六 please respond"
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        assert set(targets) == {"xueqiu", "liuliu"}
    
    def test_parse_mentions_ignores_self(self) -> None:
        """Cannot mention self - current_animal is excluded."""
        text = "@雪球 hello"  # xueqiu mentioning itself
        
        targets = parse_a2a_mentions(text, current_animal="xueqiu")
        
        # Self-mention should be ignored
        assert targets == []
    
    def test_parse_mentions_ignores_duplicates(self) -> None:
        """Duplicate @mentions should result in unique targets only."""
        text = "@雪球 @雪球 @雪球 hello"
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        # Should only have one xueqiu
        assert targets == ["xueqiu"]
        assert len(targets) == 1
    
    def test_parse_mentions_max_two_targets(self) -> None:
        """At most 2 targets should be returned."""
        text = "@雪球 @六六 @小黄 hello everyone!"
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        # Should only return first 2
        assert len(targets) == 2
    
    def test_parse_mentions_english_pattern(self) -> None:
        """Parse English mention patterns."""
        text = "Hey @xueqiu and @liuliu"
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        assert set(targets) == {"xueqiu", "liuliu"}
    
    def test_parse_mentions_xiaohuang_pattern(self) -> None:
        """Parse @小黄 mention."""
        text = "@小黄 please help"
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        assert targets == ["xiaohuang"]
    
    def test_parse_mentions_no_mentions(self) -> None:
        """Text without mentions should return empty list."""
        text = "Hello everyone, how are you?"
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        assert targets == []
    
    def test_parse_mentions_ignores_code_blocks(self) -> None:
        """Mentions inside code blocks should be ignored."""
        text = """
Here is some code:
```python
# @雪球 this is a comment
print("@六六")
```
@小黄 outside code block
"""
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        # Only @小黄 outside code block should be detected
        assert targets == ["xiaohuang"]
    
    def test_parse_mentions_ignores_inline_code(self) -> None:
        """Mentions inside inline code should be ignored."""
        text = "Use `@雪球` to mention xueqiu, but @六六 is real"
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        # Only @六六 outside inline code should be detected
        assert targets == ["liuliu"]
    
    def test_parse_mentions_alternate_patterns(self) -> None:
        """Parse alternate mention patterns like @雪纳瑞."""
        text = "@雪纳瑞 please help"
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        # @雪纳瑞 maps to xueqiu
        assert targets == ["xueqiu"]
    
    def test_parse_mentions_blue_parrot_pattern(self) -> None:
        """Parse @蓝鹦鹉 pattern for liuliu."""
        text = "@蓝鹦鹉 please review"
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        assert targets == ["liuliu"]
    
    def test_parse_mentions_yellow_parrot_pattern(self) -> None:
        """Parse @黄鹦鹉 pattern for xiaohuang."""
        text = "@黄鹦鹉 please design"
        
        targets = parse_a2a_mentions(text, current_animal="user")
        
        assert targets == ["xiaohuang"]


class TestGetAnimalNames:
    """Tests for get_animal_names function."""
    
    def test_get_animal_names_returns_mapping(self) -> None:
        """get_animal_names should return key to name mapping."""
        names = get_animal_names()
        
        assert names["xueqiu"] == "雪球"
        assert names["liuliu"] == "六六"
        assert names["xiaohuang"] == "小黄"


class TestGetAnimalPatterns:
    """Tests for get_animal_patterns function."""
    
    def test_get_animal_patterns_xueqiu(self) -> None:
        """Get patterns for xueqiu."""
        patterns = get_animal_patterns("xueqiu")
        
        assert "@雪球" in patterns
        assert "@xueqiu" in patterns
        assert "@雪纳瑞" in patterns
    
    def test_get_animal_patterns_liuliu(self) -> None:
        """Get patterns for liuliu."""
        patterns = get_animal_patterns("liuliu")
        
        assert "@六六" in patterns
        assert "@liuliu" in patterns
        assert "@蓝鹦鹉" in patterns
    
    def test_get_animal_patterns_xiaohuang(self) -> None:
        """Get patterns for xiaohuang."""
        patterns = get_animal_patterns("xiaohuang")
        
        assert "@小黄" in patterns
        assert "@xiaohuang" in patterns
        assert "@黄鹦鹉" in patterns
    
    def test_get_animal_patterns_unknown(self) -> None:
        """Get patterns for unknown animal should return empty list."""
        patterns = get_animal_patterns("unknown_animal")
        
        assert patterns == []


class TestAnimalConfigs:
    """Tests for ANIMAL_CONFIGS and PATTERN_TO_ANIMAL mappings."""
    
    def test_animal_configs_has_all_animals(self) -> None:
        """ANIMAL_CONFIGS should have all three animals."""
        assert "xueqiu" in ANIMAL_CONFIGS
        assert "liuliu" in ANIMAL_CONFIGS
        assert "xiaohuang" in ANIMAL_CONFIGS
    
    def test_pattern_to_animal_mapping(self) -> None:
        """PATTERN_TO_ANIMAL should map all patterns correctly."""
        assert PATTERN_TO_ANIMAL["@雪球"] == "xueqiu"
        assert PATTERN_TO_ANIMAL["@xueqiu"] == "xueqiu"
        assert PATTERN_TO_ANIMAL["@六六"] == "liuliu"
        assert PATTERN_TO_ANIMAL["@liuliu"] == "liuliu"
        assert PATTERN_TO_ANIMAL["@小黄"] == "xiaohuang"
        assert PATTERN_TO_ANIMAL["@xiaohuang"] == "xiaohuang"
    
    def test_all_patterns_mapped(self) -> None:
        """All patterns in ANIMAL_CONFIGS should be in PATTERN_TO_ANIMAL."""
        for animal_key, config in ANIMAL_CONFIGS.items():
            for pattern in config["patterns"]:
                assert pattern in PATTERN_TO_ANIMAL
                assert PATTERN_TO_ANIMAL[pattern] == animal_key