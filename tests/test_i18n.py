"""Tests for the i18n module."""

import pytest

from chatinsights.i18n import SUPPORTED_LANGUAGES, TRANSLATIONS, I18n


def test_supported_languages():
    assert "en" in SUPPORTED_LANGUAGES
    assert "ru" in SUPPORTED_LANGUAGES


def test_default_language_is_english():
    i18n = I18n()
    assert i18n.lang == "en"


def test_unknown_language_falls_back_to_english():
    i18n = I18n("xx")
    assert i18n.lang == "en"


def test_set_lang_valid():
    i18n = I18n("en")
    i18n.set_lang("ru")
    assert i18n.lang == "ru"


def test_set_lang_invalid():
    i18n = I18n("ru")
    i18n.set_lang("xx")
    assert i18n.lang == "en"


def test_translation_exists_in_both_languages():
    for lang, strings in TRANSLATIONS.items():
        for key, value in strings.items():
            assert key and value, f"Empty key or value in {lang}: {key!r}={value!r}"


@pytest.mark.parametrize("key", ["tab.import", "import.process", "status.ready", "err.no_file", "dlg.error"])
def test_common_keys_translated(key):
    en = TRANSLATIONS["en"][key]
    ru = TRANSLATIONS["ru"][key]
    assert en
    assert ru
    assert en != ru


def test_format_placeholders_match():
    for key in TRANSLATIONS["en"]:
        if key in TRANSLATIONS["ru"]:
            import re

            en_placeholders = set(re.findall(r"\{(\w+)\}", TRANSLATIONS["en"][key]))
            ru_placeholders = set(re.findall(r"\{(\w+)\}", TRANSLATIONS["ru"][key]))
            assert (
                en_placeholders == ru_placeholders
            ), f"Placeholders differ for {key}: {en_placeholders} != {ru_placeholders}"


def test_tr_returns_key_for_missing_translation():
    i18n = I18n("en")
    assert i18n.tr("no.such.key") == "no.such.key"


def test_tr_formats_kwargs():
    i18n = I18n("en")
    assert i18n.tr("status.detected", platform="CHATGPT") == "Detected: CHATGPT"


def test_tr_missing_kwarg_returns_raw_text():
    i18n = I18n("en")
    assert i18n.tr("status.detected") == "Detected: {platform}"


def test_tr_russian():
    i18n = I18n("ru")
    assert i18n.tr("status.ready") == "Готово"
    assert i18n.tr("status.detected", platform="CHATGPT") == "Определено: CHATGPT"


def test_fallback_to_english_when_key_missing_in_selected_language():
    translations = dict(TRANSLATIONS["en"])
    translations.pop("tab.settings")
    i18n = I18n("en")
    text = i18n.tr("tab.settings")
    assert text == "Settings"


def test_supported_languages_mapping():
    i18n = I18n("en")
    langs = i18n.supported_languages()
    assert "en" in langs
    assert "ru" in langs
