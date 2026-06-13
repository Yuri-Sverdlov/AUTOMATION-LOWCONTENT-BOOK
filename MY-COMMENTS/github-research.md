# GitHub Research — KDP Automation Repos
**Дата:** 2026-06-13 (сессия 14)
**Цель:** не изобретать велосипед — найти, что уже сделано, взять паттерны.

---

## ⭐ Высокий приоритет — взять и использовать

### `rxpelle/kdp-scout` ★36
**https://github.com/rxpelle/kdp-scout**
Инструмент исследования ниш и ключевых слов. Наиболее релевантный из всех найденных.

Что умеет:
- Майнинг ключевых слов из Amazon autocomplete (a-z expansion), авто-обход 50 KDP-категорий
- Трекинг конкурентов по ASIN: BSR, цена, рейтинг, динамика снимков
- Импорт отчётов Amazon Ads → кросс-референс с базой ключевых слов
- Составной скоринг (autocomplete position + ad impressions + clicks + orders + competition)
- Экспорт **7 × 50 байт KDP backend keywords** (готовый формат для KDP!)
- Поддержка 8 маркетплейсов: us, ca, au, de, uk, fr, es, **it**
- SQLite локально, без облака, без телеметрии, MIT license

Что взять для нашего проекта:
- **Паттерн backend keyword export** (7 слотов × 50 байт) — точно нужен на шаге 5 пайплайна
- **BSR-to-sales estimation model** (`collectors/bsr_model.py`) — для Фазы 1 разведки
- **Autocomplete miner** (`collectors/autocomplete.py`) — вместо ручного BookBolt в Фазе 1
- Команда `kdp-scout trending` — поиск горячих ниш без стартового зерна

Ограничения: это CLI-инструмент для fiction/nonfiction авторов (по умолчанию Kindle Books dept.),
не заточен под low-content. Но ядро автокомплит-майнера и BSR-модель универсальны.

**Вывод:** ★ Установить и использовать как инструмент разведки в Фазе 1. Код открытый —
можно подсмотреть паттерн backend keyword export и адаптировать для нашего шага 5.

---

## 🔶 Средний приоритет — изучить паттерны

### `fracabu/claude-kdp-agents` ★2
**https://github.com/fracabu/claude-kdp-agents**
Multi-agent пайплайн на Claude Code для coloring/activity books. Dec 2025. US+IT рынки.

Архитектура (3 агента, последовательно):
```
Market Intelligence Architect (Phase 1)
  → NICHE_REPORT_*.md (competitor analysis, BSR, Google Trends, Go/No-Go)
Product Design Director (Phase 2)
  → CONTENT_BLUEPRINT_*.md (tech specs, AI image prompts, Canva brief)
Publishing Optimization Specialist (Phase 3)
  → PUBLISHING_PACKAGE_*.md (HTML descriptions, backend keywords, A+ Content)
```

Что интересно:
- **Структура агентов** в `.claude/agents/` — это субагенты Claude Code, не Python-код.
  Похоже на нашу архитектуру Архитектор+Кодер, но всё внутри Claude Code.
- **Паттерн: HTML description + byte-count backend keywords** в Phase 3 → наш шаг 5 (Title+Blurb)
  должен делать то же самое
- **Publishing Optimization Specialist** явно проверяет байты backend keywords — взять как образец

Ограничения: никакого Python-кода, только агентные промпты в .md файлах. Нет реальной
автоматизации PDF/обложки. Но паттерн трёхфазного пайплайна нам близок.

**Вывод:** Прочитать файлы агентов фазы 3 — там промпты для HTML-описания и keyword export.
Это прямой аналог нашего шага 5.

---

### `alexeygrigorev/ai-book-generator` ★5
**https://github.com/alexeygrigorev/ai-book-generator**
Полный KDP пайплайн для текстовых книг (text → EPUB → KDP interior PDF + cover PDF).
Gemini для генерации контента, Python + XeLaTeX (Docker) для PDF.

Что интересно:
- `scripts/create_kdp_cover.py` — **автоматический расчёт ширины корешка** по числу страниц,
  задник + корешок + передник, crop marks, bleed. Похоже на наш `cover_generator.py`.
  Стоит сравнить формулы расчёта корешка.
- `scripts/create_kdp_interior.py` — XeLaTeX, 6×9, mirror margins, гаттер. Другой подход
  (LaTeX vs reportlab) — для наших нужд reportlab проще.
