"""
Unit tests for training data generation and auxiliary operations.
"""

import os

from chatinsights.training import (
    _md_with_frontmatter,
    cleanup_empty_untitled_files,
    copy_conversations_to_obsidian,
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
        "January_2025": [
            {
                "title": "Test",
                "messages": [
                    {"author": "Me", "text": "A long enough instruction for the model here"},
                    {"author": "Bot", "text": "Response"},
                ],
            }
        ]
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


def test_md_with_frontmatter():
    content = "# Model: gpt-4o\n# Title: My Chat\n# Date: 2025-01-01 10:00:00\n\nBody text\n"
    md = _md_with_frontmatter(content)
    assert md.startswith("---\n")
    assert 'title: "My Chat"' in md
    assert 'model: "gpt-4o"' in md
    assert 'date: "2025-01-01 10:00:00"' in md
    assert md.rstrip().endswith("Body text")


def test_md_with_frontmatter_no_headers():
    content = "No headers here\n"
    assert _md_with_frontmatter(content) == content


def test_md_with_frontmatter_escapes_title():
    content = '# Title: Hello "World": Part 1\n# Model: claude\n\nBody\n'
    md = _md_with_frontmatter(content)
    assert 'title: "Hello \\"World\\": Part 1"' in md


def test_copy_conversations_to_obsidian_with_frontmatter(tmp_path):
    month_dir = os.path.join(str(tmp_path), "data", "January_2025")
    os.makedirs(month_dir)
    src = os.path.join(month_dir, "My_Chat_01_01_2025_10_00_00.txt")
    with open(src, "w", encoding="utf-8") as f:
        f.write("# Model: gpt-4o\n# Title: My Chat\n# Date: 2025-01-01 10:00:00\n\nHello world\n")

    obsidian_dir = os.path.join(str(tmp_path), "Obsidian", "Concepts")
    copy_conversations_to_obsidian(os.path.join(str(tmp_path), "data"), obsidian_dir)

    dest = os.path.join(obsidian_dir, "Conversations", "January_2025", "My_Chat_01_01_2025_10_00_00.md")
    assert os.path.exists(dest)
    with open(dest, encoding="utf-8") as f:
        content = f.read()
    assert content.startswith("---\n")
    assert 'title: "My Chat"' in content
    assert "Hello world" in content


def test_copy_conversations_to_obsidian_with_symlinks(tmp_path):
    month_dir = os.path.join(str(tmp_path), "data", "January_2025")
    os.makedirs(month_dir)
    src = os.path.join(month_dir, "My_Chat_01_01_2025_10_00_00.txt")
    with open(src, "w", encoding="utf-8") as f:
        f.write("# Model: gpt-4o\n# Title: My Chat\n\nHello world\n")

    obsidian_dir = os.path.join(str(tmp_path), "Obsidian", "Concepts")
    copy_conversations_to_obsidian(
        os.path.join(str(tmp_path), "data"), obsidian_dir, use_symlinks=True
    )

    dest = os.path.join(obsidian_dir, "Conversations", "January_2025", "My_Chat_01_01_2025_10_00_00.md")
    assert os.path.islink(dest)
    assert os.path.realpath(dest) == os.path.realpath(src)
    with open(dest, encoding="utf-8") as f:
        content = f.read()
    assert "Hello world" in content
    # No frontmatter in symlink mode
    assert not content.startswith("---")


def test_copy_conversations_to_obsidian_symlink_replaces_old_copy(tmp_path):
    month_dir = os.path.join(str(tmp_path), "data", "January_2025")
    os.makedirs(month_dir)
    src = os.path.join(month_dir, "My_Chat_01_01_2025_10_00_00.txt")
    with open(src, "w", encoding="utf-8") as f:
        f.write("Hello world\n")

    obsidian_dir = os.path.join(str(tmp_path), "Obsidian", "Concepts")

    # First run: plain copy
    copy_conversations_to_obsidian(os.path.join(str(tmp_path), "data"), obsidian_dir)
    dest = os.path.join(obsidian_dir, "Conversations", "January_2025", "My_Chat_01_01_2025_10_00_00.md")
    assert os.path.isfile(dest) and not os.path.islink(dest)

    # Second run: symlink mode replaces the existing copy
    copy_conversations_to_obsidian(
        os.path.join(str(tmp_path), "data"), obsidian_dir, use_symlinks=True
    )
    assert os.path.islink(dest)
    assert os.path.realpath(dest) == os.path.realpath(src)
