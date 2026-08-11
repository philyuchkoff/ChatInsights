"""
Unit tests for streaming JSON loading (io.py).
"""

import json
import os

import pytest

from chatinsights.io import (
    STREAM_THRESHOLD,
    ExportLoadError,
    backup_file,
    iter_conversations,
    load_json_file,
    use_streaming,
)


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


def test_load_json_file_missing():
    with pytest.raises(ExportLoadError):
        load_json_file("/nonexistent/path.json")


def test_load_json_file_empty(tmp_path):
    path = os.path.join(str(tmp_path), "empty.json")
    open(path, "w").close()
    with pytest.raises(ExportLoadError, match="empty"):
        load_json_file(path)


def test_load_json_file_invalid(tmp_path):
    path = os.path.join(str(tmp_path), "bad.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write("{not valid json")
    with pytest.raises(ExportLoadError, match="Invalid JSON"):
        load_json_file(path)


def test_load_json_file_utf8_bom(tmp_path):
    path = os.path.join(str(tmp_path), "bom.json")
    with open(path, "wb") as f:
        f.write(b"\xef\xbb\xbf" + json.dumps([{"title": "BOM"}]).encode("utf-8"))
    data = load_json_file(path)
    assert data[0]["title"] == "BOM"


def test_load_json_file_non_utf8(tmp_path):
    path = os.path.join(str(tmp_path), "latin.json")
    with open(path, "wb") as f:
        f.write(b"\xff\xfe\x00\x01\x02")
    with pytest.raises(ExportLoadError):
        load_json_file(path)


def test_load_json_file_valid(tmp_path, chatgpt_conversations):
    path = write_export(tmp_path, chatgpt_conversations)
    data = load_json_file(path)
    assert data == chatgpt_conversations


def test_backup_file_creates_bak(tmp_path):
    path = os.path.join(str(tmp_path), "config.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"key": "value"}')

    assert backup_file(path)
    bak = path + ".bak"
    assert os.path.exists(bak)
    with open(bak, encoding="utf-8") as f:
        assert f.read() == '{"key": "value"}'


def test_backup_file_custom_backup_path(tmp_path):
    path = os.path.join(str(tmp_path), "config.json")
    backup = os.path.join(str(tmp_path), "config.bak.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write("data")

    assert backup_file(path, backup_path=backup)
    assert os.path.exists(backup)


def test_backup_file_missing_source(tmp_path):
    assert not backup_file(os.path.join(str(tmp_path), "does_not_exist.json"))


def test_backup_file_overwrites_previous_backup(tmp_path):
    path = os.path.join(str(tmp_path), "config.json")
    bak = path + ".bak"
    with open(path, "w", encoding="utf-8") as f:
        f.write("new content")

    assert backup_file(path)
    with open(bak, encoding="utf-8") as f:
        assert f.read() == "new content"

    with open(path, "w", encoding="utf-8") as f:
        f.write("newer content")
    assert backup_file(path)
    with open(bak, encoding="utf-8") as f:
        assert f.read() == "newer content"
