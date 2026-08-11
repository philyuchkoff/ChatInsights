"""
Common utilities for ChatInsights.
"""

import re

# transliteration for Cyrillic names
translit_map = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    "А": "A",
    "Б": "B",
    "В": "V",
    "Г": "G",
    "Д": "D",
    "Е": "E",
    "Ё": "Yo",
    "Ж": "Zh",
    "З": "Z",
    "И": "I",
    "Й": "Y",
    "К": "K",
    "Л": "L",
    "М": "M",
    "Н": "N",
    "О": "O",
    "П": "P",
    "Р": "R",
    "С": "S",
    "Т": "T",
    "У": "U",
    "Ф": "F",
    "Х": "Kh",
    "Ц": "Ts",
    "Ч": "Ch",
    "Ш": "Sh",
    "Щ": "Shch",
    "Ъ": "",
    "Ы": "Y",
    "Ь": "",
    "Э": "E",
    "Ю": "Yu",
    "Я": "Ya",
}


def transliterate(text):
    """Convert Cyrillic to Latin."""
    result = []
    for char in text:
        result.append(translit_map.get(char, char))
    return "".join(result)


def safe_filename_translit(title):
    """Convert title to safe ASCII filename."""
    # Сначала транслитерируем
    ascii_title = transliterate(title)
    # Затем заменяем все не-ASCII и проблемные символы
    safe = re.sub(r"[^a-zA-Z0-9_.\-]", "_", ascii_title)
    safe = re.sub(r"_+", "_", safe)  # схлопываем множественные подчеркивания
    safe = safe.strip("_.")
    if len(safe) > 120:
        safe = safe[:120]
    return safe if safe else "untitled"
