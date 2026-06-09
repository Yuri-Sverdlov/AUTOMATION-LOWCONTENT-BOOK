# TASK: простой режим — проверка размера готового разворота + обёртка в PDF

**От:** архитектор → **кому:** кодер (терминал)
**Дата:** 2026-06-08 (заменяет прошлое ТЗ про DPI-турникет — оно НЕ выполнялось)
**Тип:** упрощение пайплайна (валидатор размера + упаковщик)
**Git:** ⛔ НЕ коммитить и НЕ пушить.

---

## Цель (простыми словами)

Пользователь сам рисует **полный разворот обложки** (задник+корешок+перёд) в графическом
редакторе, пиксель-в-пиксель под требование Amazon KDP. Скрипт НЕ масштабирует и НЕ
собирает — он только:
1. читает `config.yaml` (размер обложки в дюймах ИЛИ см + путь к файлу разворота);
2. считает ожидаемый размер в пикселях (`размер × 300 DPI`, см → дюймы делением на 2.54);
3. **сверяет** реальные пиксели файла с ожидаемыми (точно, допуск **±1 px** на округление);
   - не совпало → **`raise` с конкретными числами** «нужен WxH px, у вас AxB px»;
   - совпало → кладёт файл как `cover.png` и оборачивает в `cover.pdf` в дерево ниши.

Никакого cover-fit, кропа, апскейла, DPI-порогов. Только «точный размер или ошибка».

---

## Часть A — `config.yaml` (в корне репо), новая схема

```yaml
cover_file: "data/niches/2026-06_snarky-notebook/output/2026-06-08/book-1/cover.png"
unit: in              # in | cm
cover_w: 15.4967      # ШИРИНА полного разворота (в указанных единицах)
cover_h: 9.5          # ВЫСОТА полного разворота
dpi: 300
niche: "2026-06_snarky-notebook"
book: "book-2"        # writing target; для теста — book-2, чтобы не затирать вход
# date: optional, по умолчанию сегодня
```

- `unit: in` → `expected_px = round(value * dpi)`.
- `unit: cm` → `expected_px = round(value / 2.54 * dpi)`.
- Зависимость: `pyyaml`.

## Часть B — `engine/build_cover.py`: новая функция простого режима

Добавь функцию (НЕ удаляя существующую `build_cover_chain` — она остаётся для будущего
авто-пайплайна, но CLI по умолчанию использует НОВУЮ):

```python
def wrap_validated_cover(config: dict) -> dict:
    # 1. expected_w_px, expected_h_px из cover_w/cover_h/unit/dpi
    # 2. art_w, art_h = Image.open(cover_file).size
    # 3. если abs(art_w-expected_w_px)>1 или abs(art_h-expected_h_px)>1:
    #       raise ValueError(понятное сообщение с требуемым и фактическим размером)
    # 4. целевая папка data/niches/{niche}/output/{date}/{book}/ (makedirs)
    # 5. сохранить/скопировать разворот как cover.png (без пересжатия — копия файла)
    # 6. cover_to_pdf.cover_png_to_pdf(cover.png, cover.pdf, dpi=dpi)
    # 7. вернуть dict: пути, expected/actual размеры, geometry PDF
```

Текст ошибки (пример):
```
Cover size mismatch: file is 2400x2957 px, but config requires 4649x2850 px
(15.4967x9.5 in @ 300 DPI). Create the spread at exactly 4649x2850 px, or fix
cover_w/cover_h/unit in config.yaml.
```

**CLI:** `python engine/build_cover.py [--config config.yaml]` → читает конфиг → зовёт
`wrap_validated_cover`. Печатает результат (или падает с ошибкой размера).

- Копию `cover.png` делать БЕЗ перекодирования содержимого (это уже мастер-разворот; можно
  `shutil.copy`, либо open+save без изменений — главное не менять пиксели/не ресемплить).
- Идемпотентность: повторный запуск перезаписывает cover.png/cover.pdf.

## Часть C — НЕ трогать

- `cover_generator.py`, `cover_to_pdf.py` (используется как есть), `text_layout.py`,
  `layout_variants.py` — без правок (diff `--ignore-all-space` пуст).
- `build_cover_chain` остаётся в файле, но из CLI не вызывается.

---

## Прогон приёмки (обе ветки)

**Ветка ПРОХОДА:** `config.yaml` как выше (`cover_file` = готовый разворот 4649×2850,
