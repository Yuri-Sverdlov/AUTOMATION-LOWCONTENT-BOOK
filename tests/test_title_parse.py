"""
test_title_parse.py — Тесты для парсера названий.

Проверяет функцию parse_titles на различных входах:
- Чистый JSON массив
- JSON массив внутри ```json``` фенса
- JSON массив после вводного текста
- Мусорный вход (не должен ронять процесс)
"""

import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from engine.titles.generator import parse_titles


def test_clean_json_array():
    """Тест 1: Чистый JSON-массив."""
    input_text = '["Title One", "Title Two", "Title Three"]'
    result = parse_titles(input_text)

    assert isinstance(result, list)
    assert len(result) == 3
    assert "Title One" in result
    assert "Title Two" in result
    assert "Title Three" in result


def test_json_in_code_fence():
    """Тест 2: JSON массив внутри ```json``` фенса."""
    input_text = """```json
["First Title", "Second Title", "Third Title", "Fourth Title"]
```"""
    result = parse_titles(input_text)

    assert isinstance(result, list)
    assert len(result) == 4
    assert "First Title" in result
    assert "Fourth Title" in result


def test_json_after_intro_text():
    """Тест 3: JSON массив после вводного текста."""
    input_text = """Here are some great titles for your notebook:

["Awesome Title", "Another Great Title", "Final Title"]

I hope these help!"""
    result = parse_titles(input_text)

    assert isinstance(result, list)
    assert len(result) == 3
    assert "Awesome Title" in result
    assert "Another Great Title" in result


def test_garbage_input():
    """Тест 4: Мусорный вход (не должен ронять процесс)."""
    garbage_inputs = [
        "",  # Пустая строка
        "random text without json",  # Текст без JSON
        "[unclosed array",  # Неправильный JSON
        "```\nno json here\n```",  # Фенс без JSON
        "12345",  # Числа
        "[1, 2, 3]",  # Массив чисел, не строк
    ]

    for garbage in garbage_inputs:
        result = parse_titles(garbage)
        # Не должно быть исключений, результат - список (может быть пустым)
        assert isinstance(result, list)


def test_deduplication():
    """Тест 5: Проверка дедупликации (регистронезависимо)."""
    input_text = '["Title One", "Title Two", "TITLE ONE", "title two", "Title Three"]'
    result = parse_titles(input_text)

    assert isinstance(result, list)
    # Должно остаться 3 уникальных (регистронезависимо)
    assert len(result) == 3


def test_whitespace_trimming():
    """Тест 6: Проверка обрезки пробелов."""
    input_text = '[" Title One ", "  Title Two  ", "Title Three"]'
    result = parse_titles(input_text)

    assert isinstance(result, list)
    assert len(result) == 3
    # Все пробелы должны быть обрезаны
    assert "Title One" in result
    assert "Title Two" in result
    assert " Title One " not in result


if __name__ == "__main__":
    # Простой запуск без pytest (для проверки)
    test_clean_json_array()
    test_json_in_code_fence()
    test_json_after_intro_text()
    test_garbage_input()
    test_deduplication()
    test_whitespace_trimming()
    print("All tests passed!")
