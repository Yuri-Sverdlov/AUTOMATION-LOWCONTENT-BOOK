# TASK: git-чекпоинт сессии 8 — сохранить всё на GitHub

**От:** архитектор → **кому:** кодер (терминал)
**Дата:** 2026-06-08
**Тип:** обслуживание репозитория
**Git:** ⚠️ **ЯВНОЕ ИСКЛЮЧЕНИЕ** — в рамках ЭТОГО задания коммитить и пушить РАЗРЕШЕНО.

---

## Цель

Закоммитить результаты сессии 8 (оркестратор + простой режим + доки) и запушить на
`origin/main`. Коммит — на Windows-машине пользователя (git + креды работают).

> CRLF: `git status` покажет «modified» у кучи трекнутых файлов — это шум LF↔CRLF.
> Истинный дифф: `git diff --ignore-all-space --stat`. Добавляем ТОЛЬКО перечисленные пути.

## Шаг 0 — префлайт (если падает авторизация — СТОП, отчёт)

```
git rev-parse --abbrev-ref HEAD          # main
git remote -v                            # origin = .../AUTOMATION-LOWCONTENT-BOOK.git
git push --dry-run origin main
```

## Шаг 1 — smoke (не коммитить сломанное)

```
python engine/build_cover.py             # простой режим: соберёт cover в book-2, без traceback
python -m py_compile engine/build_cover.py engine/cover_generator.py
```

## Шаг 2 — точечные коммиты (НЕ `git add -A`)

**Коммит 1 — код:**
```
git add engine/build_cover.py engine/cover_generator.py config.yaml
git commit -m "feat: simple-mode validated cover wrapper + front cover-fit"
```

**Коммит 2 — паспорт ниши:**
```
git add data/niches/2026-06_snarky-notebook/niche.yaml
git commit -m "chore: add 2026-06_snarky-notebook niche passport"
```

**Коммит 3 — доки/задачи/архивы/бэклог:**
```
git add CONTEXT.md PROJECT_LOG.md tasks/TASK.md tasks/REPORT.md tasks/backlog ^
  tasks/done/2026-06-08_git-checkpoint tasks/done/2026-06-08_build-cover-chain ^
  tasks/done/2026-06-08_simple-validate-wrap
git commit -m "docs: accept cover-chain + simple-mode; archive tasks; add backlog; log s8"
```

После каждого `git add` — `git status` и `git diff --cached --ignore-all-space --stat`,
убедись, что добавилось ровно нужное.

## Шаг 3 — НЕ добавлять

`nul` (мусор от `> nul`), `tasks/lv_test/`, `tasks/lv_test_safe/`, посторонний
`"Можешь ли ты прочитать один.docx"`, любые `output/`, `*.png`, `*.pdf` (и так в `.gitignore`).
Если попали в `git status` — просто не делай им `git add`.

## Шаг 4 — push

```
git push origin main
```

## Критерии приёмки (в REPORT.md)

1. Префлайт: ветка main, origin ок, push-доступ есть. ✅/❌
2. Smoke: `build_cover.py` без traceback, py_compile ок. ✅/❌
3. Созданы 3 коммита; впиши хэши (`git log --oneline -4`). ✅/❌
4. В коммиты НЕ попали `nul`, `lv_test*`, `.docx`, `output/`, бинарники
   (подтверди `git show --stat` по каждому). ✅/❌
5. `git push origin main` прошёл; `git status` чисто, up to date. ✅/❌

## Границы

- НЕ `git push --force`, НЕ трогать чужие ветки/историю.
- НЕ добавлять мусор/бинарники/output.
- Разовое исключение: после пуша снова «не коммитить без указания».

## После выполнения

Заполни `tasks/REPORT.md`: префлайт, smoke, 3 хэша, результат push, финальный
`git status` и `git log --oneline -5`.
