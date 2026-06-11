"""
generator.py — Генератор названий-крючков (building block 1).

Использует LLMClient для вызова API и генерации списка названий на основе
крючков и паспорта ниши.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

import yaml

# Добавляем корень проекта в sys.path для импорта reusable модулей
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from reusable.python.llm_client import LLMClient


def load_niche(niche_path: str) -> dict:
    """
    Загрузить паспорт ниши из niche.yaml.

    Args:
        niche_path: Путь к файлу niche.yaml

    Returns:
        Словарь с полями: niche, audience, interior_type, interior_style,
        format, title_formula
    """
    niche_file = Path(niche_path)
    if not niche_file.exists():
        raise FileNotFoundError(f"Niche file not found: {niche_path}")

    with open(niche_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return {
        "niche": data.get("niche", ""),
        "audience": data.get("audience", ""),
        "interior_type": data.get("interior_type", ""),
        "interior_style": data.get("interior_style", ""),
        "format": data.get("format", ""),
        "title_formula": data.get("title_formula", ""),
    }


def build_generation_prompt(
    persona_system: str,
    hooks: list[str],
    niche: dict,
    n: int
) -> tuple[str, str]:
    """
    Построить промпты для генерации названий (чистая функция).

    Args:
        persona_system: System prompt персоны (из файла промпта)
        hooks: Список крючков-фраз
        niche: Словарь с данными ниши
        n: Количество названий для генерации

    Returns:
        Кортеж (system_prompt, user_message)
    """
    system_prompt = persona_system.strip()

    # Форматируем крючки как список
    hooks_text = "\n".join(f"{i+1}. \"{hook}\"" for i, hook in enumerate(hooks))

    # Формируем user_message с явным указанием всех требований
    user_message = f"""Generate {n} compelling titles for a low-content book.

**Hooks (use at least one per title):**
{hooks_text}

**Target audience:** {niche.get('audience', 'general audience')}
**Product type:** {niche.get('interior_type', 'notebook')} ({niche.get('interior_style', '')})
**Format:** {niche.get('format', '')}
**Title formula hint:** {niche.get('title_formula', '{audience} + {type} + {hook}')}

**Requirements:**
- Generate exactly {n} unique titles
- Each title must incorporate at least one of the hooks above
- Titles should resonate with the target audience
- Keep titles concise (typically 3-7 words)
- Return ONLY a JSON array of {n} strings, no extra text or explanation

