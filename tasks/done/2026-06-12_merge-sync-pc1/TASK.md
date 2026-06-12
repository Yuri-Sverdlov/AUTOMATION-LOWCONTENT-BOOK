# TASK: sync ПК1 ↔ GitHub — слияние работы двух компьютеров

**От:** архитектор → **кому:** кодер (терминал, Windows, ПК1)
**Дата:** 2026-06-11
**Тип:** обслуживание репозитория (merge + конфликты в доках)
**Git:** ⚠️ **ЯВНОЕ ИСКЛЮЧЕНИЕ** — в рамках ЭТОГО задания коммитить, мёрджить и пушить РАЗРЕШЕНО.

---

## Ситуация (прочитай, прежде чем делать)

- **Локально (ПК1):** стоим на `bbdf614`. НЕ закоммичено: приёмка чекпоинта s10
  (CONTEXT, PROJECT_LOG, архив `tasks/done/2026-06-11_git-checkpoint-s10/`,
  это задание + REPORT) и 2 backlog-файла, забытые в s10.
- **origin/main (работа с ПК2):** 3 коммита поверх `bbdf614`, HEAD = `436c563` —
  титульный конвейер (`engine/titles/`, `tests/`, `config/`, `QUICK_START.md`,
  backlog `2026-06_title-pipeline.md`, архивы приёмок).
- **Гарантированные конфликты:** `CONTEXT.md`, `PROJECT_LOG.md`, `tasks/TASK.md`,
  `tasks/REPORT.md` — менялись на обеих машинах.

Порядок принят: сначала закоммитить локальное (без push) → merge → разрешить
конфликты по правилам ниже → push.

> CRLF: `git status` шумит «modified» на куче файлов — истина через
> `git diff --ignore-all-space --stat`. Добавлять ТОЛЬКО перечисленные пути.

---

## Шаг 0 — префлайт
```bat
del .git\config.lock 2>NUL
del .git\index.lock  2>NUL
git rev-parse --abbrev-ref HEAD       :: main
git log --oneline -1                  :: bbdf614
git fetch origin
git log --oneline origin/main -1      :: 436c563
git push --dry-run origin main 2>&1   :: упадёт "non-fast-forward" — это ОЖИДАЕМО, не СТОП
```

## Шаг 1 — локальный коммит ПК1 (БЕЗ push)
```bat
git add CONTEXT.md PROJECT_LOG.md tasks/TASK.md tasks/REPORT.md tasks/done/2026-06-11_git-checkpoint-s10 tasks/backlog/2026-06_art-palette-STAGES.md tasks/backlog/2026-06_external-ideas-research.md
git status
git commit -m "docs: accept s10 checkpoint (archive) + 2 missed backlog files (PC1, pre-merge)"
```
Проверь по `git status`: добавилось ровно перечисленное, без генерёжки
(`output/`, `*.png`/`*.pdf`, `data/niches/*/output/`, `.claude/`, `tasks/image_test.png`).

## Шаг 2 — merge работы ПК2
```bat
git pull --no-rebase origin main
```
Ожидаем конфликты в 4 файлах. Правила разрешения:

| Файл | Правило |
|------|---------|
| `PROJECT_LOG.md` | **Оставить ОБЕ стороны.** Журнал append-only: записи обеих машин сохраняются полностью, упорядочить по дате — новые сверху. Ничего не удалять. |
| `CONTEXT.md` | **Объединить.** Секция «Ревизия проекта (2026-06-11, s10)» из ПК1 — сохранить. Изменения ПК2 (титульный конвейер и пр.) — сохранить. Абзац «Сейчас в tasks/TASK.md» — взять версию ПК1 (это sync-задание). Списки бэклога — объединить (все пункты обеих сторон, без дублей). |
| `tasks/TASK.md` | **Взять версию ПК1** (этот файл): `git checkout --ours tasks/TASK.md` |
| `tasks/REPORT.md` | **Взять версию ПК1** (заготовка «ожидает»): `git checkout --ours tasks/REPORT.md`. НО сначала проверь: текст REPORT с ПК2 (origin-версия) должен дублироваться в `tasks/done/2026-06-11_*/REPORT.md`. Если НЕ дублируется — СТОП, не теряем отчёт, сообщи архитектору. |

После правок:
```bat
git add CONTEXT.md PROJECT_LOG.md tasks/TASK.md tasks/REPORT.md
git status        :: конфликтов не осталось
git commit        :: стандартное merge-сообщение
```

## Шаг 3 — проверка после слияния
```bat
pip install -r requirements.txt
python -m py_compile engine/build_cover.py engine/cover_generator.py engine/cover_to_pdf.py engine/text_layout.py engine/layout_variants.py engine/interior_lined.py engine/titles/generator.py engine/titles/pool.py
python -m pytest tests/ -q
```
pytest должен быть зелёным (тесты приехали с ПК2). Если падает из-за отсутствия
API-ключей/сети — отметь в отчёте, какие именно тесты, НЕ СТОП.

## Шаг 4 — push
```bat
git push origin main
git status          :: clean, up to date
git log --oneline -6
```

---

## Критерии приёмки (в REPORT.md)

1. Pre-merge коммит ПК1 создан (хэш), ровно перечисленные пути. ✅/❌
2. Merge выполнен; конфликты разрешены по правилам (перечисли, что и как). ✅/❌
3. В `PROJECT_LOG.md` присутствуют записи ОБЕИХ машин (ничего не потеряно). ✅/❌
4. py_compile чистый; pytest — результат (зелёный / что упало и почему). ✅/❌
5. Push прошёл; финальный `git status` clean; `git log --oneline -6`. ✅/❌

---

## Границы / СТОП-условия

- НЕ `git push --force`, НЕ rebase, НЕ переписывать историю.
- НЕ удалять контент чужой стороны при разрешении конфликтов — при сомнении
  сохраняй обе версии и помечай вопросом в отчёте.
- REPORT ПК2 не найден в `tasks/done/` → СТОП (см. таблицу).
- Merge пошёл вразнос (конфликтов сильно больше 4 файлов, бинарники и т.п.) →
  `git merge --abort`, СТОП, отчёт.
- Разовое исключение: после пуша снова «не коммитить без указания».

## После выполнения

Заполни `tasks/REPORT.md` по критериям 1–5. Остановись.
