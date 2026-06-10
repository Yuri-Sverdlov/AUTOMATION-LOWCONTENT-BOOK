# TASK: git-чекпоинт — сохранить локальные доки + дропнуть устаревший stash

**От:** архитектор → **кому:** кодер (терминал, Windows)
**Дата:** 2026-06-10
**Тип:** обслуживание репозитория
**Git:** ⚠️ **ЯВНОЕ ИСКЛЮЧЕНИЕ** — в рамках ЭТОГО задания коммитить и пушить РАЗРЕШЕНО.

---

## Цель

Зафиксировать накопленные на этом ПК локальные правки (возврат ссылки DEV-NOTES в
`AGENTS.md`, запись в журнал, архив приёмки сборщика) и **дропнуть устаревший stash**
от прошлой синхронизации. Код движков НЕ менялся — это коммит документации/петли задач.

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

## Шаг 1 — дропнуть устаревший stash
```bat
git stash list
```
- Если есть `stash@{0}: ... local edits before sync ...` — это он, устаревший. Дропни:
```bat
git stash drop stash@{0}
```
- Если stash-список пуст (уже дропнут вручную) — просто отметь это в отчёте, идём дальше.
- Если в списке НЕ тот stash (другое описание) — СТОП, не трогай, сообщи архитектору.

## Шаг 2 — посмотреть реальные изменения
```bat
git status --short
git diff --ignore-all-space --stat
```
Ожидаемые к коммиту пути (док/петля задач):
`AGENTS.md`, `PROJECT_LOG.md`, `CONTEXT.md` (если изменён), `tasks/TASK.md`,
`tasks/REPORT.md`, новый каталог `tasks/done/2026-06-10_verify_build_cover/`.

## Шаг 3 — лёгкий smoke (не коммитить сломанное)
```bat
python -m py_compile engine/build_cover.py engine/cover_generator.py engine/cover_to_pdf.py engine/text_layout.py engine/layout_variants.py engine/interior_lined.py
```
Без ошибок. (Код не меняли, это просто страховка.)

## Шаг 4 — коммит (точечно) и push
```bat
git add AGENTS.md PROJECT_LOG.md tasks/TASK.md tasks/REPORT.md tasks/done/2026-06-10_verify_build_cover
:: добавь CONTEXT.md ТОЛЬКО если он реально изменён (по git diff выше)
git status
git commit -m "docs: restore DEV-NOTES link; log s9 (sync+move+build_cover accepted); archive verify"
git push origin main
```
После `git add` — проверь `git status`, что добавилось ровно нужное, без лишнего.

## Шаг 5 — НЕ добавлять
`output/`, любые `*.png`/`*.pdf` (генерёжка), `data/niches/*/output/`, `.claude/`,
`~$*`, `.env`, `nul`, тестовые `book-verify-*` папки. Всё это в `.gitignore` или мусор —
если всплыло в `git status`, просто не делай `git add`.

---

## Критерии приёмки (в REPORT.md)

1. Префлайт: ветка main, origin ок, push-доступ есть. ✅/❌
2. Stash: устаревший дропнут (или подтверждено, что список пуст). ✅/❌
3. В коммит вошли только доки/петля задач (перечисли файлы); генерёжка/мусор НЕ вошли. ✅/❌
4. py_compile без ошибок. ✅/❌
5. Коммит создан (впиши хэш и сообщение); `git push origin main` прошёл. ✅/❌
6. Финальный `git status` = clean, up to date; `git log --oneline -3`. ✅/❌

---

## Границы / СТОП-условия

- Если нет push-доступа — СТОП, отчёт (нужен токен).
- Если stash в списке не тот — СТОП, не дропать.
- НЕ `git push --force`, НЕ переписывать историю, НЕ добавлять генерёжку/мусор.
- Разовое исключение: после пуша снова «не коммитить без указания».

---

## После выполнения

Заполни `tasks/REPORT.md`: префлайт, судьба stash, список закоммиченного, хэш, push,
финальный `git status`/`git log`. Остановись.
