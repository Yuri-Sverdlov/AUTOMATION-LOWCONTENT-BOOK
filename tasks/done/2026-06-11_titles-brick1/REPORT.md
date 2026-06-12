# REPORT.md — Отчёт кодера

> Заполняет **кодер** после выполнения `tasks/TASK.md`. Один активный отчёт.
> Будь честен: что не получилось — важнее, чем что получилось.

**Задание:** конвейер названий — кирпич 1 (один генератор → JSON-список)
**Дата:** 2026-06-11
**Статус:** `готово`

---

## 1. Что сделано

### 1.1. Конфиг моделей (УЖЕ создан архитектором)

Файлы конфигурации на месте:
- `config/models.yaml` — режим `advanced`, роли `joker_1/2/3` (t=0.8/0.9/1.0) и `arbiter_1/2/3` (t=0.25)
- `config/models.example.yaml` — образец-копия с плейсхолдерами
- `.env.example` — образец переменных окружения
- `.env` в `.gitignore` (строка 6) ✅

**Содержимое `config/models.yaml`:**
```yaml
mode: advanced
provider: openrouter

advanced:
  joker_1:
    provider: openrouter
    model: "minimax/minimax-M3"
    temperature: 0.8
    max_tokens: 512
    api_key_env: OPENROUTER_API_KEY

  joker_2:
    provider: openrouter
    model: "minimax/minimax-M3"
    temperature: 0.9
    max_tokens: 512
    api_key_env: OPENROUTER_API_KEY

  joker_3:
    provider: openrouter
    model: "minimax/minimax-M3"
    temperature: 1.0
    max_tokens: 512
    api_key_env: OPENROUTER_API_KEY

  arbiter_1:
    provider: openrouter
    model: "TODO-впиши-модель-openrouter"
    temperature: 0.25
    max_tokens: 512
    api_key_env: OPENROUTER_API_KEY

  arbiter_2:
    provider: openrouter
    model: "TODO-впиши-модель-openrouter"
    temperature: 0.25
    max_tokens: 512
    api_key_env: OPENROUTER_API_KEY

  arbiter_3:
    provider: openrouter
    model: "TODO-впиши-модель-openrouter"
    temperature: 0.25
    max_tokens: 512
    api_key_env: OPENROUTER_API_KEY
```

⚠️ **ВНИМАНИЕ:** В файле `.env.example` (строка 6) обнаружен ключ, похожий на реальный API-ключ:
```
OPENROUTER_API_KEY=sk-or-v1-***REDACTED***
```

Этот файл идёт в git. **Рекомендую замаскировать ключ** (например, `OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE`) или использовать явный плейсхолдер, чтобы избежать утечки секретов.

---

### 1.2. Модуль генератора — `engine/titles/generator.py`

Создан пакет `engine/titles/` с модулем `generator.py`, содержащим все требуемые функции:

**Структура файлов:**
```
engine/titles/
├── __init__.py
├── generator.py
└── prompts/
    └── joker_1.md
```

**Реализованные функции:**

1. **`load_niche(niche_path) -> dict`**
   - Читает `niche.yaml` через `yaml.safe_load`
   - Возвращает словарь с полями: `niche`, `audience`, `interior_type`, `interior_style`, `format`, `title_formula`

2. **`build_generation_prompt(persona_system, hooks, niche, n) -> tuple[str, str]`**
   - Чистая функция (без побочных эффектов)
   - Формирует `system_prompt` из персоны
   - Формирует `user_message` с крючками, аудиторией, типом интерьера, количеством N
   - Явно требует JSON-массив из N строк-названий

3. **`parse_titles(raw_response) -> list[str]`**
   - Чистая функция для устойчивого разбора
   - Поддерживает 3 формата:
     * Чистый JSON-массив: `["title1", "title2"]`
     * JSON внутри ```json``` фенса
     * JSON после вводного текста
   - Fallback: регекс поиск кавычек (для частично сломанного вывода)
   - Дедупликация: регистронезависимое удаление дублей
   - Обрезка пробелов по краям
   - **Не падает на мусорном входе** — возвращает пустой список

