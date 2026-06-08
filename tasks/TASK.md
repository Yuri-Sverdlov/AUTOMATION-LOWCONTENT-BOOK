# TASK: git-чекпоинт — сохранить «зону безопасности» на GitHub

**От:** архитектор → **кому:** кодер (терминал)
**Дата:** 2026-06-08
**Тип:** обслуживание репозитория
**Git:** ⚠️ **ЯВНОЕ ИСКЛЮЧЕНИЕ** из правила «кодер не коммитит» (`AGENTS.md`).
В рамках ИМЕННО этого задания коммитить и пушить РАЗРЕШЕНО.

---

## Цель

Этап «зона безопасности» принят архитектором (`tasks/done/2026-06-08_safe_box/ACCEPTED.md`).
Нужно сохранить реальные изменения логичными коммитами и запушить на `origin`.
Коммит делается на Windows-машине пользователя, где git работает штатно.

**Принцип: сначала показать и проверить, потом коммитить. Никаких сюрпризов.**

> ВАЖНО про CRLF: `git status` покажет «modified» почти у всех файлов — это шум
> переводов строк (LF↔CRLF), не реальные правки. Истинный дифф смотри так:
> `git diff --ignore-all-space --stat`. По существу изменены только движки и док-файлы.

---

## Шаг 0 — Префлайт. Если что-то не так — СТОП и отчёт.

```bash
git rev-parse --abbrev-ref HEAD      # ожидаем main
git remote -v                        # origin = https://github.com/Yuri-Sverdlov/AUTOMATION-LOWCONTENT-BOOK.git
git push --dry-run origin main       # проверка прав на ЗАПИСЬ (нужен GitHub-токен)
```
Если dry-run падает с ошибкой авторизации — **СТОП, не коммить.** Впиши в REPORT.md:
«нужен GitHub Personal Access Token с правом repo (push)».

## Шаг 1 — Smoke-тест (не коммитить сломанное)

```bash
python engine/text_layout.py
python engine/layout_variants.py
```
Оба — без traceback. Если падает — **СТОП**, опиши ошибку в REPORT.md.

## Шаг 2 — Что коммитим (точечно, НЕ `git add -A` вслепую)

**Коммит 1 — автоматизация:**
```
engine/text_layout.py engine/layout_variants.py
```
Сообщение: `feat: safe-box + max-font cap for text overlay (layout_variants)`

**Коммит 2 — документация этапа:**
```
CONTEXT.md PROJECT_LOG.md tasks/REPORT.md tasks/TASK.md tasks/done/2026-06-08_safe_box/
```
Сообщение: `docs: accept safe-box stage; archive task + log`

После каждого `git add ...` сделай `git status` и `git diff --cached --ignore-all-space --stat`,
убедись, что добавилось ровно нужное.

## Шаг 3 — НЕ коммитить демо-мусор

Папки `tasks/lv_test/` и `tasks/lv_test_safe/` — разовые тест-прогоны. **НЕ добавляй их.**
PNG и так режутся `.gitignore` глобально; но `run_demo.py`/`verify_criteria.py`/`*.json`
из этих папок коммитить НЕ нужно. Если они попадают в `git status` — просто не делай им `git add`.

## Шаг 4 — Push

```bash
git push origin main
```

---

## Критерии приёмки (впиши в REPORT.md)

1. Префлайт: ветка `main`, origin корректный, push-доступ есть. ✅/❌
2. Smoke-тест: оба скрипта без ошибок. ✅/❌
3. Создан коммит 1 (движки) и коммит 2 (доки); впиши хэши (`git log --oneline -3`). ✅/❌
4. В коммиты НЕ попали `tasks/lv_test*/`, `output/`, `*.pdf`, `*.png`, `.env`, `.claude/`
   (подтверди `git show --stat` по каждому коммиту). ✅/❌
5. `git push origin main` прошёл; `git status` = clean, up to date with origin/main. ✅/❌

---

## Границы / СТОП-условия

- Нет push-доступа → НЕ коммить, отчитайся, что нужен токен.
- Smoke-тест падает → НЕ коммить, отчитайся.
- **НЕ** `git push --force`, **НЕ** трогать чужие ветки/историю.
- **НЕ** добавлять `output/`, бинарники, секреты, демо-папки `lv_test*`.
- Это разовое исключение: после выполнения снова действует «не коммитить без указания».

---

## После выполнения

Заполни `tasks/REPORT.md`: префлайт, smoke, хэши коммитов, результат push, финальный
`git status` и `git log --oneline -4`. Останься.