- Структура вывода: `books/book-name/plan.yaml` + `interior.pdf` + `cover.pdf` — очень похоже
  на нашу `data/niches/<ниша>/output/<дата>/book-N/`
- `book_generator/content.py` генерирует back cover description — паттерн для нашего шага 5

Ограничения: сфокусирован на текстовых книгах (fiction/nonfiction), не low-content.
TTS, S3, Docker — лишний оверхед для нас.

**Вывод:** Подсмотреть формулу расчёта корешка в `create_kdp_cover.py` и паттерн
back cover description в `content.py`.

---

### `JYMOH001/Puzzle-Book-Generator` (апрель 2026)
**https://github.com/JYMOH001/Puzzle-Book-Generator**
Генерация puzzle books (Sudoku, Maze) — Python, KDP-совместимые PDF.
Самый близкий к нашему случаю по типу контента (не текст, а визуальные страницы).

Что взять:
- Паттерн генерации повторяющихся puzzle-страниц (аналог наших линованных страниц)
- Как они параметризуют difficulty/количество/размер

**Вывод:** Изучить структуру PDF-генерации для puzzle страниц.

---

### `abubakarsayem/Amazon-KDP-Book-Metadata-Generator-with-LLM` ★0
**https://github.com/abubakarsayem/Amazon-KDP-Book-Metadata-Generator-with-LLM**
Streamlit + Gemini 2.5 Flash + LangChain. Единственный промпт → SEO title + description.

Что взять:
- Практически ничего. Подход (один промпт, один выход) намного слабее нашего пайплайна
  (3 персоны × 6 вариантов → арбитры → z-score).
- Интересен только как демонстрация того, что простой подход "в лоб" существует и
  конкурирует с нашей более сложной архитектурой — значит наша сложность оправдана.

---

## 🔴 Красная линия — НЕ использовать, НЕ вдохновляться

### `BrahimAkar/Amazon-KDP-Automater`
### `misarb/SpiderKDP`

Оба используют browser automation (Playwright/Selenium) для загрузки книг в KDP.
**Нарушают нашу красную линию** — бан аккаунта.
Упоминаем только как предупреждение: такие решения существуют, люди публикуют их, это не значит,
что это безопасно.

---

## 📊 Общая картина

| Репозиторий | Ниша | Звёзд | Полезность | Что взять |
|---|---|---|---|---|
| rxpelle/kdp-scout | keyword research | 36 | ★★★ высокая | установить, backend keyword export паттерн |
| fracabu/claude-kdp-agents | coloring books | 2 | ★★ средняя | промпты фазы 3 (HTML desc + keywords) |
| alexeygrigorev/ai-book-generator | text books | 5 | ★★ средняя | расчёт корешка, back cover desc паттерн |
| JYMOH001/Puzzle-Book-Generator | puzzle books | ? | ★★ средняя | паттерн PDF puzzle-страниц |
| abubakarsayem/KDP-Metadata-LLM | metadata | 0 | ★ низкая | подтверждение нашего подхода сложнее |
| BrahimAkar/KDP-Automater | upload | ? | ❌ красная линия | — |
| misarb/SpiderKDP | upload | ? | ❌ красная линия | — |

---

## 🎯 Выводы для нашего проекта

**1. Разведка ниш (Фаза 1) — kdp-scout закрывает большую часть задачи.**
   Вместо ручного исследования в BookBolt → `kdp-scout mine-categories` + `kdp-scout trending`
   + `kdp-scout track add <ASIN>`. Паттерн можно встроить в `niche.yaml` как шаг 0.

**2. Backend keywords (шаг 5) — паттерн найден в двух местах.**
   rxpelle/kdp-scout: `kdp-scout export backend` (7 × 50 байт).
   fracabu: Phase 3 агент явно считает байты.
   Нам нужно реализовать это в шаге 5 — взять готовую логику.

**3. Наш title pipeline (шаги 3–4) — уникален.** Ничего подобного (3 персоны + арбитры +
   z-score) в открытом доступе нет. abubakarsayem доказывает, что конкуренты делают "один промпт"
   — наша архитектура дифференцирована.

**4. Расчёт корешка** — alexeygrigorev/ai-book-generator имеет рабочую формулу.
   Стоит сверить с нашей в `cover_generator.py`.

**5. Архитектура многоагентного пайплайна** — fracabu подтверждает правильность нашего
   подхода (файловый обмен, фазы, разделение ролей). Но они работают только с Claude Code,
   мы с Python-кодом — более надёжно для продакшена.
