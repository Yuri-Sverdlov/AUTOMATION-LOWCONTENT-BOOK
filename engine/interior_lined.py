"""
engine/interior_lined.py

Генерирует PDF-интерьер линованного блокнота (wide-ruled, серия 1).
Задание: tasks/TASK.md (2026-06-05).
Эталон: reference/series-1/ (110 стр., 7.5×9.25", No Bleed, 26 линий на стр.).

Зависимость: reportlab
"""

import os
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# ── Геометрические константы (все в pt, 1 inch = 72 pt) ──────────────────────
PAGE_W_PT = 7.5 * 72          # 540.0 pt
PAGE_H_PT = 9.25 * 72         # 666.0 pt

LINE_COLOR = (153 / 255, 153 / 255, 153 / 255)   # #999999
LINE_WIDTH_PT = 0.48           # 2 px @ 300 DPI

LINE_X_LEFT_PT = 28.35         # 118.125 px @ 300 DPI
LINE_X_RIGHT_PT = 521.10       # 2171.25 px @ 300 DPI

FIRST_LINE_TOP_PT = 24.30      # 101.25 px от верха
LINE_SPACING_PT = 24.696       # 102.9 px шаг


def _draw_lined_page(c: canvas.Canvas, lines_per_page: int) -> None:
    """Рисует wide-ruled линии на текущей странице холста."""
    c.setStrokeColorRGB(*LINE_COLOR)
    c.setLineWidth(LINE_WIDTH_PT)

    for n in range(lines_per_page):
        y_top = FIRST_LINE_TOP_PT + n * LINE_SPACING_PT
        y_bottom = PAGE_H_PT - y_top          # reportlab: начало координат снизу
        c.line(LINE_X_LEFT_PT, y_bottom, LINE_X_RIGHT_PT, y_bottom)


def build_lined_interior(
    out_path: str,
    pages: int = 110,
    lines_per_page: int = 26,
    front_matter_image: str | None = None,
) -> None:
    """
    Генерирует lined-interior PDF.

    :param out_path:          путь к выходному PDF
    :param pages:             число страниц (по умолч. 110)
    :param lines_per_page:    линий на каждой lined-странице (по умолч. 26)
    :param front_matter_image: путь к изображению для стр. 1 (None → пустая стр.)
    """
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    c = canvas.Canvas(out_path, pagesize=(PAGE_W_PT, PAGE_H_PT))

    for page_num in range(1, pages + 1):
        if page_num == 1:
            # TODO: front-matter image (стр. 1).
            # Если front_matter_image задан — вставить по центру страницы.
            if front_matter_image:
                img_w, img_h = PAGE_W_PT * 0.8, PAGE_H_PT * 0.8
                c.drawImage(
                    front_matter_image,
                    (PAGE_W_PT - img_w) / 2,
                    (PAGE_H_PT - img_h) / 2,
                    width=img_w,
                    height=img_h,
                    preserveAspectRatio=True,
                )
            # else: пустая белая страница (фон уже белый по умолчанию)
        else:
            _draw_lined_page(c, lines_per_page)

        c.showPage()

    c.save()


if __name__ == "__main__":
    out = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output",
        "interior_lined_test.pdf",
    )
    build_lined_interior(out)
    print(f"Done: {out}")
