"""
engine/text_layout.py

Draws text elements on an art image according to a JSON layout spec.
Tasks: tasks/TASK.md (2026-06-06), updated for leading/tracking support.

JSON spec format: elements have box_px or box_pct, align, valign, color,
scrim, max_lines, font, leading, tracking.
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont

_FONT_SEARCH = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]

_FONT_SIZE_MAX = 200
_FONT_SIZE_MIN = 8
_SCRIM_ALPHA   = 160
_SCRIM_PADDING = 8


def _find_default_font() -> str | None:
    for p in _FONT_SEARCH:
        if os.path.exists(p):
            return p
    return None


def _load_font(path: str | None, size: int) -> ImageFont.FreeTypeFont:
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default(size=size)


def _text_width(draw: ImageDraw.ImageDraw, text: str,
                font: ImageFont.FreeTypeFont, tracking: int = 0) -> int:
    """Measure text width, accounting for extra inter-character spacing (tracking)."""
    if tracking == 0:
        return int(draw.textlength(text, font=font))
    total = 0
    for i, char in enumerate(text):
        bb = draw.textbbox((0, 0), char, font=font)
        total += bb[2] - bb[0]
        if i < len(text) - 1:
            total += tracking
    return total


def _draw_text_line(draw: ImageDraw.ImageDraw, pos: tuple[int, int], text: str,
                    fill: str, font: ImageFont.FreeTypeFont, tracking: int = 0) -> None:
    """Draw a single line of text with optional letter-spacing (tracking)."""
    if tracking == 0:
        draw.text(pos, text, fill=fill, font=font)
        return
    x, y = pos
    for char in text:
        draw.text((x, y), char, fill=fill, font=font)
        bb = draw.textbbox((0, 0), char, font=font)
        x += (bb[2] - bb[0]) + tracking


def _wrap_text(text: str, font: ImageFont.FreeTypeFont,
               max_width: int, tracking: int = 0) -> list[str]:
    """Word-wrap text to fit within max_width pixels, respecting tracking."""
    words = text.split()
    lines: list[str] = []
    current = ""
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for word in words:
        candidate = (current + " " + word).strip()
        w = _text_width(dummy, candidate, font, tracking)
        if w <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _autofit_font(
    text: str,
    font_path: str | None,
    box_w: int,
    box_h: int,
    max_lines: int,
    leading: float = 1.2,
    tracking: int = 0,
    max_font_size: int | None = None,
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    """
    Find the largest font size where wrapped text fits in box_w×box_h
    with at most max_lines lines, accounting for leading and tracking.
    Returns (font, lines, font_size).
    """
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    cap   = max_font_size or _FONT_SIZE_MAX
    size  = min(_FONT_SIZE_MAX, box_h, cap)

    while size >= _FONT_SIZE_MIN:
        font  = _load_font(font_path, size)
        lines = _wrap_text(text, font, box_w, tracking)
        if len(lines) > max_lines:
            size -= 2
            continue
        line_hs = []
        for line in lines:
            bb = dummy.textbbox((0, 0), line, font=font)
            line_hs.append(bb[3] - bb[1])
        if not line_hs:
            size -= 2
            continue
        line_h   = max(line_hs)
        # gap = vertical space between bottom of one line and top of next
        gap      = max(0, int(line_h * leading) - line_h)
        total_h  = sum(line_hs) + gap * (len(lines) - 1)
        if total_h <= box_h:
            return font, lines, size
        size -= 2

    font  = _load_font(font_path, _FONT_SIZE_MIN)
    lines = _wrap_text(text, font, box_w, tracking)[:max_lines]
    return font, lines, _FONT_SIZE_MIN


def _avg_brightness(img: Image.Image, box_px: tuple[int, int, int, int]) -> float:
    """Average luminance of img under the given box (x, y, w, h)."""
    x, y, w, h = box_px
    region = img.crop((x, y, x + w, y + h)).convert("L")
    data   = list(region.getdata())
    return sum(data) / max(len(data), 1)


def render_layout(
    art_path: str,
    layout: dict | str,
    out_path: str,
    default_font: str | None = None,
    leading: float = 1.2,
    tracking: int = 0,
) -> dict:
    """
    Draw text elements on the art image per the layout spec.

    :param art_path:     path to the source art PNG
    :param layout:       layout dict or path to a .json file
    :param out_path:     where to save the resulting PNG
    :param default_font: fallback TTF path (overrides built-in search list)
    :param leading:      line-height multiplier (1.0 = tight, 1.5 = airy); default 1.2
    :param tracking:     extra pixels between characters (letter-spacing); default 0
    :returns: dict keyed by element role → {font_size, n_lines, lines, bbox, box_px, block_h}
    """
    if isinstance(layout, str):
        with open(layout, encoding="utf-8") as f:
            layout = json.load(f)

    img   = Image.open(art_path).convert("RGB")
    draw  = ImageDraw.Draw(img, "RGBA")
    img_w, img_h = img.size

    fallback_font = default_font or _find_default_font()
    dummy         = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    results: dict[str, dict] = {}

    for role, elem in layout.get("elements", {}).items():
        text       = elem.get("text", "")
        align      = elem.get("align",  "left")
        valign     = elem.get("valign", "top")
        color      = elem.get("color")
        use_scrim  = elem.get("scrim", False)
        max_lines  = elem.get("max_lines", 10)
        font_hint  = elem.get("font") or fallback_font
        # Per-element leading/tracking override global params
        el_leading  = elem.get("leading",  leading)
        el_tracking = elem.get("tracking", tracking)

        # ── Box in pixels ─────────────────────────────────────────────────────
        if "box_px" in elem:
            bx, by, bw, bh = elem["box_px"]
        else:
            pct = elem["box_pct"]
            bx  = round(pct[0] / 100 * img_w)
            by  = round(pct[1] / 100 * img_h)
            bw  = round(pct[2] / 100 * img_w)
            bh  = round(pct[3] / 100 * img_h)

        # ── Auto-fit font & wrap ──────────────────────────────────────────────
        mf_pct        = elem.get("max_font_pct")
        max_font_size = round(mf_pct / 100 * img_h) if mf_pct else None
        font, lines, font_size = _autofit_font(
            text, font_hint, bw, bh, max_lines, el_leading, el_tracking, max_font_size
        )

        # ── Measure lines ─────────────────────────────────────────────────────
        line_bbs = [dummy.textbbox((0, 0), ln, font=font) for ln in lines]
        line_hs  = [bb[3] - bb[1] for bb in line_bbs]
        line_ws  = [_text_width(dummy, ln, font, el_tracking) for ln in lines]
        max_lh   = max(line_hs) if line_hs else font_size
        gap      = max(0, int(max_lh * el_leading) - max_lh)
        block_h  = sum(line_hs) + gap * (len(lines) - 1)
        max_line_w = max(line_ws) if line_ws else 0

        # ── Vertical alignment ────────────────────────────────────────────────
        if valign == "middle":
            text_y = by + (bh - block_h) // 2
        elif valign == "bottom":
            text_y = by + bh - block_h
        else:
            text_y = by

        # ── Auto-contrast (fallback when no color given) ──────────────────────
        if not color:
            brightness = _avg_brightness(img, (bx, by, bw, bh))
            color = "#FFFFFF" if brightness < 128 else "#000000"

        # ── Scrim ─────────────────────────────────────────────────────────────
        if use_scrim:
            r, g, b    = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            lum        = 0.299 * r + 0.587 * g + 0.114 * b
            scrim_rgb  = (0, 0, 0) if lum > 128 else (255, 255, 255)
            draw.rectangle(
                [bx - _SCRIM_PADDING,
                 text_y - _SCRIM_PADDING,
                 bx + max_line_w + _SCRIM_PADDING,
                 text_y + block_h + _SCRIM_PADDING],
                fill=(*scrim_rgb, _SCRIM_ALPHA),
            )

        # ── Draw lines ────────────────────────────────────────────────────────
        actual_bboxes: list[tuple[int, int, int, int]] = []
        cy = text_y
        for line, lw, lh in zip(lines, line_ws, line_hs):
            if align == "center":
                cx = bx + (bw - lw) // 2
            elif align == "right":
                cx = bx + bw - lw
            else:
                cx = bx
            _draw_text_line(draw, (cx, cy), line, color, font, el_tracking)
            actual_bboxes.append((cx, cy, cx + lw, cy + lh))
            cy += lh + gap

        if actual_bboxes:
            tx0 = min(b[0] for b in actual_bboxes)
            ty0 = min(b[1] for b in actual_bboxes)
            tx1 = max(b[2] for b in actual_bboxes)
            ty1 = max(b[3] for b in actual_bboxes)
        else:
            tx0 = ty0 = tx1 = ty1 = 0

        results[role] = {
            "font_size": font_size,
            "n_lines":   len(lines),
            "lines":     lines,
            "bbox":      (tx0, ty0, tx1, ty1),
            "box_px":    (bx, by, bw, bh),
            "block_h":   block_h,
        }

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path, "PNG")
    return results


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    art  = os.path.join(base, "data", "niches", "2026-06_test",
                        "sources", "images", "front_art_test.png")
    spec = os.path.join(base, "data", "niches", "2026-06_test",
                        "sources", "layout_test.json")
    out  = os.path.join(base, "output", "text_layout_test.png")

    result = render_layout(art, spec, out)
    print(f"Done: {out}")
    for role, info in result.items():
        print(f"\n[{role}]")
        for k, v in info.items():
            print(f"  {k}: {v}")
