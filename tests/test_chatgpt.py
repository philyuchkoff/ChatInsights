"""
Unit tests for the ChatGPT parser.
"""

from chatinsights.parsers.chatgpt import (
    get_chatgpt_messages,
    get_chatgpt_model_slug,
    process_chatgpt_conversations,
)


def test_get_messages_reversed_order(chatgpt_conversations, names):
    messages = get_chatgpt_messages(chatgpt_conversations[0], names)
    assert len(messages) == 2
    assert messages[0]["author"] == names["user"]
    assert messages[0]["text"] == "Hello, test message here"
    assert messages[1]["author"] == names["assistant"]
    assert messages[1]["text"] == "Hi there!"


def test_get_messages_custom_names(chatgpt_conversations):
    custom = {"user": "Me", "assistant": "Bot", "system": "Sys"}
    messages = get_chatgpt_messages(chatgpt_conversations[0], custom)
    assert messages[0]["author"] == "Me"
    assert messages[1]["author"] == "Bot"


def test_get_model_slug(chatgpt_conversations):
    assert get_chatgpt_model_slug(chatgpt_conversations[0]) == "gpt-4o"


def test_get_model_slug_fallback(chatgpt_conversations):
    conv = dict(chatgpt_conversations[0])
    conv["mapping"] = {"a": {"message": {"author": {"role": "user"}}}}
    assert get_chatgpt_model_slug(conv) == "ChatGPT"


def test_process_creates_files(chatgpt_conversations, names, tmp_path):
    created, pruned = process_chatgpt_conversations(chatgpt_conversations, str(tmp_path), names)
    assert len(created) == 1
    file = created[0]["file"]
    assert file.endswith(".txt")
    content = file_content(file)
    assert "# Model: gpt-4o" in content
    assert "# Title: Hello World Testing" in content
    assert "Hello, test message here" in content
    assert "Hi there!" in content


def test_process_pruned_data(chatgpt_conversations, names, tmp_path):
    _, pruned = process_chatgpt_conversations(chatgpt_conversations, str(tmp_path), names)
    assert "November_2023" in pruned
    entry = pruned["November_2023"][0]
    assert entry["model"] == "gpt-4o"
    assert entry["title"] == "Hello World Testing"
    assert len(entry["messages"]) == 2


def test_process_skips_missing_timestamp(names, tmp_path):
    data = [{"title": "No time", "mapping": {}}]
    created, pruned = process_chatgpt_conversations(data, str(tmp_path), names)
    assert created == []
    assert pruned == {}


def test_process_cyrillic_filename_preserved(chatgpt_conversations, names, tmp_path):
    data = [dict(chatgpt_conversations[0])]
    data[0]["title"] = "Привет мир"
    data[0]["update_time"] = 1700000100
    data[0]["create_time"] = 1700000000
    created, _ = process_chatgpt_conversations(data, str(tmp_path), names)
    filename = created[0]["file"]
    assert "Привет_мир" in filename


def file_content(path):
    with open(path, encoding="utf-8") as f:
        return f.read()
