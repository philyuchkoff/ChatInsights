"""
Unit tests for the Claude parser.
"""

from chatinsights.parsers.claude import get_claude_messages, process_claude_conversations


def test_get_messages_with_thinking_and_tools(claude_conversations, names):
    messages = get_claude_messages(claude_conversations[0], names)
    assert len(messages) == 4
    assert messages[0] == {"author": names["user"], "text": "Tell me about python"}
    assert messages[1]["author"] == f"{names['assistant']} (Thinking)"
    assert messages[1]["text"] == "Let me think about this"
    assert messages[2] == {"author": names["assistant"], "text": "Python is great"}
    assert messages[3]["author"] == f"{names['assistant']} (Tool Use)"


def test_get_messages_wrapped_dict(claude_conversations, names):
    messages = get_claude_messages(claude_conversations[0], names)
    assert any(m["text"] == "Python is great" for m in messages)


def test_get_messages_dict_chat_messages(names):
    conversation = {"chat_messages": {
        "0": {"sender": "human", "text": "hello"},
        "1": {"sender": "assistant", "text": "world"}
    }}
    messages = get_claude_messages(conversation, names)
    assert messages == [
        {"author": names["user"], "text": "hello"},
        {"author": names["assistant"], "text": "world"},
    ]


def test_get_messages_alternative_fields(names):
    conversation = {"messages": [{"sender": "human", "text": "hi"}]}
    messages = get_claude_messages(conversation, names)
    assert messages == [{"author": names["user"], "text": "hi"}]


def test_get_messages_empty(claude_conversations):
    conversation = dict(claude_conversations[0])
    conversation["chat_messages"] = []
    assert get_claude_messages(conversation) == []


def test_process_creates_files(claude_conversations, names, tmp_path):
    created, pruned = process_claude_conversations(claude_conversations, str(tmp_path), names)
    assert len(created) == 1
    content = file_content(created[0]["file"])
    assert "# Model: Claude" in content
    assert "# Title: Claude Test Chat" in content
    assert "## Conversation Summary" in content
    assert "Test summary" in content
    assert "(Thinking)" in content
    assert "Python is great" in content


def test_process_pruned_data(claude_conversations, names, tmp_path):
    _, pruned = process_claude_conversations(claude_conversations, str(tmp_path), names)
    assert "January_2025" in pruned
    entry = pruned["January_2025"][0]
    assert entry["model"] == "Claude"
    assert entry["summary"] == "Test summary"
    assert entry["create_time"] == "2025-01-01T12:00:00Z"


def test_process_wrapped_dict(claude_conversations, names, tmp_path):
    data = {"conversations": claude_conversations}
    created, _ = process_claude_conversations(data, str(tmp_path), names)
    assert len(created) == 1


def test_process_skips_bad_timestamp(names, tmp_path):
    data = [{"name": "Bad", "updated_at": "not-a-date", "chat_messages": []}]
    created, pruned = process_claude_conversations(data, str(tmp_path), names)
    assert created == []
    assert pruned == {}


def test_process_title_from_first_message(claude_conversations, names, tmp_path):
    data = [dict(claude_conversations[0])]
    data[0]["name"] = ""
    created, _ = process_claude_conversations(data, str(tmp_path), names)
    content = file_content(created[0]["file"])
    assert "Tell me about python" in content


def file_content(path):
    with open(path, encoding="utf-8") as f:
        return f.read()
