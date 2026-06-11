# TASK: добавочный чекпоинт — закоммитить QUICK_START.md

**От:** архитектор → **кому:** кодер (терминал, реальная Windows-машина)
**Дата:** 2026-06-11
**Тип:** мини git-чекпоинт (один новый файл)
**Git:** ✅ **РАЗРЕШЕНО** коммитить и пушить в рамках этого задания.

---

## Контекст

Предыдущий чекпоинт s11 принят (`efd595a` на origin/main). После него архитектор создал
новый файл `QUICK_START.md` (шпаргалка «как запустить», заполнен блок «Генерация названий»).
Он ещё не в git. Плюс с этого задания добавились архивы:
`tasks/done/2026-06-11_git-checkpoint-s11/` (TASK/REPORT/ACCEPTED) и этот `tasks/TASK.md`/`REPORT.md`.

## Что коммитим

- `QUICK_START.md` (корень)
- `tasks/done/2026-06-11_git-checkpoint-s11/` (архив прошлого чекпоинта)
- `tasks/TASK.md`, `tasks/REPORT.md` (это задание + отчёт)

## ⛔ Что НЕ коммитим

`.env`, `tmp_pool.json`, `*.pyc`/`__pycache__`, `nul`, `*.docx`, `tasks/lv_test*`.

## Шаги

```
git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}" -- .        # ожидаемо ПУСТО; если нашлось — СТОП
git add QUICK_START.md tasks/done/2026-06-11_git-checkpoint-s11 tasks/TASK.md tasks/REPORT.md
git status                                            # только намеренные файлы
git commit -m "docs: QUICK_START guide (title-generation block) + archive s11 checkpoint"
git push origin main
git status -sb                                        # вровень с origin/main
git log --oneline -3
```

## Критерии приёмки (в REPORT.md)

1. Скан секретов пуст. ✅/❌
2. В индексе только намеренные файлы (`.env`/`tmp_pool.json`/мусор НЕ в коммите). ✅/❌
3. Коммит создан (хэш). ✅/❌
4. `git push origin main` прошёл (строка `..  main -> main`). ✅/❌
5. `git status -sb` = вровень с origin/main; `git log --oneline -3`. ✅/❌

## СТОП-условия

- Реальный ключ в отслеживаемом файле → СТОП. Никаких `--force`/rebase.

## После выполнения

Заполни `tasks/REPORT.md`: скан, индекс, хэш, push, финальные `git status -sb` и `git log`.
