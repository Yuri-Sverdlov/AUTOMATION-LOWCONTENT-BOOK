# TASK: git-чекпоинт сессии 11 (конвейер названий, этапы 1–2)

**От:** архитектор → **кому:** кодер (терминал, реальная Windows-машина)
**Дата:** 2026-06-11
**Тип:** git-чекпоинт (закрытие сессии)
**Git:** ✅ **ЯВНОЕ ИСКЛЮЧЕНИЕ** — коммит и push в рамках ЭТОГО задания РАЗРЕШЕНЫ.
**Важно:** выполнять на реальной машине (там корректный CRLF и git-credentials).
Из песочницы git ненадёжен (CRLF-шум + устаревшие снимки) — не использовать.

---

## Что коммитим (итог сессии 11)

Конвейер названий, этапы 1–2 (приняты), закрытый дизайн, каркас конфига, обновлённые
доки и архивы. Перечень намеренных изменений:

- `config/models.yaml`, `config/models.example.yaml`, `.env.example`
- `engine/titles/__init__.py`, `generator.py`, `pool.py`
- `engine/titles/prompts/joker_1.md`, `joker_2.md`, `joker_3.md`
- `data/niches/2026-06_test/sources/hooks.example.yaml`
- `tests/test_title_parse.py`, `tests/test_pool.py`
- `requirements.txt`
- `tasks/backlog/2026-06_title-pipeline.md`
- `CONTEXT.md`, `PROJECT_LOG.md`, `tasks/TASK.md`, `tasks/REPORT.md`
- `tasks/done/2026-06-11_titles-brick1/`, `tasks/done/2026-06-11_titles-stage2/`,
  `tasks/done/2026-06-11_merge-sync/`

## ⛔ Что НЕ коммитим (проверь, что НЕ попало в индекс)

- `.env` (секрет, в `.gitignore`);
- `tmp_pool.json` (временный вывод smoke-теста);
- `engine/titles/__pycache__/`, любые `*.pyc`;
- мусор в корне: файл `nul`, `*.docx` («Можешь ли…», «Рассуждение…»), `tasks/lv_test*`.

## Шаг 0 — СКАН СЕКРЕТОВ (критично)

```
git grep -nE "sk-or-v1-[A-Za-z0-9]{20,}" -- . ':!tasks/done/*'
```
Ожидаемо: ПУСТО (реальный ключ должен быть только в `.env`, который не отслеживается).
Если нашёлся реальный ключ в любом отслеживаемом файле — **СТОП**, замаскируй и сообщи.
(Плейсхолдеры вида `YOUR_KEY_HERE`/`***REDACTED***` — это не секрет, они допустимы.)

## Шаг 1 — обзор и подготовка индекса

```
git status
git add -A
git reset -- .env tmp_pool.json nul "engine/titles/__pycache__" *.docx tasks/lv_test
git status        # убедись: в индексе только намеренные файлы из списка выше
```
(если какого-то мусорного пути нет — ничего страшного, `git reset` по нему просто без эффекта).

## Шаг 2 — коммит

```
git commit -m "feat(titles): generation stage — 3 generators + candidate pool; close design; config scaffold" ^
  -m "- title-pipeline design decisions + z-score memo (backlog)" ^
  -m "- config/models.yaml (advanced, Variant A) + .env.example" ^
  -m "- engine/titles: generator.py, pool.py, personas joker_1..3" ^
  -m "- tests: test_title_parse, test_pool (smoke on OpenRouter OK)" ^
  -m "- requirements: openai, python-dotenv, pyyaml" ^
  -m "- docs: CONTEXT + PROJECT_LOG s11; archive brick1/stage2/merge-sync" ^
  -m "- security: moved leaked OpenRouter key out of tracked files"
```
(в PowerShell перенос строки — backtick `` ` ``; можно и одной строкой одним `-m`.)

## Шаг 3 — push

```
git push origin main
```
**НЕ** `--force`, **НЕ** rebase.

## Шаг 4 — проверка

```
git status -sb      # ожидаем: вровень с origin/main, дерево чисто (кроме игнор-мусора)
git log --oneline -5
```

---

## Критерии приёмки (в REPORT.md)

1. Скан секретов (шаг 0) — пусто; реального ключа в отслеживаемых файлах нет. ✅/❌
2. В индексе только намеренные файлы; `.env`/`tmp_pool.json`/`__pycache__`/`*.docx`/`nul` НЕ в коммите. ✅/❌
3. Коммит создан (впиши хэш). ✅/❌
4. `git push origin main` прошёл (приведи строку `..  main -> main`). ✅/❌
5. Финальный `git status -sb` = вровень с origin/main; `git log --oneline -5` (приведи). ✅/❌

## СТОП-условия

- Нашёлся реальный ключ в отслеживаемом файле → СТОП, маскируй, сообщи.
- Ошибка авторизации push → СТОП, отчёт «нужен доступ к GitHub».
- Любой неожиданный конфликт/расхождение с origin → СТОП, не делай `--force`, опиши.

## После выполнения

Заполни `tasks/REPORT.md`: результат скана секретов, что в индексе, хэш коммита, результат
push, финальные `git status -sb` и `git log`.
