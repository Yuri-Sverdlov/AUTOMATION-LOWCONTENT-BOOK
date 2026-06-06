"""
engine/layout_variants.py

Generates N layout variants (archetypes) for a given art + text,
renders each via text_layout.render_layout, and assembles a contact-sheet gallery.
Task: tasks/TASK.md (2026-06-06).

Dependency: Pillow, text_layout (engine/)
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ── Built-in archetypes (deterministic, no random) ────────────────────────────
# box_pct = [x%, y%, w%, h%] from top-left of art.
# leading: line-height multiplier (default 1.2; tight 0.95×1.2=1.14, airy 1.25×1.2=1.50)
# tracking: extra px between characters
ARCHETYPES: list[dict] = [
    {
        "id":      "A",
        "name":    "center-hero",
        "box_pct": [10, 34, 80, 42],
        "align":   "left",
        "valign":  "top",
        "leading": 1.20,
        "tracking": 0,
        "scrim":   False,
    },
    {
        "id":      "B",
        "name":    "bottom-band",
        "box_pct": [8, 60, 84, 34],
        "align":   "left",
        "valign":  "top",
        "leading": 1.14,   # tight: 1.2 × 0.95
        "tracking": 0,
        "scrim":   True,
    },
    {
        "id":      "C",
        "name":    "centered-airy",
        "box_pct": [12, 30, 76, 45],
        "align":   "center",
        "valign":  "middle",
        "leading": 1.50,   # airy: 1.2 × 1.25
        "tracking": 0,
        "scrim":   False,
    },
    {
        "id":      "D",
        "name":    "top-left-block",
        "box_pct": [8, 30, 58, 40],
        "align":   "left",
        "valign":  "top",
        "leading": 1.20,
        "tracking": 0,
        "scrim":   False,
    },
    {
        "id":      "E",
        "name":    "lower-center",
        "box_pct": [14, 55, 72, 38],
        "align":   "center",
        "valign":  "top",
        "leading": 1.20,
        "tracking": 3,     # extra letter-spacing
        "scrim":   False,
    },
]

_GALLERY_THUMB_W = 220   # px width of each thumbnail in gallery
_GALLERY_COLS    = 3
_GALLERY_PAD     = 14    # px between cells
_GALLERY_LABEL_H = 32    # px height reserved for label under each thumb
_GALLERY_BG      = "#1A1A1A"
_GALLERY_FG      = "#EEEEEE"

_GALLERY_FONT_SEARCH = [
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def _gallery_font(size: int) -> ImageFont.FreeTypeFont:
    for p in _GALLERY_FONT_SEARCH:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default(size=size)


def _build_spec(archetype: dict, text: str | dict,
                img_w: int, img_h: int, base_color: str) -> dict:
    """Build a full text_layout JSON spec from an archetype + text input."""
    if isinstance(text, str):
        roles = {"title": text}
    else:
        roles = text  # dict of {title, subtitle, author, ...}

    elements = {}
    for role, content in roles.items():
        elements[role] = {
            "text":      content,
            "box_pct":   archetype["box_pct"],
            "align":     archetype["align"],
            "valign":    archetype.get("valign", "top"),
            "color":     base_color,
            "scrim":     archetype["scrim"],
            "max_lines": 5,
            "font":      None,
            "leading":   archetype["leading"],
            "tracking":  archetype["tracking"],
        }

    return {
        "canvas":   "front_cover",
        "image_px": [img_w, img_h],
        "elements": elements,
    }


def _build_gallery(variant_pngs: list[tuple[str, str, str]],
                   out_path: str, art_h: int, art_w: int) -> None:
    """
    Assemble a contact-sheet gallery PNG from rendered variant images.
    variant_pngs: list of (variant_id, name, png_path)
    """
    ratio     = art_h / art_w
    thumb_w   = _GALLERY_THUMB_W
    thumb_h   = round(thumb_w * ratio)
    cols      = _GALLERY_COLS
    rows      = (len(variant_pngs) + cols - 1) // cols

    cell_w    = thumb_w
    cell_h    = thumb_h + _GALLERY_LABEL_H
    gallery_w = cols * cell_w + (cols + 1) * _GALLERY_PAD
    gallery_h = rows * cell_h + (rows + 1) * _GALLERY_PAD

    gallery   = Image.new("RGB", (gallery_w, gallery_h), _GALLERY_BG)
    draw      = ImageDraw.Draw(gallery)
    font      = _gallery_font(15)

    for idx, (vid, name, png_path) in enumerate(variant_pngs):
        row = idx // cols
        col = idx % cols
        x   = _GALLERY_PAD + col * (cell_w + _GALLERY_PAD)
        y   = _GALLERY_PAD + row * (cell_h + _GALLERY_PAD)

        thumb = Image.open(png_path).convert("RGB")
        thumb.thumbnail((thumb_w, thumb_h), Image.LANCZOS)
        # Centre the thumb in the cell horizontally if smaller
        tx = x + (thumb_w - thumb.width) // 2
        gallery.paste(thumb, (tx, y))

        label = f"{vid} · {name}"
        bb    = draw.textbbox((0, 0), label, font=font)
        lw    = bb[2] - bb[0]
        lx    = x + (cell_w - lw) // 2
        ly    = y + thumb_h + 6
        draw.text((lx, ly), label, fill=_GALLERY_FG, font=font)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    gallery.save(out_path, "PNG")


def generate_variants(
    art_path: str,
    text: str | dict,
    out_dir: str,
    archetypes: list[dict] | None = None,
    base_color: str = "#FFFFFF",
) -> dict:
    """
    Render N layout variants for the given art and text.

    :param art_path:   source art PNG (no text)
    :param text:       title string OR dict {title, subtitle, author}
    :param out_dir:    output directory for PNG + JSON files
    :param archetypes: list of archetype dicts (None → built-in A..E)
    :param base_color: default text color (used unless overridden per element)
    :returns: dict keyed by variant id → {id, name, png, json, render_info}
    """
    # Import here to avoid circular dep if modules are co-located
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from text_layout import render_layout  # noqa: PLC0415

    if archetypes is None:
        archetypes = ARCHETYPES

    art_img = Image.open(art_path)
    art_w, art_h = art_img.size
    art_img.close()

    os.makedirs(out_dir, exist_ok=True)

    results       = {}
    gallery_items = []

    for arch in archetypes:
        vid      = arch["id"]
        name     = arch["name"]
        png_path = os.path.join(out_dir, f"variant_{vid}.png")
        json_path = os.path.join(out_dir, f"variant_{vid}.json")

        spec = _build_spec(arch, text, art_w, art_h, base_color)

        # Save spec for reproducibility
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)

        render_info = render_layout(art_path, spec, png_path)

        results[vid] = {
            "id":          vid,
            "name":        name,
            "png":         png_path,
            "json":        json_path,
            "render_info": render_info,
        }
        gallery_items.append((vid, name, png_path))

    # Build gallery
    gallery_path = os.path.join(out_dir, "_gallery.png")
    _build_gallery(gallery_items, gallery_path, art_h, art_w)
    results["_gallery"] = gallery_path

    return results


if __name__ == "__main__":
    base    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    art     = os.path.join(base, "data", "niches", "2026-06_test",
                           "sources", "images", "front_art_test.png")
    out_dir = os.path.join(base, "output", "layout_variants")
    title   = "Things I Do When Nobody’s Watching (Totally SFW Edition)"

    results = generate_variants(art, title, out_dir)

    print(f"Gallery: {results['_gallery']}")
    print("\nVariants:")
    for vid, info in results.items():
        if vid == "_gallery":
            continue
        ri = info["render_info"].get("title", {})
        print(f"  [{vid}] {info['name']}")
        print(f"        font_size={ri.get('font_size')}, "
              f"n_lines={ri.get('n_lines')}, "
              f"block_h={ri.get('block_h')}, "
              f"bbox={ri.get('bbox')}")
