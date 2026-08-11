"""
Unit tests for streaming JSON loading (io.py).
"""

import json
import os

from chatinsights.io import STREAM_THRESHOLD, iter_conversations, use_streaming


def write_export(tmp_path, data, name="export.json"):
    path = os.path.join(str(tmp_path), name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def test_iter_array_export(tmp_path, chatgpt_conversations):
    path = write_export(tmp_path, chatgpt_conversations)
    items = list(iter_conversations(path))
    assert len(items) == 1
    assert items[0]["title"] == "Hello World Testing"


def test_iter_wrapped_export(tmp_path, chatgpt_conversations):
    path = write_export(tmp_path, {"conversations": chatgpt_conversations})
    items = list(iter_conversations(path))
    assert len(items) == 1
    assert items[0]["title"] == "Hello World Testing"


def test_iter_empty_array(tmp_path):
    path = write_export(tmp_path, [])
    assert list(iter_conversations(path)) == []


def test_iter_single_dict(tmp_path):
    path = write_export(tmp_path, {"title": "Solo", "mapping": {}})
    items = list(iter_conversations(path))
    assert len(items) == 1
    assert items[0]["title"] == "Solo"


def test_iter_many_conversations(tmp_path, chatgpt_conversations):
    data = chatgpt_conversations * 100
    path = write_export(tmp_path, data)
    items = list(iter_conversations(path))
    assert len(items) == 100


def test_use_streaming_small_file(tmp_path, chatgpt_conversations):
    path = write_export(tmp_path, chatgpt_conversations)
    assert not use_streaming(path)


def test_use_streaming_large_file(tmp_path):
    path = os.path.join(str(tmp_path), "big.json")
    with open(path, "wb") as f:
        f.write(b"x" * (STREAM_THRESHOLD + 1))
    assert use_streaming(path)


def test_use_streaming_missing_file():
    assert not use_streaming("/nonexistent/path.json")
