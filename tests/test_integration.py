"""
Integration tests: full pipeline (export -> logs -> training -> Obsidian) for each platform.
"""

import json
import os

from chatinsights.parsers import detect_platform
from chatinsights.parsers.chatgpt import process_chatgpt_conversations
from chatinsights.parsers.claude import process_claude_conversations
from chatinsights.parsers.deepseek import process_deepseek_conversations
from chatinsights.tracker import ConceptTracker
from chatinsights.training import (
    copy_conversations_to_obsidian,
    create_training_pairs,
    generate_conversation_titles,
)

EXPECTED_STRUCTURE = [
    "conversation_titles.txt",
    "pruned.json",
    "training_data.jsonl",
]


def run_pipeline(conversations, processor, platform, names, tmp_path):
    data_dir = os.path.join(str(tmp_path), "data")
    os.makedirs(data_dir, exist_ok=True)

    assert detect_platform(conversations) == platform

    created, pruned = processor(conversations, data_dir, names)
    assert len(created) > 0

    training_pairs = create_training_pairs(
        pruned, os.path.join(data_dir, "training_data.jsonl"), names
    )
    titles_file = generate_conversation_titles(data_dir)

    # Obsidian vault
    obsidian_dir = os.path.join(str(tmp_path), "Obsidian", "Concepts")
    os.makedirs(obsidian_dir, exist_ok=True)

    tracker = ConceptTracker()
    results = tracker.process(titles_file, obsidian_dir)
    assert results["conversations"] == len(conversations)

    copy_conversations_to_obsidian(data_dir, obsidian_dir)

    # Verify output structure
    assert os.path.exists(os.path.join(data_dir, "pruned.json"))
    assert os.path.exists(os.path.join(data_dir, "training_data.jsonl"))
    assert os.path.exists(os.path.join(data_dir, "conversation_titles.txt"))
    assert os.path.exists(os.path.join(obsidian_dir, "Concepts-MOC.md"))
    assert os.path.exists(os.path.join(obsidian_dir, "Concept-Dashboard.md"))
    assert os.path.exists(os.path.join(obsidian_dir, "Recurring-Terms.md"))

    # Conversations must be copied as .md (inside month subfolders)
    conversations_dir = os.path.join(obsidian_dir, "Conversations")
    assert os.path.isdir(conversations_dir)
    md_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(conversations_dir)
        for f in files
        if f.endswith(".md")
    ]
    assert len(md_files) == len(created)

    return created, pruned, training_pairs


def test_full_pipeline_chatgpt(chatgpt_conversations, names, tmp_path):
    created, pruned, pairs = run_pipeline(
        chatgpt_conversations, process_chatgpt_conversations, "chatgpt", names, tmp_path
    )
    # Verify model header and content
    with open(created[0]["file"], encoding="utf-8") as f:
        content = f.read()
    assert "# Model: gpt-4o" in content
    assert len(pairs) == 1


def test_full_pipeline_claude(claude_conversations, names, tmp_path):
    created, pruned, pairs = run_pipeline(
        claude_conversations, process_claude_conversations, "claude", names, tmp_path
    )
    with open(created[0]["file"], encoding="utf-8") as f:
        content = f.read()
    assert "## Conversation Summary" in content
    assert "(Thinking)" in content


def test_full_pipeline_deepseek(deepseek_conversations, names, tmp_path):
    created, pruned, pairs = run_pipeline(
        deepseek_conversations, process_deepseek_conversations, "deepseek", names, tmp_path
    )
    with open(created[0]["file"], encoding="utf-8") as f:
        content = f.read()
    assert "# Model: deepseek-chat" in content
    assert "(Thinking)" in content


def test_pruned_json_is_valid(chatgpt_conversations, names, tmp_path):
    data_dir = os.path.join(str(tmp_path), "data")
    os.makedirs(data_dir, exist_ok=True)
    _, pruned = process_chatgpt_conversations(chatgpt_conversations, data_dir, names)

    with open(os.path.join(data_dir, "pruned.json"), encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == pruned
