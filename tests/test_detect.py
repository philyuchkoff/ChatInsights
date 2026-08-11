"""
Unit tests for platform detection.
"""

from chatinsights.parsers import detect_platform


def test_detect_chatgpt(chatgpt_conversations):
    assert detect_platform(chatgpt_conversations) == "chatgpt"


def test_detect_claude(claude_conversations):
    assert detect_platform(claude_conversations) == "claude"


def test_detect_deepseek(deepseek_conversations):
    assert detect_platform(deepseek_conversations) == "deepseek"


def test_detect_wrapped_dict(wrapped_exports):
    assert detect_platform(wrapped_exports) == "chatgpt"


def test_detect_unknown():
    assert detect_platform([]) == "unknown"
    assert detect_platform("not json") == "unknown"
    assert detect_platform([{"some": "other", "structure": True}]) == "unknown"


def test_detect_chatgpt_by_conversation_id():
    data = [{"conversation_id": "abc123", "mapping": {}}]
    assert detect_platform(data) == "chatgpt"


def test_detect_claude_by_uuid():
    data = [{"uuid": "uuid-123", "name": "Test"}]
    assert detect_platform(data) == "claude"


def test_detect_deepseek_vs_chatgpt_priority():
    """Mapping with fragments must be detected as Deepseek even without conversation_id."""
    data = [
        {"conversation_id": "x", "mapping": {"1": {"message": {"fragments": [{"type": "REQUEST", "content": "hi"}]}}}}
    ]
    assert detect_platform(data) == "deepseek"
