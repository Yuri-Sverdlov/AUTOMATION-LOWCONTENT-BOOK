# CONTEXT.md — Память проекта

> Читать **первым делом**. Медленный слой: суть проекта, стек, роли, текущий фокус.
> История сессий — в `PROJECT_LOG.md`. Активное задание — в `tasks/TASK.md`.

**Обновлено:** 2026-06-05

---

## Суть проекта

`AUTOMATION-LOWCONTENT-BOOK` — конвейер для производства **low-content книг** под
Amazon KDP (линованные блокноты, журналы, планировщики и т.п.). Цель: кодом готовить
готовые к загрузке файлы (interior.pdf + cover.png + crib.md), оставив человеку только
ручную загрузку в KDP. Полная стратегия — в `PROJECT-OVERVIEW.md`, структура данных —
в `STRUCTURE.md`.

**Красная линия:** никакой автоматизации браузера против KDP (бан). См. `AGENTS.md`.

---

## Разделение ролей

- **Архитектор** (чат, дорогая модель) — стратегия, ТЗ, проверка, логи.
- **Кодер** (терминал, дешёвая модель, напр. DeepSeek/Qwen через Claude Code CLI) —
  пишет код по `tasks/TASK.md`, отчитывается в `tasks/REPORT.md`.

Обмен — только через файлы. Каноническая файловая система описана в `AGENTS.md`.

---

## Стек (предварительно)

- **Интерьер PDF:** Python + `reportlab` (генерация по геометрии KDP).
- **Обложка:** `Pillow` (позже).
- **LLM (названия/описания):** Claude API или Ollama; есть `reusable/python/llm_client.py`.
- **Данные разведки:** Publisher Rocket / Book Bolt, Amazon autocomplete, Google Trends.

---

## Эталон: Серия 1 (уже выпущено вручную)

В `reference/series-1/` лежат файлы реально выпущенной книги (сделана в Book Bolt):

- `interior_reference.pdf` — 110 страниц, **7.5 × 9.25", No Bleed, ч/б, белая бумага**.
- `sample_page_05.json` — образец линованной страницы (Book Bolt формат).
- `sample_page_01.json` — образец страницы 1 (декоративная картинка, не линовка).
- `KDP_SETTINGS.txt` — настройки KDP для этой книги.

**Структура книги (контракт):** стр. 1 — декоративная картинка; стр. 2–110 —
одинаковые **wide-ruled, 26 линий**. Точные числа — в `tasks/TASK.md`.

---

## Текущий фокус

Физика книги собрана и принята:
- **`engine/interior_lined.py`** (reportlab) — линованный интерьер, копия серии 1.
- **`engine/cover_generator.py`** (Pillow) — параметрический разворот KDP (bleed,
  корешок от числа страниц, safe-зоны, proof-картинка).

`data/niches/2026-06_test/output/2026-06-05/book-1/` = реальные `interior.pdf` + `cover.png`
от наших движков. book-2/3 — заглушки.

**book-1 готов к ручной загрузке в KDP:** `interior.pdf` + `cover.pdf` + `crib.md`.

### Гибридная обложка — все 4 кирпича готовы
1. **Арт** (ComfyUI/RunPod, внешний) — чистый фон без текста.
2. **Раскладка** — vision-модель (или архитектор вручную, «шаг А») выдаёт JSON: где/как
   ставить текст. Тест-кейс: `data/niches/2026-06_test/sources/layout_test.json`.
3. **Текст кодом** — `engine/text_layout.py`: рисует текст по JSON (авто-кегль/перенос/
   контраст/scrim). Тест-арт: `sources/images/front_art_test.png`.
4. **Разворот+PDF** — `engine/cover_generator.py` (front_image) + `engine/cover_to_pdf.py`.

**Следующее — «сборка» в один проход:** art + layout JSON → text_layout → вставить
готовый фронт как `front_image` в cover_generator (полный разворот) → cover_to_pdf.
Затем: автоматизация шага А через vision-API; мост ComfyUI→папка ниши; данные ниши
в `niche.yaml`; сборщик `crib.md` из паспорта; пакетная генерация серии.
