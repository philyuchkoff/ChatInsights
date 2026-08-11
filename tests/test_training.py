"""
Unit tests for training data generation and auxiliary operations.
"""

import os

from chatinsights.training import (
    cleanup_empty_untitled_files,
    create_training_pairs,
    generate_conversation_titles,
)

PRUNED = {
    "January_2025": [
        {
            "title": "Test",
            "messages": [
                {"author": "User", "text": "This is a sufficiently long instruction text"},
                {"author": "Assistant", "text": "And here is the response"},
                {"author": "User", "text": "Short"},
                {"author": "Assistant", "text": "Should be skipped"},
            ],
        }
    ]
}


def test_create_training_pairs_jsonl(names, tmp_path):
    out = os.path.join(str(tmp_path), "training.jsonl")
    pairs = create_training_pairs(PRUNED, out, names)
    assert len(pairs) == 1
    assert pairs[0]["instruction"] == "This is a sufficiently long instruction text"
    assert pairs[0]["response"] == "And here is the response"
    assert os.path.exists(out)
    with open(out, encoding="utf-8") as f:
        lines = f.read().strip().split("\n")
    assert len(lines) == 1


def test_create_training_pairs_csv(names, tmp_path):
    out = os.path.join(str(tmp_path), "training.csv")
    pairs = create_training_pairs(PRUNED, out, names)
    assert len(pairs) == 1
    with open(out, encoding="utf-8") as f:
        content = f.read()
    assert content.startswith("instruction,response")


def test_create_training_pairs_min_length(names, tmp_path):
    out = os.path.join(str(tmp_path), "training.jsonl")
    pairs = create_training_pairs(PRUNED, out, names, min_length=100)
    assert pairs == []


def test_create_training_pairs_custom_names(tmp_path):
    custom = {"user": "Me", "assistant": "Bot", "system": "Sys"}
    pruned = {
        "January_2025": [{
            "title": "Test",
            "messages": [
                {"author": "Me", "text": "A long enough instruction for the model here"},
                {"author": "Bot", "text": "Response"},
            ],
        }]
    }
    out = os.path.join(str(tmp_path), "training.jsonl")
    pairs = create_training_pairs(pruned, out, custom)
    assert len(pairs) == 1


def test_generate_conversation_titles(tmp_path):
    month_dir = os.path.join(str(tmp_path), "January_2025")
    os.makedirs(month_dir)
    open(os.path.join(month_dir, "convo_15_01_2025_10_00_00.txt"), "w").close()
    open(os.path.join(month_dir, "convo_01_01_2025_09_00_00.txt"), "w").close()

    titles_file = generate_conversation_titles(str(tmp_path))
    assert os.path.exists(titles_file)
    with open(titles_file, encoding="utf-8") as f:
        content = f.read()
    assert "---" in content  # YAML frontmatter header
    assert "convo_01_01_2025" in content
    assert "convo_15_01_2025" in content
    # Files must be sorted by date
    assert content.index("convo_01_01_2025") < content.index("convo_15_01_2025")


def test_cleanup_empty_untitled_files(tmp_path):
    month_dir = os.path.join(str(tmp_path), "January_2025")
    os.makedirs(month_dir)

    empty_untitled = os.path.join(month_dir, "untitled_01_01_2025_00_00_00.txt")
    open(empty_untitled, "w").close()

    normal = os.path.join(month_dir, "normal_01_01_2025_00_00_00.txt")
    with open(normal, "w") as f:
        f.write("content")

    non_empty_untitled = os.path.join(month_dir, "untitled_02_01_2025_00_00_00.txt")
    with open(non_empty_untitled, "w") as f:
        f.write("not empty")

    result = cleanup_empty_untitled_files(str(tmp_path))
    assert result["count"] == 1
    assert not os.path.exists(empty_untitled)
    assert os.path.exists(normal)
    assert os.path.exists(non_empty_untitled)


def test_cleanup_no_empty_files(tmp_path):
    month_dir = os.path.join(str(tmp_path), "January_2025")
    os.makedirs(month_dir)
    with open(os.path.join(month_dir, "normal.txt"), "w") as f:
        f.write("content")

    result = cleanup_empty_untitled_files(str(tmp_path))
    assert result["count"] == 0
    assert result["cleanup_dir"] is None
