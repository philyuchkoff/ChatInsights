"""
Tests for the command-line interface.
"""

import os

from chatinsights.cli import build_parser, run


def _args(file_path, tmp_path, **overrides):
    defaults = {
        "file": file_path,
        "platform": "auto",
        "output": str(tmp_path),
        "user_name": "User",
        "assistant_name": "Assistant",
        "system_name": "System",
        "no_training": False,
        "no_concepts": False,
        "symlink_conversations": False,
        "min_length": 10,
        "verbose": False,
    }
    defaults.update(overrides)
    return argparse_namespace(defaults)


def argparse_namespace(d):
    return type("Args", (), d)()


def test_build_parser():
    parser = build_parser()
    args = parser.parse_args(["export.json", "--platform", "deepseek", "--no-training", "--symlink-conversations"])
    assert args.file == "export.json"
    assert args.platform == "deepseek"
    assert args.no_training
    assert args.symlink_conversations


def test_run_missing_file(tmp_path):
    code = run(_args("/nonexistent.json", tmp_path))
    assert code == 2


def test_run_no_file_arg(tmp_path):
    code = run(_args(None, tmp_path))
    assert code == 2


def test_run_full_pipeline_chatgpt(chatgpt_conversations, names, tmp_path, caplog):
    import json

    export = os.path.join(str(tmp_path), "export.json")
    with open(export, "w", encoding="utf-8") as f:
        json.dump(chatgpt_conversations, f)

    code = run(_args(export, tmp_path))
    assert code == 0

    data_dir = os.path.join(str(tmp_path), "data")
    assert os.path.exists(os.path.join(data_dir, "pruned.json"))
    assert os.path.exists(os.path.join(data_dir, "training_data.jsonl"))
    assert os.path.exists(os.path.join(data_dir, "conversation_titles.txt"))

    obsidian_dir = os.path.join(str(tmp_path), "Obsidian", "Concepts")
    assert os.path.exists(os.path.join(obsidian_dir, "Concepts-MOC.md"))
    assert os.path.exists(os.path.join(obsidian_dir, "Concept-Dashboard.md"))


def test_run_with_symlink_conversations(chatgpt_conversations, tmp_path):
    import json

    export = os.path.join(str(tmp_path), "export.json")
    with open(export, "w", encoding="utf-8") as f:
        json.dump(chatgpt_conversations, f)

    code = run(_args(export, tmp_path, symlink_conversations=True))
    assert code == 0

    data_dir = os.path.join(str(tmp_path), "data")
    obsidian_convos = os.path.join(str(tmp_path), "Obsidian", "Concepts", "Conversations")
    assert os.path.isdir(obsidian_convos)

    linked = [
        os.path.join(root, name)
        for root, _, files in os.walk(obsidian_convos)
        for name in files
        if name.endswith(".md")
    ]
    assert linked, "Expected at least one linked conversation file"
    for link in linked:
        assert os.path.islink(link)
        assert os.path.isfile(link)
        assert os.path.realpath(link).startswith(os.path.realpath(data_dir))


def test_run_skips_training_and_concepts(chatgpt_conversations, tmp_path):
    import json

    export = os.path.join(str(tmp_path), "export.json")
    with open(export, "w", encoding="utf-8") as f:
        json.dump(chatgpt_conversations, f)

    code = run(_args(export, tmp_path, no_training=True, no_concepts=True))
    assert code == 0

    data_dir = os.path.join(str(tmp_path), "data")
    assert not os.path.exists(os.path.join(data_dir, "training_data.jsonl"))
    assert not os.path.exists(os.path.join(tmp_path, "Obsidian"))


def test_run_invalid_json(tmp_path):
    export = os.path.join(str(tmp_path), "bad.json")
    with open(export, "w", encoding="utf-8") as f:
        f.write("{broken")

    code = run(_args(export, tmp_path))
    assert code == 1


def test_run_unknown_platform(tmp_path):
    export = os.path.join(str(tmp_path), "unknown.json")
    with open(export, "w", encoding="utf-8") as f:
        f.write('[{"something": "else"}]')

    code = run(_args(export, tmp_path))
    assert code == 1
