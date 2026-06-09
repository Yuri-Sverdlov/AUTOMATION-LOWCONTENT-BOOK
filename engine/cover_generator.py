"""
engine/cover_generator.py

Generates a full KDP cover spread (back + spine + front) as PNG at 300 DPI.
Task: tasks/TASK.md (2026-06-05).
Reference geometry: reference/series-1/ (7.5x9.25", 110 pages, B&W white).

Dependency: Pillow
"""

import os
from PIL import Image, ImageDraw, ImageFont

# ── Constants ─────────────────────────────────────────────────────────────────
DPI = 300
BLEED_IN = 0.125   # inches, applied to all external edges of spread
SAFE_IN  = 0.25    # inches, content safety margin from trim/fold lines

SPINE_FACTORS = {
    "white":  0.002252,   # in/page, B&W white paper
    "cream":  0.0025,
    "color":  0.002347,
}

_FONT_SEARCH = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def _px(inches: float) -> int:
    return round(inches * DPI)


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_SEARCH:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default(size=size)


def build_cover(
    out_path: str,
    pages: int = 110,
    trim_w_in: float = 7.5,
    trim_h_in: float = 9.25,
    paper: str = "white",
    title: str = "",
    subtitle: str = "",
    author: str = "",
    bg_color: str = "#F2ECE3",
    front_image: str | None = None,
    draw_guides: bool = False,
    min_dpi: int = 300,
) -> dict:
    """
    Build a full KDP cover spread PNG (back cover + spine + front cover).
    Returns a dict of computed dimensions for logging and verification.
    """
    # ── Geometry (all from formulas, no magic numbers) ─────────────────────────
    spine_in  = pages * SPINE_FACTORS[paper]
    full_w_in = 2 * trim_w_in + spine_in + 2 * BLEED_IN
    full_h_in = trim_h_in + 2 * BLEED_IN

    full_w_px = _px(full_w_in)
    full_h_px = _px(full_h_in)
    spine_px  = _px(spine_in)
    bleed_px  = _px(BLEED_IN)
    trim_w_px = _px(trim_w_in)
    trim_h_px = _px(trim_h_in)
    safe_px   = _px(SAFE_IN)

    # X layout: [bleed | back trim | spine | front trim | bleed]
    back_trim_x0  = bleed_px
    back_trim_x1  = bleed_px + trim_w_px
    spine_x0      = back_trim_x1
    spine_x1      = spine_x0 + spine_px
    front_trim_x0 = spine_x1
    front_trim_x1 = full_w_px - bleed_px   # absorbs any ±1px rounding remainder

    # Y layout: [bleed | trim | bleed]
    trim_y0 = bleed_px
    trim_y1 = full_h_px - bleed_px

    # Safe zones (content must stay inside these)
    front_safe = (
        front_trim_x0 + safe_px,
        trim_y0 + safe_px,
        front_trim_x1 - safe_px,
        trim_y1 - safe_px,
    )
    back_safe = (
        back_trim_x0 + safe_px,
        trim_y0 + safe_px,
        back_trim_x1 - safe_px,
        trim_y1 - safe_px,
    )

    # ── Canvas ────────────────────────────────────────────────────────────────
    img  = Image.new("RGB", (full_w_px, full_h_px), bg_color)
    draw = ImageDraw.Draw(img)

    # ── Front cover ───────────────────────────────────────────────────────────
    if front_image and os.path.exists(front_image):
        fi  = Image.open(front_image).convert("RGB")
        art_w, art_h = fi.size

        # Target area: full front panel with bleed (spine edge to right bleed edge)
        panel_x0 = spine_x1
        panel_y0 = 0
        panel_w  = full_w_px - spine_x1
        panel_h  = full_h_px

        # DPI check: effective resolution of art relative to physical panel size
        panel_w_in = panel_w / DPI
        panel_h_in = panel_h / DPI
        eff_dpi = min(art_w / panel_w_in, art_h / panel_h_in)

        if eff_dpi < min_dpi:
            need_w = round(panel_w_in * min_dpi)
            need_h = round(panel_h_in * min_dpi)
            print(f"WARNING: front art ~{eff_dpi:.0f} DPI < {min_dpi}, upscaled -> "
                  f"potential quality loss. Provide art at full resolution "
                  f"(~{need_w}x{need_h}px).")

        # Cover-fit (scale-to-fill): scale art to fill panel, preserving aspect ratio
        # Excess is cropped at center. No distortion.
        scale_w = panel_w / art_w
        scale_h = panel_h / art_h
        scale   = max(scale_w, scale_h)  # Take larger scale to ensure full coverage

        new_w = round(art_w * scale)
        new_h = round(art_h * scale)
        fi_scaled = fi.resize((new_w, new_h), Image.LANCZOS)

        # Crop to panel size, centered
        crop_x = (new_w - panel_w) // 2
        crop_y = (new_h - panel_h) // 2
        fi_cropped = fi_scaled.crop((crop_x, crop_y, crop_x + panel_w, crop_y + panel_h))

        # Paste into canvas at panel position
        img.paste(fi_cropped, (panel_x0, panel_y0))

    # Text block: title / subtitle / author, centered in front safe zone
    front_safe_x0, front_safe_y0, front_safe_x1, front_safe_y1 = front_safe
    if title or subtitle or author:
        font_title = _load_font(72)
        font_sub   = _load_font(42)
        font_auth  = _load_font(36)
        line_gap   = 20

        entries = []
        if title:
            entries.append((title, font_title))
        if subtitle:
            entries.append((subtitle, font_sub))
        if author:
            entries.append((author, font_auth))

        bboxes = [draw.textbbox((0, 0), t, font=f) for t, f in entries]
        block_h = sum(bb[3] - bb[1] for bb in bboxes) + line_gap * (len(entries) - 1)

        cx = (front_safe_x0 + front_safe_x1) // 2
        cy = (front_safe_y0 + front_safe_y1) // 2 - block_h // 2
        for (text, font), bb in zip(entries, bboxes):
            tw = bb[2] - bb[0]
            draw.text((cx - tw // 2, cy), text, fill="#1A1A1A", font=font)
            cy += (bb[3] - bb[1]) + line_gap

    # ── Spine ─────────────────────────────────────────────────────────────────
    if pages >= 80 and title and spine_px >= 20:
        font_size_spine = min(spine_px - 8, 56)
        font_spine = _load_font(font_size_spine)
        bb = draw.textbbox((0, 0), title, font=font_spine)
        txt_w, txt_h = bb[2] - bb[0], bb[3] - bb[1]

        # Render text horizontally on a temporary image, then rotate 90° CCW
        # so spine title reads bottom-to-top (standard orientation).
        tmp = Image.new("RGBA", (trim_h_px, spine_px), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text(
            ((trim_h_px - txt_w) // 2, (spine_px - txt_h) // 2),
            title, fill="#1A1A1A", font=font_spine,
        )
        rotated = tmp.rotate(90, expand=True)  # → size: (spine_px, trim_h_px)
        img.paste(rotated, (spine_x0, trim_y0), mask=rotated)

    # ── Save final PNG ────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path, "PNG", dpi=(DPI, DPI))

    # ── Proof image (guides overlay, not in final) ────────────────────────────
    if draw_guides:
        proof = img.copy()
        pd    = ImageDraw.Draw(proof)
        lw    = 3

        # Red: bleed border
        pd.rectangle(
            [bleed_px, bleed_px, full_w_px - bleed_px - 1, full_h_px - bleed_px - 1],
            outline="red", width=lw,
        )
        # Blue: spine fold lines
        pd.line([(spine_x0, 0), (spine_x0, full_h_px)], fill="blue", width=lw)
        pd.line([(spine_x1, 0), (spine_x1, full_h_px)], fill="blue", width=lw)
        # Green: front safe zone
        pd.rectangle(
            [front_safe[0], front_safe[1], front_safe[2], front_safe[3]],
            outline="green", width=lw,
        )
        # Green: back safe zone
        pd.rectangle(
            [back_safe[0], back_safe[1], back_safe[2], back_safe[3]],
            outline="green", width=lw,
        )

        proof_path = out_path.replace(".png", "_proof.png")
        proof.save(proof_path, "PNG", dpi=(DPI, DPI))

    return {
        "full_w_px":    full_w_px,
        "full_h_px":    full_h_px,
        "spine_px":     spine_px,
        "bleed_px":     bleed_px,
        "trim_w_px":    trim_w_px,
        "trim_h_px":    trim_h_px,
        "spine_in":     round(spine_in, 5),
        "back_trim_x":  (back_trim_x0, back_trim_x1),
        "spine_x":      (spine_x0, spine_x1),
        "front_trim_x": (front_trim_x0, front_trim_x1),
        "trim_y":       (trim_y0, trim_y1),
    }


if __name__ == "__main__":
    out = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output",
        "cover_test.png",
    )
    dims = build_cover(
        out,
        title="Test Notebook",
        subtitle="Wide Ruled | 110 Pages",
        author="Test Author",
        draw_guides=True,
    )
    print("Done:", out)
    print("Dimensions:")
    for k, v in dims.items():
        print(f"  {k}: {v}")