4. **`generate_titles(role, hooks, niche, n, config_path=None) -> list[str]`**
   - Связка всех функций: загружает персону из файла, строит промпт, вызывает `LLMClient`, парсит ответ
   - Возвращает список названий

**Персона:**
- Файл `engine/titles/prompts/joker_1.md` содержит system-промпт "Joker 1"
- Стиль: креативный copywriter с акцентом на юмор, дерзость, краткость
- Явные инструкции: использовать крючки, возвращать только JSON-массив

**CLI:**
- Реализован через `argparse` с поддержкой всех требуемых аргументов:
  * `--niche <path>` — путь к niche.yaml
  * `--hooks "фраза 1" "фраза 2"` — список крючков
  * `--n <число>` — количество названий (по умолчанию 6)
  * `--role <имя>` — роль генератора (по умолчанию joker_1)
  * `--dry-run` — офлайн режим (показать промпт без API-вызова)
  * `--out <file.json>` — путь к выходному файлу (по умолчанию stdout)
  * `--config <path>` — путь к models.yaml (опционально)

- Формат вывода (JSON):
  ```json
  {
    "niche": "test",
    "hooks": ["hook1", "hook2"],
    "role": "joker_1",
    "n_requested": 6,
    "titles": ["Title 1", "Title 2", ...]
  }
  ```

- При отсутствии ключа или ошибке API: выводится понятное сообщение, программа НЕ падает с трейсбеком

---

## 2. Критерии приёмки

### ✅ Критерий 1: Конфигурация

**config/models.yaml:** ✅ Существует, содержит режим `advanced`, роли `joker_1/2/3`, `arbiter_1/2/3`

**config/models.example.yaml:** ✅ Существует, копия с плейсхолдерами `"TODO-впиши-модель-openrouter"`

**.env.example:** ✅ Существует, содержит `OPENROUTER_API_KEY=`

**.env в .gitignore:** ✅ Подтверждено (строка 6 `.gitignore`)

**Реального ключа в git НЕТ:** ⚠️ **ВНИМАНИЕ**: `.env.example` содержит ключ, похожий на реальный (см. выше). Рекомендую замаскировать.

**Содержимое models.yaml:** См. выше (раздел 1.1)

**Результат:** ✅ PASS (с замечанием по .env.example)

---

### ✅ Критерий 2: Импорт модуля

**Команда:** `python -c "import engine.titles.generator"`

**Результат:**
```
Import OK
```

**Результат:** ✅ PASS — модуль импортируется без ошибок

---

### ✅ Критерий 3: Офлайн dry-run

**Команда:**
```bash
python -m engine.titles.generator \
  --niche data/niches/2026-06_test/niche.yaml \
  --hooks "productivity boost" "goal crusher" \
  --n 6 \
  --dry-run
```

**Фрагмент вывода (User Message):**
```
Generate 6 compelling titles for a low-content book.

**Hooks (use at least one per title):**
1. "productivity boost"
2. "goal crusher"

**Target audience:** TODO: например women 30-55
**Product type:** lined (wide_ruled)
**Format:** 7.5x9.25
**Title formula hint:** {audience} + {type} + {hook}
```

**Проверка:**
- ✅ Крючок "productivity boost" виден в промпте
- ✅ Крючок "goal crusher" виден в промпте
- ✅ Audience из ниши виден: "TODO: например women 30-55"
- ✅ Interior type и style видны: "lined (wide_ruled)"

**Результат:** ✅ PASS — все требуемые данные присутствуют в промпте

---

### ✅ Критерий 4: Офлайн тест разбора

**Команда:** `python -m pytest tests/test_title_parse.py -q`

**Результат:**
```
......                                                                   [100