# TASK: git-чекпоинт сессии 10 — доки ревизии на GitHub

**От:** архитектор → **кому:** кодер (терминал, Windows)
**Дата:** 2026-06-11
**Тип:** обслуживание репозитория (только документация, код НЕ менялся)
**Git:** ⚠️ **ЯВНОЕ ИСКЛЮЧЕНИЕ** — в рамках ЭТОГО задания коммитить и пушить РАЗРЕШЕНО.

---

## Цель

Зафиксировать на GitHub результаты ревизии проекта (сессия 10): запись в журнал,
обновлённый CONTEXT, 5 новых backlog-файлов, архив чекпоинта s9, новые TASK/REPORT.

> CRLF: `git status` покажет «modified» у многих файлов — это шум LF↔CRLF. Истинные
> изменения смотри через `git diff --ignore-all-space --stat`. Добавляй ТОЛЬКО
> перечисленные ниже пути (точечно, без `git add -A`).

---

## Шаг 0 — префлайт (если падает авторизация — СТОП, отчёт)
```bat
del .git\config.lock 2>NUL
del .git\index.lock  2>NUL
git rev-parse --abbrev-ref HEAD       :: main
git remote -v                         :: origin = .../AUTOMATION-LOWCONTENT-BOOK.git
git push --dry-run origin main        :: проверка доступа на запись
```

## Шаг 1 — убрать мусор с диска (НЕ через git)
```bat
del "~$OJECT-OVERVIEW.md" 2>NUL
del "~$RUCTURE.md" 2>NUL
```
Это lock-файлы Word, в `.gitignore` уже есть — просто удалить с диска.

## Шаг 2 — посмотреть реальные изменения
```bat
git status --short
git diff --ignore-all-space --stat
```
Ожидаемые к коммиту пути (всё — доки/петля задач):
- `CONTEXT.md` (секция ревизии s10, приоритеты, статус движков)
- `PROJECT_LOG.md` (запись сессии 10)
- `tasks/TASK.md` (это задание), `tasks/REPORT.md` (сброшен в ожидание)
- `tasks/backlog/2026-06_crib-builder.md`
- `tasks/backlog/2026-06_parametrize-interior.md`
- `tasks/backlog/2026-06_pytest-smoke.md`
- `tasks/backlog/2026-06_published-csv-dedup.md`
- `tasks/backlog/2026-06_first-real-book.md`
- `tasks/done/2026-06-10_git-checkpoint-s9/` (TASK.md + REPORT.md + ACCEPTED.md)

## Шаг 3 — лёгкий smoke (не коммитить сломанное)
```bat
python -m py_compile engine/build_cover.py engine/cover_generator.py engine/cover_to_pdf.py engine/text_layout.py engine/layout_variants.py engine/interior_lined.py
```
Без ошибок. (Код не меняли, это страховка.)

## Шаг 4 — коммит (точечно) и push
```bat
git add CONTEXT.md PROJECT_LOG.md tasks/TASK.md tasks/REPORT.md tasks/backlog/2026-06_crib-builder.md tasks/backlog/2026-06_parametrize-interior.md tasks/backlog/2026-06_pytest-smoke.md tasks/backlog/2026-06_published-csv-dedup.md tasks/backlog/2026-06_first-real-book.md tasks/done/2026-06-10_git-checkpoint-s9
git status
git commit -m "docs: model review s10 — findings to context/log, 5 backlog items, archive s9 checkpoint"
git push origin main
```
После `git add` — проверь `git status`: добавилось ровно перечисленное, без лишнего.

## Шаг 5 — НЕ добавлять
`output/`, любые `*.png`/`*.pdf` (генерёжка), `data/niches/*/output/`, `.claude/`,
`~$*`, `.env`, `nul`, `tasks/image_test.png`. Если всплыло в `git status` —
просто не делай `git add`.

---

## Критерии приёмки (в REPORT.md)

1. Префлайт: ветка main, origin ок, push-доступ есть. ✅/❌
2. Lock-файлы `~$*` удалены с диска. ✅/❌
3. В коммит вошли только перечисленные доки (приведи список); генерёжка/мусор НЕ вошли. ✅/❌
4. py_compile без ошибок. ✅/❌
5. Коммит создан (впиши хэш и сообщение); `git push origin main` прошёл. ✅/❌
6. Финальный `git status` = clean, up to date; `git log --oneline -3`. ✅/❌

---

## Границы / СТОП-условия

- Если нет push-доступа — СТОП, отчёт (нужен токен).
- НЕ `git push --force`, НЕ переписывать историю, НЕ добавлять генерёжку/мусор.
- НЕ трогать код движков и `config.yaml` — это чисто документационный коммит.
- Разовое исключение: после пуша снова «не коммитить без указания».

---

## После выполнения

Заполни `tasks/REPORT.md`: префлайт, удаление мусора, список закоммиченного, хэш,
push, финальный `git status`/`git log`. Остановись.