**Expected output format:**
["Title 1", "Title 2", "Title 3", ...]
"""

    return system_prompt, user_message


def parse_titles(raw_response: str) -> list[str]:
    """
    Разобрать ответ LLM и извлечь список названий (чистая функция).

    Устойчиво обрабатывает различные форматы:
    - Чистый JSON массив: ["title1", "title2"]
    - Массив внутри ```json``` фенса
    - Массив после вводного текста

    Args:
        raw_response: Сырой ответ от LLM

    Returns:
        Список уникальных непустых строк (без дублей)
    """
    text = raw_response.strip()
    if not text:
        return []

    # Убираем markdown code fence если есть
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text).strip()
        text = re.sub(r"\n?```$", "", text).strip()

    titles = []

    # Попытка 1: прямой парсинг всего текста как JSON
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, str):
                    title = item.strip()
                    if title:
                        titles.append(title)
            if titles:
                return _deduplicate_titles(titles)
    except json.JSONDecodeError:
        pass

    # Попытка 2: поиск JSON массива в тексте
    start = text.find("[")
    end = text.rfind("]")

    if start != -1 and end != -1 and end > start:
        json_fragment = text[start:end + 1]
        try:
            parsed = json.loads(json_fragment)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, str):
                        title = item.strip()
                        if title:
                            titles.append(title)
                if titles:
                    return _deduplicate_titles(titles)
        except json.JSONDecodeError:
            pass

    # Попытка 3: поиск строк в кавычках (fallback)
    pattern = r'"([^"]{3,100})"'
    matches = re.findall(pattern, text)
    for match in matches:
        title = match.strip()
        if title and len(title.split()) >= 2:  # Минимум 2 слова
            titles.append(title)

    if titles:
        return _deduplicate_titles(titles)

    # Если ничего не распарсилось, возвращаем пустой список
    return []


def _deduplicate_titles(titles: list[str]) -> list[str]:
    """Удалить точные дубликаты (регистронезависимо), сохранив порядок."""
    seen = set()
    result = []
    for title in titles:
        title_lower = title.lower()
        if title_lower not in seen:
            seen.add(title_lower)
            result.append(title)
    return result


def generate_titles(
    role: str,
    hooks: list[str],
    niche: dict,
    n: int,
    config_path: Optional[str] = None
) -> list[str]:
    """
    Сгенерировать список названий через LLM API.

    Args:
        role: Роль генератора (например, "joker_1")
        hooks: Список крючков-фраз
        niche: Словарь с данными ниши (из load_niche)
        n: Количество названий для генерации
        config_path: Путь к config/models.yaml (опционально)

    Returns:
        Список сгенерированных названий
    """
    # Загружаем персону из файла
    persona_file = ROOT_DIR / "engine" / "titles" / "prompts" / f"{role}.md"
    if not persona_file.exists():
        raise FileNotFoundError(f"Persona file not found: {persona_file}")

    persona_system = persona_file.read_text(encoding="utf-8")

    # Строим промпты
    system_prompt, user_message = build_generation_prompt(
        persona_system, hooks, niche, n
    )

    # Вызываем LLM
    client = LLMClient(role, config_path)
    raw_response = client.call(system_prompt, user_message)

    # Разбираем ответ
    titles = parse_titles(raw_response)

    return titles


def main():
    """CLI для генератора названий."""
    parser = argparse.ArgumentParser(
        description="Генератор названий-крючков (building block 1)"
    )
    parser.add_argument(
        "--niche",
        required=True,
        help="Путь к niche.yaml"
    )
    parser.add_argument(
        "--hooks",
        nargs="+",
        required=True,
        help="Крючки-фразы (минимум один)"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=6,
        help="Количество названий для генерации (по умолчанию: 6)"
    )
    parser.add_argument(
        "--role",
        default="joker_1",
        help="Роль генератора (по умолчанию: joker_1)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Офлайн режим: показать промпт без вызова API"
    )
    parser.add_argument(
        "--out",
        help="Путь к выходному JSON файлу (по умолчанию: stdout)"
    )
    parser.add_argument(
        "--config",
        help="Путь к config/models.yaml (опционально)"
    )

    args = parser.parse_args()

    # Загружаем нишу
    try:
        niche = load_niche(args.niche)
    except Exception as e:
        print(f"[ERROR] Не удалось загрузить niche.yaml: {e}", file=sys.stderr)
        sys.exit(1)

    # Загружаем персону
    persona_file = ROOT_DIR / "engine" / "titles" / "prompts" / f"{args.role}.md"
    if not persona_file.exists():
        print(f"[ERROR] Файл персоны не найден: {persona_file}", file=sys.stderr)
        sys.exit(1)

    persona_system = persona_file.read_text(encoding="utf-8")

    # Строим промпты
    system_prompt, user_message = build_generation_prompt(
        persona_system, args.hooks, niche, args.n
    )

    # Dry-run режим
    if args.dry_run:
        print("=" * 70)
        print("DRY-RUN MODE: Промпт (без вызова API)")
        print("=" * 70)
        print("\n[SYSTEM PROMPT]")
        print(system_prompt)
        print("\n" + "=" * 70)
        print("\n[USER MESSAGE]")
        print(user_message)
        print("\n" + "=" * 70)
        return

    # Живой вызов API
    try:
        client = LLMClient(args.role, args.config)
        raw_response = client.call(system_prompt, user_message)

        # Проверяем, не вернулась ли ошибка
        if raw_response.startswith("[ERROR]"):
            print(f"[WARNING] {raw_response}", file=sys.stderr)
            print("[INFO] Шаг живого вызова пропущен (нет API-ключа или ошибка провайдера)", file=sys.stderr)

            # Формируем результат с пустым списком
            result = {
                "niche": niche.get("niche", ""),
                "hooks": args.hooks,
                "role": args.role,
                "n_requested": args.n,
                "titles": [],
                "error": raw_response
            }
        else:
            # Разбираем ответ
            titles = parse_titles(raw_response)

            # Формируем результат
            result = {
                "niche": niche.get("niche", ""),
                "hooks": args.hooks,
                "role": args.role,
                "n_requested": args.n,
                "titles": titles
            }

        # Выводим результат
        output_json = json.dumps(result, ensure_ascii=False, indent=2)

        if args.out:
            Path(args.out).write_text(output_json, encoding="utf-8")
            print(f"[INFO] Результат записан в {args.out}")
        else:
            print(output_json)

    except Exception as e:
        print(f"[ERROR] Ошибка при вызове API: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
