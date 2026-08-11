"""
Streaming JSON helpers for processing large exports without loading them fully
into memory. Uses the optional `ijson` library when available and falls back
to a regular json.load otherwise.
"""

import json
import os

STREAM_THRESHOLD = 50 * 1024 * 1024  # 50 MB


def use_streaming(file_path):
    """Return True if the export file is large enough to warrant streaming."""
    try:
        return os.path.getsize(file_path) > STREAM_THRESHOLD
    except OSError:
        return False


def iter_conversations(file_path):
    """Yield conversation objects one at a time from an export file.

    Supports both top-level arrays and {'conversations': [...]} wrappers.
    Uses ijson streaming when installed, otherwise falls back to json.load.
    """
    try:
        import ijson
    except ImportError:
        yield from _iter_with_json_load(file_path)
        return

    with open(file_path, 'rb') as f:
        structure = _detect_top_level(f)
        f.seek(0)
        if structure == 'array':
            yield from ijson.items(f, 'item')
        elif structure == 'conversations':
            yield from ijson.items(f, 'conversations.item')
        else:
            # Unknown structure: fall back to full load
            yield from _iter_with_json_load(file_path)


def _detect_top_level(f):
    """Peek at the JSON structure without loading it: 'array', 'conversations' or None."""
    import ijson

    events = iter(ijson.parse(f))
    for event, value, _ in events:
        if event == 'start_array':
            return 'array'
        if event == 'start_map':
            # Look for a 'conversations' key before the first nested value
            for e2, v2 in events:
                if e2 == 'map_key' and v2 == 'conversations':
                    return 'conversations'
                if e2 in ('start_array', 'start_map'):
                    return None
            return None
    return None


def _iter_with_json_load(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'conversations' in data:
        data = data['conversations']
    if isinstance(data, list):
        yield from data
    else:
        yield data
