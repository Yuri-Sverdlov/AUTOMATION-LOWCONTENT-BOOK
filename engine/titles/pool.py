"""
pool.py — Сборщик пула кандидатов (этап 2 конвейера названий).

Запускает N шутников на M наборах крючков и собирает все варианты в
структурированный пул для передачи арбитрам.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Optional

import yaml

# Добавляем корень проекта в sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from engine.titles.generator import generate_titles, load_niche, build_generation_prompt


def build_pool(
    hook_sets: list[list[str]],
    roles: list[str],
    niche: dict,
    n: int,
    config_path: Optional[str] = None,
    generator_fn: Optional[Callable] = None
) -> dict:
    """
    Построить пул кандидатов: hook_sets × roles → candidates.

    Args:
        hook_sets: Список наборов крючков, каждый набор = list[str]
        roles: Список ролей генераторов (например, ["joker_1", "joker_2", "joker_3"])
        niche: Словарь с данными ниши (из load_niche)
        n: Количество названий на один вызов генератора
        config_path: Путь к config/models.yaml (опционально)
        generator_fn: Функция генерации (по умолчанию generate_titles).
                     Для тестов можно подсунуть фейковый генератор.

    Returns:
        Словарь с пулом кандидатов:
        {
            "niche": str,
            "n_per_role": int,
            "roles": list[str],
            "hook_sets": list[list[str]],
            "candidates": [
                {"id": "s1-joker_1-1", "title": "...", "author_role": "joker_1",
                 "hook_set_index": 1, "hooks": ["..."]},
                ...
            ]
        }
    """
    if generator_fn is None:
        generator_fn = generate_titles

    candidates = []

    for set_index, hooks in enumerate(hook_sets, start=1):
        for role in roles:
            # Генерируем названия для этого набора крючков × роль
            try:
                titles = generator_fn(
                    role=role,
                    hooks=hooks,
                    niche=niche,
                    n=n,
                    config_path=config_path
                )
            except Exception as e:
                # При ошибке генерации продолжаем, но логируем
                print(f"[WARNING] Error generating for set {set_index}, role {role}: {e}",
                      file=sys.stderr)
                titles = []

            # Добавляем каждое название как кандидата
            for title_index, title in enumerate(titles, start=1):
                candidate = {
                    "id": f"s{set_index}-{role}-{title_index}",
                    "title": title,
                    "author_role": role,
                    "hook_set_index": set_index,
                    "hooks": hooks
                }
                candidates.append(candidate)

    # Формируем результат
    result = {
        "niche": niche.get("niche", ""),
        "n_per_role": n,
        "roles": roles,
        "hook_sets": hook_sets,
        "candidates": candidates
    }

    return result


def load_hooks_file(hooks_file_path: str) -> list[list[str]]:
    """
    Загрузить наборы крючков из YAML файла.

    Args:
        hooks_file_path: Путь к файлу с hook_sets

    Returns:
        Список наборов крючков
    """
    hooks_file = Path(hooks_file_path)
    if not hooks_file.exists():
        raise FileNotFoundError(f"Hooks file not found: {hooks_file_path}")

    with open(hooks_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if "hook_sets" not in data:
        raise ValueError(f"Invalid hooks file format: missing 'hook_sets' key")

    return data["hook_sets"]


def main():
    """CLI для сборщика пула."""
    parser = argparse.ArgumentParser(
        description="Сборщик пула кандидатов (этап 2 конвейера названий)"
    )
    parser.add_argument(
        "--niche",
        required=True,
        help="Путь к niche.yaml"
    )
    parser.add_argument(
        "--hooks-file",
        required=True,
        help="Путь к YAML файлу с наборами крючков (hook_sets)"
    )
    parser.add_argument(
        "--roles",
        nargs="+",
        default=["joker_1", "joker_2", "joker_3"],
        help="Список ролей генераторов (по умолчанию: joker_1 joker_2 joker_3)"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=6,
        help="Количество названий на один вызов генератора (по умолчанию: 6)"
    )
    parser.add_argument(
        "--out",
        help="Путь к выходному JSON файлу (по умолчанию: stdout)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Офлайн режим: показать план и промпт первого набора без вызова API"
    )
    parser.add_argument(
        "--config",
        help="Путь к config/models.yaml (опционально)"
    )

    args = parser.parse_args()

    # Загружаем нишу и крючки
    try:
        niche = load_niche(args.niche)
        hook_sets = load_hooks_file(args.hooks_file)
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки файлов: {e}", file=sys.stderr)
        sys.exit(1)

    # Dry-run режим
    if args.dry_run:
        total_calls = len(hook_sets) * len(args.roles)
        total_titles = total_calls * args.n

        print("=" * 70)
        print("DRY-RUN MODE: План генерации (без вызова API)")
        print("=" * 70)
        print(f"\nНаборов крючков: {len(hook_sets)}")
        print(f"Ролей (шутников): {len(args.roles)} ({', '.join(args.roles)})")
        print(f"Названий на вызов: {args.n}")
        print(f"\nИтого вызовов API: {total_calls}")
        print(f"Ожидаемо названий (max): {total_titles}")
        print("\n" + "=" * 70)
        print("\nПромпт для первого набора x первой роли:")
        print("=" * 70)

        # Показываем промпт для первого набора и первой роли
        if hook_sets and args.roles:
            first_hooks = hook_sets[0]
            first_role = args.roles[0]

            # Загружаем персону
            persona_file = ROOT_DIR / "engine" / "titles" / "prompts" / f"{first_role}.md"
            if persona_file.exists():
                persona_system = persona_file.read_text(encoding="utf-8")
                system_prompt, user_message = build_generation_prompt(
                    persona_system, first_hooks, niche, args.n
                )

                print(f"\n[ROLE: {first_role}]")
                print(f"[HOOKS: {first_hooks}]")
                print("\n[SYSTEM PROMPT]")
                print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
                print("\n" + "-" * 70)
                print("\n[USER MESSAGE]")
                print(user_message)
            else:
                print(f"[WARNING] Файл персоны не найден: {persona_file}")

        print("\n" + "=" * 70)
        return

    # Живой режим: генерируем пул
    print(f"[INFO] Генерация пула: {len(hook_sets)} наборов x {len(args.roles)} ролей x {args.n} названий",
          file=sys.stderr)

    try:
        pool = build_pool(
            hook_sets=hook_sets,
            roles=args.roles,
            niche=niche,
            n=args.n,
            config_path=args.config
        )

        # Выводим результат
        output_json = json.dumps(pool, ensure_ascii=False, indent=2)

        if args.out:
            Path(args.out).write_text(output_json, encoding="utf-8")
            print(f"[INFO] Пул записан в {args.out}: {len(pool['candidates'])} кандидатов",
                  file=sys.stderr)
        else:
            print(output_json)

    except Exception as e:
        print(f"[ERROR] Ошибка при генерации пула: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
