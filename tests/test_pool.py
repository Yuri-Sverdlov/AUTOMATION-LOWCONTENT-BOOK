"""
test_pool.py — Тесты для сборщика пула (engine.titles.pool).

Используем fake генератор вместо реальных вызовов LLM.
"""

import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from engine.titles.pool import build_pool


def fake_generator(role, hooks, niche, n, config_path=None):
    """Фейковый генератор для тестов — возвращает предсказуемые названия."""
    return [f"Title-{role}-hook{i+1}" for i in range(n)]


def test_build_pool_structure():
    """Тест: структура выходного пула соответствует спецификации."""
    hook_sets = [
        ["hook1", "hook2"],
        ["hook3", "hook4"]
    ]
    roles = ["joker_1", "joker_2"]
    niche = {"niche": "test_niche"}
    n = 3

    pool = build_pool(
        hook_sets=hook_sets,
        roles=roles,
        niche=niche,
        n=n,
        generator_fn=fake_generator
    )

    # Проверяем обязательные ключи
    assert "niche" in pool
    assert "n_per_role" in pool
    assert "roles" in pool
    assert "hook_sets" in pool
    assert "candidates" in pool

    # Проверяем значения
    assert pool["niche"] == "test_niche"
    assert pool["n_per_role"] == 3
    assert pool["roles"] == roles
    assert pool["hook_sets"] == hook_sets

    # Проверяем количество кандидатов: 2 набора × 2 роли × 3 названия = 12
    assert len(pool["candidates"]) == 12


def test_candidate_structure():
    """Тест: каждый кандидат имеет правильную структуру."""
    hook_sets = [["hook1"]]
    roles = ["joker_1"]
    niche = {"niche": "test"}
    n = 2

    pool = build_pool(
        hook_sets=hook_sets,
        roles=roles,
        niche=niche,
        n=n,
        generator_fn=fake_generator
    )

    # Проверяем первого кандидата
    candidate = pool["candidates"][0]

    assert "id" in candidate
    assert "title" in candidate
    assert "author_role" in candidate
    assert "hook_set_index" in candidate
    assert "hooks" in candidate

    # Проверяем значения
    assert candidate["id"] == "s1-joker_1-1"
    assert candidate["title"] == "Title-joker_1-hook1"
    assert candidate["author_role"] == "joker_1"
    assert candidate["hook_set_index"] == 1
    assert candidate["hooks"] == ["hook1"]


def test_candidate_ids():
    """Тест: ID кандидатов имеют правильный формат s{set}-{role}-{index}."""
    hook_sets = [["h1"], ["h2"]]
    roles = ["joker_1", "joker_2"]
    niche = {"niche": "test"}
    n = 2

    pool = build_pool(
        hook_sets=hook_sets,
        roles=roles,
        niche=niche,
        n=n,
        generator_fn=fake_generator
    )

    candidates = pool["candidates"]

    # Проверяем формат ID для разных комбинаций
    expected_ids = [
        "s1-joker_1-1", "s1-joker_1-2",  # набор 1 × joker_1
        "s1-joker_2-1", "s1-joker_2-2",  # набор 1 × joker_2
        "s2-joker_1-1", "s2-joker_1-2",  # набор 2 × joker_1
        "s2-joker_2-1", "s2-joker_2-2",  # набор 2 × joker_2
    ]

    actual_ids = [c["id"] for c in candidates]
    assert actual_ids == expected_ids


def test_empty_hook_sets():
    """Тест: пустой список наборов крючков → пустой список кандидатов."""
    hook_sets = []
    roles = ["joker_1"]
    niche = {"niche": "test"}
    n = 5

    pool = build_pool(
        hook_sets=hook_sets,
        roles=roles,
        niche=niche,
        n=n,
        generator_fn=fake_generator
    )

    assert len(pool["candidates"]) == 0


def test_empty_roles():
    """Тест: пустой список ролей → пустой список кандидатов."""
    hook_sets = [["hook1"]]
    roles = []
    niche = {"niche": "test"}
    n = 5

    pool = build_pool(
        hook_sets=hook_sets,
        roles=roles,
        niche=niche,
        n=n,
        generator_fn=fake_generator
    )

    assert len(pool["candidates"]) == 0


def test_generator_error_handling():
    """Тест: при ошибке генератора продолжаем работу, но пропускаем этот вызов."""
    def failing_generator(role, hooks, niche, n, config_path=None):
        if role == "joker_2":
            raise RuntimeError("Generator failed!")
        return [f"Title-{role}-{i}" for i in range(n)]

    hook_sets = [["hook1"]]
    roles = ["joker_1", "joker_2", "joker_3"]
    niche = {"niche": "test"}
    n = 2

    pool = build_pool(
        hook_sets=hook_sets,
        roles=roles,
        niche=niche,
        n=n,
        generator_fn=failing_generator
    )

    # joker_2 упал → только joker_1 и joker_3 дали результаты
    # 1 набор × 2 успешные роли × 2 названия = 4 кандидата
    assert len(pool["candidates"]) == 4

    # Проверяем, что joker_2 отсутствует
    roles_in_candidates = {c["author_role"] for c in pool["candidates"]}
    assert "joker_1" in roles_in_candidates
    assert "joker_3" in roles_in_candidates
    assert "joker_2" not in roles_in_candidates
