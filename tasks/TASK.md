# TASK: git-чекпоинт s12 — приёмка sync'а + pytest в requirements

**От:** архитектор → **кому:** кодер (терминал, Windows, ПК1)
**Дата:** 2026-06-12
**Тип:** обслуживание репозитория (доки + 1 строка в requirements)
**Git:** ⚠️ **ЯВНОЕ ИСКЛЮЧЕНИЕ** — в рамках ЭТОГО задания коммитить и пушить РАЗРЕШЕНО.

---

## Цель

Зафиксировать на GitHub приёмку sync'а двух компьютеров (сессия 12) + добавленный
`pytest` в `requirements.txt` (твоё же замечание из прошлого отчёта). После пуша
ПК1 полностью совпадает с GitHub.

> CRLF: `git status` шумит — истина через `git diff --ignore-all-space --stat`.
> Добавлять ТОЛЬКО перечисленные пути.

## Шаги

```bat
del .git\config.lock 2>NUL
del .git\index.lock  2>NUL
git push --dry-run origin main
git diff --ignore-all-space --stat
git add CONTEXT.md PROJECT_LOG.md requirements.txt tasks/TASK.md tasks/REPORT.md tasks/done/2026-06-12_merge-sync-pc1
git status
python -m pytest tests/ -q
git commit -m "docs: accept pc1-pc2 merge-sync (archive s12); add pytest to requirements"
git push origin main
git status
git log --oneline -3
```

Ожидаемые пути: `CONTEXT.md`, `PROJECT_LOG.md`, `requirements.txt`,
`tasks/TASK.md`, `tasks/REPORT.md`, `tasks/done/2026-06-12_merge-sync-pc1/` (3 файла).
Генерёжку/мусор (`output/`, `*.png`/`*.pdf`, `.claude/`, `.docx`, `tasks/image_test.png`)
НЕ добавлять.

---

## Критерии приёмки (в REPORT.md)

1. Push-доступ ок; в коммите ровно перечисленные пути, лишнего нет. ✅/❌
2. pytest зелёный перед коммитом. ✅/❌
3. Хэш + сообщение; push прошёл; финальный `git status` clean, up to date. ✅/❌

---

## Границы / СТОП-условия

- НЕ `git push --force`, НЕ трогать код движков.
- Если `git push --dry-run` показывает non-fast-forward (на GitHub что-то новое) —
  СТОП, сообщи архитектору (не мёрджить самовольно).
- Разовое исключение: после пуша снова «не коммитить без указания».

## После выполнения

Заполни `tasks/REPORT.md` кратко (3 критерия + хэш). Остановись.
