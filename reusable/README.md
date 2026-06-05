# reusable/ — готовые к запуску исходники

Это **распакованная** версия `../SCRIPTS-CATALOG.md`: тот же отобранный код, но
не вшитый в один Markdown, а разложенный по реальным файлам — можно сразу
импортировать и запускать.

Связка двух форматов:
- `../SCRIPTS-CATALOG.md` — **путеводитель** (что это, моя оценка, контекст).
- `reusable/` (эта папка) — **сам код** в рабочем виде.

## Содержимое

| Файл | Ценность | Статус |
|------|----------|--------|
| `python/llm_client.py` | ⭐⭐⭐ | запускается; нужен `config/models.yaml` + `.env` с ключом (или Ollama без ключа) |
| `python/title_blurb_orchestrator.py` | ⭐⭐ | **референс**: завязан на структуру проекта DOE (импорт `execution.orchestrator`), целиком не запустится — берём паттерн и функции парсинга JSON |
| `python/agents.py` | ⭐ | **референс-каркас**: контент в `_create_story` — заглушка, заменить на вызов `llm_client` |
| `js/data-reader.js` | ⭐⭐⭐ | запускается (нужны `xlsx`, `fs-extra`); логику валидации планируем портировать на Python |
| `js/title-generator.js` | ⭐⭐ | запускается как есть (Node) |
| `js/cover-generator.js` | ⭐⭐ | нужен пакет `canvas`; в проекте обложки делаем на Pillow |
| `playwright-DO-NOT-RUN-ON-KDP/` | ⚠️ | **архив, против KDP не запускать** — см. README внутри папки |

## Зависимости (если будешь запускать)

Python: `pip install openai requests pyyaml python-dotenv`
Node (JS): `npm install xlsx fs-extra canvas`

> Подробный разбор каждого файла — в `../SCRIPTS-CATALOG.md`.
