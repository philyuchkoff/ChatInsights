"""
Shared pytest fixtures with sample exports for all three platforms.
"""

import pytest

NAMES = {"user": "User", "assistant": "Assistant", "system": "System"}


@pytest.fixture
def names():
    return dict(NAMES)


@pytest.fixture
def chatgpt_conversations():
    return [{
        "title": "Hello World Testing",
        "create_time": 1700000000,
        "update_time": 1700000100,
        "current_node": "b",
        "mapping": {
            "a": {"parent": None, "message": {"author": {"role": "user"},
                   "content": {"content_type": "text", "parts": ["Hello, test message here"]}}},
            "b": {"parent": "a", "message": {"author": {"role": "assistant"},
                   "content": {"content_type": "text", "parts": ["Hi there!"]},
                   "metadata": {"model_slug": "gpt-4o"}}}
        }
    }]


@pytest.fixture
def claude_conversations():
    return [{
        "name": "Claude Test Chat",
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-01T12:05:00Z",
        "summary": "Test summary",
        "chat_messages": [
            {"sender": "human", "content": [{"type": "text", "text": "Tell me about python"}]},
            {"sender": "assistant", "content": [
                {"type": "thinking", "thinking": "Let me think about this"},
                {"type": "text", "text": "Python is great"},
                {"type": "tool_use", "name": "web_search", "input": {"q": "python"}}
            ]}
        ]
    }]


@pytest.fixture
def deepseek_conversations():
    return [{
        "title": "Deepseek Test",
        "updated_at": "2025-01-02T10:00:00+00:00",
        "inserted_at": "2025-01-02T10:00:00+00:00",
        "mapping": {
            "1": {"id": "1", "parent": None, "message": {"model": "deepseek-chat",
                   "inserted_at": "2025-01-02T10:00:00",
                   "fragments": [{"type": "REQUEST", "content": "What is AI?"}]}},
            "2": {"id": "2", "parent": "1", "message": {"model": "deepseek-chat",
                   "inserted_at": "2025-01-02T10:00:05",
                   "fragments": [{"type": "THINK", "content": "AI is complex"},
                                 {"type": "RESPONSE", "content": "AI stands for artificial intelligence"}]}}
        }
    }]


@pytest.fixture
def wrapped_exports(chatgpt_conversations):
    """Exports wrapped in a top-level dict (Claude app export format)."""
    return {"conversations": chatgpt_conversations}
