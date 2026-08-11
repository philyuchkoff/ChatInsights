"""
Unit tests for common utilities (transliteration, safe filenames).
"""

from chatinsights.common import safe_filename_translit, transliterate


def test_transliterate_cyrillic():
    assert transliterate("Привет") == "Privet"
    assert transliterate("Съешь ещё этих мягких булок") == "Sesh eshchyo etikh myagkikh bulok"


def test_transliterate_mixed():
    assert transliterate("Привет World") == "Privet World"


def test_transliterate_empty():
    assert transliterate("") == ""


def test_safe_filename_translit_cyrillic():
    name = safe_filename_translit("Привет мир")
    assert name == "Privet_mir"


def test_safe_filename_translit_special_chars():
    name = safe_filename_translit("Test: файл*?")
    assert name == "Test_fayl"


def test_safe_filename_translit_long_title_truncated():
    long_title = "A" * 200
    assert len(safe_filename_translit(long_title)) == 120


def test_safe_filename_translit_untitled_fallback():
    assert safe_filename_translit("!!!") == "untitled"
    assert safe_filename_translit("") == "untitled"
