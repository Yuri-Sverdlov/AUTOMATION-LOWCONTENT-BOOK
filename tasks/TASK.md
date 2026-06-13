# TASK: git-чекпоинт s13 — пайплайн-дизайн, MY-COMMENTS, архивы done/

**От:** архитектор → **кому:** кодер (терминал, Windows, ПК1)
**Дата:** 2026-06-12
**Тип:** обслуживание репозитория (доки + новые папки)
**Git:** ⚠️ **ЯВНОЕ ИСКЛЮЧЕНИЕ** — в рамках ЭТОГО задания коммитить и пушить РАЗРЕШЕНО.

---

## Что нужно закоммитить

Всё накопленное с последнего пуша (`49a1ea4`):

**Изменённые файлы:**
- `CONTEXT.md`, `PROJECT_LOG.md`, `tasks/TASK.md`, `tasks/REPORT.md`

**Новые папки/файлы:**
- `MY-COMMENTS/01_full_cycle_mindmap.svg`
- `MY-COMMENTS/02_ai_generation_detail.svg`
- `MY-COMMENTS/pipeline-design.md`
- `tasks/backlog/2026-06_pipeline-flowchart.md`
- `tasks/done/2026-06-11_git-checkpoint-s10/`
- `tasks/done/2026-06-11_git-checkpoint-s11/`
- `tasks/done/2026-06-11_merge-sync/`
- `tasks/done/2026-06-11_titles-brick1/`
- `tasks/done/2026-06-11_titles-stage2/`
- `tasks/done/2026-06-12_git-checkpoint-s12/`
- `tasks/done/2026-06-12_merge-sync-pc1/`
- `tasks/done/TASK_2026-06-06_git-checkpoint.md`
- `tests/`

**НЕ добавлять:**
- `MY-COMMENTS/Ты сейчас как новая модель LLM.docx` — личный документ, не в git
- `output/`, `*.png`/`*.pdf`, `data/niches/*/output/`, `.claude/`, `tasks/image_test.png`, `.env`

---

## Шаги

```bat
del .git\config.lock 2>NUL
del .git\index.lock  2>NUL
git push --dry-run origin main   :: должно быть up-to-date, иначе СТОП

git add CONTEXT.md PROJECT_LOG.md tasks/TASK.md tasks/REPORT.md
git add MY-COMMENTS/01_full_cycle_mindmap.svg MY-COMMENTS/02_ai_generation_detail.svg MY-COMMENTS/pipeline-design.md
git add tasks/backlog/2026-06_pipeline-flowchart.md
git add tasks/done/2026-06-11_git-checkpoint-s10 tasks/done/2026-06-11_git-checkpoint-s11 tasks/done/2026-06-11_merge-sync tasks/done/2026-06-11_titles-brick1 tasks/done/2026-06-11_titles-stage2
git add tasks/done/2026-06-12_git-checkpoint-s12 tasks/done/2026-06-12_merge-sync-pc1
git add tasks/done/TASK_2026-06-06_git-checkpoint.md
git add tests/

git status
:: Проверь: MY-COMMENTS/*.docx НЕ добавился; output//.png/.pdf НЕ добавились
python -m pytest tests/ -q
git commit -m "docs: pipeline design + MY-COMMENTS SVGs; archive all done/ tasks; add tests (s13)"
git push origin main
git status
git log --oneline -3
```

---

## Критерии приёмки (в REPORT.md)

1. `git push --dry-run` = up-to-date (нет неожиданных изменений на GitHub). ✅/❌
2. `.docx` и генерёжка НЕ вошли в коммит. ✅/❌
3. pytest зелёный. ✅/❌
4. Хэш + сообщение; push прошёл; `git status` clean. ✅/❌

---

## Границы / СТОП-условия

- `git push --dry-run` показывает non-fast-forward → СТОП, не мёрджить самовольно.
- НЕ `git push --force`.
- Разовое исключение: после пуша снова «не коммитить без указания».

## После выполнения

Заполни `tasks/REPORT.md` кратко (4 критерия + хэш). Остановись.
