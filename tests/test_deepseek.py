"""
Unit tests for the Deepseek parser.
"""

from chatinsights.parsers.deepseek import (
    get_deepseek_messages,
    get_deepseek_model,
    process_deepseek_conversations,
)


def test_get_messages_with_fragments(deepseek_conversations, names):
    messages = get_deepseek_messages(deepseek_conversations[0], names)
    assert len(messages) == 3
    assert messages[0] == {"author": names["user"], "text": "What is AI?"}
    assert messages[1]["author"] == f"{names['assistant']} (Thinking)"
    assert messages[1]["text"] == "AI is complex"
    assert messages[2] == {"author": names["assistant"], "text": "AI stands for artificial intelligence"}


def test_get_messages_empty_mapping(names):
    assert get_deepseek_messages({"mapping": {}}, names) == []


def test_get_model(deepseek_conversations):
    assert get_deepseek_model(deepseek_conversations[0]) == "deepseek-chat"


def test_get_model_fallback(deepseek_conversations):
    conv = dict(deepseek_conversations[0])
    conv["mapping"] = {}
    assert get_deepseek_model(conv) == "Deepseek"


def test_process_creates_files(deepseek_conversations, names, tmp_path):
    created, pruned = process_deepseek_conversations(deepseek_conversations, str(tmp_path), names)
    assert len(created) == 1
    content = file_content(created[0]["file"])
    assert "# Model: deepseek-chat" in content
    assert "What is AI?" in content
    assert "AI is complex" in content
    assert "AI stands for artificial intelligence" in content


def test_process_pruned_data(deepseek_conversations, names, tmp_path):
    _, pruned = process_deepseek_conversations(deepseek_conversations, str(tmp_path), names)
    assert "January_2025" in pruned
    entry = pruned["January_2025"][0]
    assert entry["model"] == "deepseek-chat"
    assert len(entry["messages"]) == 3


def test_process_wrapped_dict(deepseek_conversations, names, tmp_path):
    data = {"conversations": deepseek_conversations}
    created, _ = process_deepseek_conversations(data, str(tmp_path), names)
    assert len(created) == 1


def test_process_title_from_first_user_message(deepseek_conversations, names, tmp_path):
    data = [dict(deepseek_conversations[0])]
    data[0]["title"] = ""
    created, _ = process_deepseek_conversations(data, str(tmp_path), names)
    content = file_content(created[0]["file"])
    assert "What is AI?" in content


def test_process_skips_bad_timestamp(names, tmp_path):
    data = [{"title": "Bad", "updated_at": "garbage", "mapping": {}}]
    created, pruned = process_deepseek_conversations(data, str(tmp_path), names)
    assert created == []
    assert pruned == {}


def file_content(path):
    with open(path, encoding="utf-8") as f:
        return f.read()
