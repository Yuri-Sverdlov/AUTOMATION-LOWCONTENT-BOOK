# QUICK START GUIDE — AUTOMATION-LOWCONTENT-BOOK

Практическая шпаргалка «как запустить» по каждому блоку конвейера. В отличие от
`PROJECT-OVERVIEW.md` (стратегия) и `CONTEXT.md` (память проекта), здесь — только команды,
файлы и порядок действий.

**Блоки гида:**

1. **Генерация названий** — заполнено ниже ✅
2. Интерьер (PDF) — _TODO_
3. Обложка (разворот + PDF) — _TODO_
4. Паспорт ниши и сборка крючков (Фаза 1) — _TODO_
5. Публикация в KDP (вручную) — _TODO_

---

## 1. Генерация названий

**Что делает:** из выбранных вручную крючков (топовые фразы с Amazon) генерирует и затем
оценивает названия-крючки для книги. Воронка: **генераторы → пул кандидатов → [арбитры] →
ранжированный список**.

**Статус:** этапы 1–2 готовы (генерация + сборка пула). Этап 3 (арбитры, баллы,
ранжирование) ещё НЕ реализован.

### Файлы

| Назначение | Путь |
|---|---|
| **Скрипт: один генератор** | `engine/titles/generator.py` (функции `load_niche`, `build_generation_prompt`, `parse_titles`, `generate_titles` + CLI) |
| **Скрипт: сборщик пула** (3 шутника × наборы крючков → пул) | `engine/titles/pool.py` (`build_pool`, `load_hooks_file` + CLI) |
| **Промпты генераторов** («шутники») | `engine/titles/prompts/joker_1.md` (юмор/дерзость), `joker_2.md` (эмпатия/тепло), `joker_3.md` (минимализм/польза) |
| **Промпты арбитров** | `engine/titles/prompts/arbiter_*.md` — **ещё НЕ созданы** (этап 3). Критерии-рубрика пока описаны в дизайн-файле (ниже); первоисточник — `G:\AI\_MY_PROGRAMMING_4\DOE-ORIGINAL-TITLE\execution\prompts\judge.md` |
| **Конфиг моделей** | `config/models.yaml` (режим `advanced`, модель/температура на каждую роль; Вариант А — одна модель, разные t°). Образец: `config/models.example.yaml` |
| **Секреты (API-ключ)** | `.env` (реальный `OPENROUTER_API_KEY`, в `.gitignore` — в git НЕ идёт). Образец: `.env.example` |
| **Вход: крючки** (выбираешь вручную с Amazon) | `data/niches/<ниша>/sources/hooks.yaml`. Образец-рыба: `data/niches/2026-06_test/sources/hooks.example.yaml` |
| **Паспорт ниши** (аудитория, тип, формула) | `data/niches/<ниша>/niche.yaml` |
| **Тесты** | `tests/test_title_parse.py` (разбор ответа LLM), `tests/test_pool.py` (сборка пула) |
| **Дизайн и принятые решения** (рубрика арбитра, z-score, фильтры) | `tasks/backlog/2026-06_title-pipeline.md` |

### Подготовка (один раз)

1. Зависимости: `pip install -r requirements.txt` (нужны `openai`, `python-dotenv`, `pyyaml`).
2. Ключ: скопировать `.env.example` → `.env`, вписать реальный `OPENROUTER_API_KEY`.
   Без `python-dotenv` ключ из `.env` не подхватится.
3. Модель: в `config/models.yaml` указать рабочий slug у ролей `joker_*`
   (сейчас `minimax/minimax-M3`, проверено живым прогоном).
4. Крючки: скопировать `hooks.example.yaml` → `hooks.yaml` и вписать реальные топовые фразы
   с Amazon. Формат:
   ```yaml
   hook_sets:
     - ["productivity boost", "goal crusher"]
     - ["self care journal", "anxiety relief"]
   ```
   «Набор» = фразы, отдаваемые шутникам разом (обычно 2). Число наборов = длина `hook_sets`.

### Запуск (из корня репозитория)

**Сухой прогон (офлайн, без API)** — посмотреть план и промпт:
```
python -m engine.titles.pool --niche data/niches/2026-06_test/niche.yaml \
  --hooks-file data/niches/2026-06_test/sources/hooks.example.yaml --dry-run
```

**Боевой прогон — весь пул (3 шутника × все наборы):**
```
python -m engine.titles.pool --niche data/niches/2026-06_test/niche.yaml \
  --hooks-file data/niches/2026-06_test/sources/hooks.yaml \
  --roles joker_1 joker_2 joker_3 --n 6 --out pool.json
```

**Только один генератор (быстрая проверка):**
```
python -m engine.titles.generator --niche data/niches/2026-06_test/niche.yaml \
  --hooks "productivity boost" "goal crusher" --n 6
```

### Результат

`pool.json` — структурированный пул кандидатов; каждый кандидат:
```json
{"id": "s1-joker_1-1", "title": "...", "author_role": "joker_1",
 "hook_set_index": 1, "hooks": ["productivity boost", "goal crusher"]}
```
Это вход для будущей ступени арбитров (этап 3).

### Важное

- **Красная линия:** крючки выбирает человек руками на Amazon. Код их НЕ скрейпит.
- **Вариант А (сейчас):** одна модель у всех шутников, разница — персона + температура
  (0.8/0.9/1.0). **Вариант B (на будущее):** разные модели у `joker_*` — меняется только
  `config/models.yaml`, код не трогаем.
- **Ключ — только в `.env`.** Никогда не клади реальный ключ в `.env.example`, `models.yaml`
  или отчёты (они идут в git).
