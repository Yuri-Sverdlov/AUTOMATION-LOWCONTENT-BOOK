# REPORT.md — Отчёт кодера

> Заполняет **кодер** после выполнения `tasks/TASK.md`. Один активный отчёт.
> Будь честен: что не получилось — важнее, чем что получилось.

**Задание:** `engine/layout_variants.py` — N раскладок текста по архетипам + галерея отбора
**Дата:** 2026-06-06
**Статус:** `готово`

---

## 1. Что сделано

- **Обновлён `engine/text_layout.py`** — добавлены параметры `leading: float = 1.2`
  и `tracking: int = 0` в `render_layout` и `_autofit_font`; добавлены хелперы
  `_text_width` (tracking-aware) и `_draw_text_line` (посимвольный рендер с tracking).
  Элементы JSON-спека могут переопределять `leading`/`tracking` поэлементно.
- **Создан `engine/layout_variants.py`** — функция `generate_variants()` со встроенным
  набором архетипов A..E; сборка галереи-контактника.
- Сгенерированы в `output/layout_variants/`:
  - `variant_A.png`, `variant_B.png`, `variant_C.png`, `variant_D.png`, `variant_E.png`
  - `variant_A.json` … `variant_E.json` (спеки для воспроизводимости)
  - `_gallery.png` (контактник 3×2, 220px миниатюры с подписями)

---

## 2. Как запускать

```bash
# Тест-кейс ниши -> output/layout_variants/
python engine/layout_variants.py

# Из кода:
# from engine.layout_variants import generate_variants
# results = generate_variants("art.png", "My Book Title", "output/variants/")
```

---

## 3. Результаты проверок (критериев приёмки)

| # | Критерий | Результат | Фактические числа |
|---|----------|-----------|-------------------|
| 1 | Запуск без ошибок; 5 PNG + 5 JSON + `_gallery.png` | ✅ | Все 11 файлов созданы |
| 2 | Все PNG = 733×903, bbox в рамке, фон не затёрт | ✅ | A-E = (733,903); bg-пиксель вне текста совпадает с оригиналом |
| 3 | Варианты различимы: разброс центра Y > 15% | ✅ | Центры Y: A=456, B=689, C=473, D=421, E=664 → spread=268px=**29.7%** |
| 4 | B (scrim=true): подложка есть; A-E без scrim — нет | ✅ | Пиксель (60,560): orig=(24,71,51), B=(121,130,126) — изменён; A=(24,71,51) — не изменён |
| 5 | C, E — center; A, B, D — left | ✅ | C bbox_cx=366≈art_cx=366; E bbox_cx=367≈art_cx=366; A/B/D bbox_x0=73/59/59 (левый край) |
| 6 | B(tight) vs C(airy): block_h заметно отличаются | ✅ | B block_h=**295px** (leading=1.14) vs C block_h=**341px** (leading=1.50), diff=**46px** |
| 7 | `_gal