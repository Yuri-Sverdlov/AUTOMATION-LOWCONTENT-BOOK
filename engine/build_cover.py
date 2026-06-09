"""
engine/build_cover.py

Two modes:
1. Simple mode (wrap_validated_cover): Validate pre-created full spread size + wrap to PDF
2. Auto mode (build_cover_chain): Generate spread from front PNG + wrap to PDF

Task: tasks/TASK.md (2026-06-08).
"""

import os
import sys
import datetime
import shutil
from PIL import Image


def wrap_validated_cover(config: dict) -> dict:
    """
    Simple mode: Validate exact pixel size of user-created full spread, wrap to PDF.

    User creates the full spread (back+spine+front) externally at exact KDP dimensions.
    This function:
    1. Reads expected dimensions from config (cover_w/cover_h in inches or cm @ DPI)
    2. Compares with actual file dimensions (tolerance ±1 px for rounding)
    3. If mismatch: raises ValueError with required vs actual sizes
    4. If match: copies spread to niche output tree as cover.png + wraps to cover.pdf

    :param config: dict with keys:
        - cover_file: path to pre-created full spread PNG
        - unit: "in" or "cm"
        - cover_w, cover_h: dimensions in specified units
        - dpi: dots per inch (typically 300)
        - niche: niche slug
        - book: book folder name
        - data_root: (optional) root directory, default "data"
        - date: (optional) ISO date, default today

    :returns: dict with paths, expected/actual sizes, PDF geometry

    :raises ValueError: if actual file size != expected size (±1 px tolerance)
    :raises FileNotFoundError: if cover_file doesn't exist
    """
    # ── Extract config ──────────────────────────────────────────────────────────
    cover_file = config["cover_file"]
    unit = config.get("unit", "in")
    cover_w = config["cover_w"]
    cover_h = config["cover_h"]
    dpi = config.get("dpi", 300)
    niche = config["niche"]
    book = config["book"]
    data_root = config.get("data_root", "data")
    date = config.get("date")

    if date is None:
        date = datetime.date.today().isoformat()

    # ── Compute expected pixel dimensions ───────────────────────────────────────
    if unit == "in":
        expected_w_px = round(cover_w * dpi)
        expected_h_px = round(cover_h * dpi)
    elif unit == "cm":
        # cm -> inches: divide by 2.54
        expected_w_px = round((cover_w / 2.54) * dpi)
        expected_h_px = round((cover_h / 2.54) * dpi)
    else:
        raise ValueError(f"Unknown unit '{unit}', expected 'in' or 'cm'")

    # ── Read actual file dimensions ─────────────────────────────────────────────
    if not os.path.exists(cover_file):
        raise FileNotFoundError(f"Cover file not found: {cover_file}")

    img = Image.open(cover_file)
    art_w, art_h = img.size
    img.close()

    # ── Validate size (tolerance ±1 px for rounding) ───────────────────────────
    w_diff = abs(art_w - expected_w_px)
    h_diff = abs(art_h - expected_h_px)

    if w_diff > 1 or h_diff > 1:
        raise ValueError(
            f"Cover size mismatch: file is {art_w}x{art_h} px, "
            f"but config requires {expected_w_px}x{expected_h_px} px\n"
            f"({cover_w}x{cover_h} {unit} @ {dpi} DPI). "
            f"Create the spread at exactly {expected_w_px}x{expected_h_px} px, "
            f"or fix cover_w/cover_h/unit in config.yaml."
        )

    # ── Target output directory ─────────────────────────────────────────────────
    output_dir = os.path.join(data_root, "niches", niche, "output", date, book)
    os.makedirs(output_dir, exist_ok=True)

    cover_png = os.path.join(output_dir, "cover.png")
    cover_pdf = os.path.join(output_dir, "cover.pdf")

    # ── Copy spread to cover.png (without re-encoding) ──────────────────────────
    shutil.copy(cover_file, cover_png)

    # ── Wrap PNG into PDF ───────────────────────────────────────────────────────
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from cover_to_pdf import cover_png_to_pdf  # noqa: E402

    pdf_dims = cover_png_to_pdf(cover_png, cover_pdf, dpi=dpi)

    # ── Return results ──────────────────────────────────────────────────────────
    result = {
        "mode":           "simple",
        "cover_file":     cover_file,
        "cover_png":      cover_png,
        "cover_pdf":      cover_pdf,
        "output_dir":     output_dir,
        "niche":          niche,
        "book":           book,
        "date":           date,
        "expected_w_px":  expected_w_px,
        "expected_h_px":  expected_h_px,
        "actual_w_px":    art_w,
        "actual_h_px":    art_h,
        "unit":           unit,
        "cover_w":        cover_w,
        "cover_h":        cover_h,
        "dpi":            dpi,
        "pdf_dims":       pdf_dims,
    }

    return result


def build_cover_chain(
    front_png: str,
    niche: str,
    book: str = "book-1",
    date: str | None = None,
    pages: int = 110,
    trim_w_in: float = 7.5,
    trim_h_in: float = 9.25,
    paper: str = "white",
    title: str = "",
    bg_color: str = "#F2ECE3",
    data_root: str = "data",
    draw_guides: bool = False,
) -> dict:
    """
    Build a full KDP cover from front PNG (art with text already applied).

    :param front_png:   Path to front cover PNG (with text already rendered)
    :param niche:       Niche slug (e.g., "2026-06_snarky-notebook")
    :param book:        Book instance folder (e.g., "book-1")
    :param date:        ISO date (YYYY-MM-DD); None -> today
    :param pages:       Page count (for spine calculation)
    :param trim_w_in:   Trim width in inches
    :param trim_h_in:   Trim height in inches
    :param paper:       Paper type ("white", "cream", "color")
    :param title:       Title for spine text (cover_generator draws it on spine)
    :param bg_color:    Background color for back cover and bleed areas
    :param data_root:   Root directory for niche tree
    :param draw_guides: Whether to generate proof image with guides

    :returns: dict with paths to generated files and geometry info

    Raises FileNotFoundError if front_png does not exist.
    """
    # ── Validate input ─────────────────────────────────────────────────────────
    if not os.path.exists(front_png):
        raise FileNotFoundError(
            f"Front PNG not found: {front_png}\n"
            f"build_cover_chain requires an existing front image with text."
        )

    # ── Compute output directory ───────────────────────────────────────────────
    if date is None:
        date = datetime.date.today().isoformat()

    output_dir = os.path.join(data_root, "niches", niche, "output", date, book)
    os.makedirs(output_dir, exist_ok=True)

    # ── Paths ──────────────────────────────────────────────────────────────────
    cover_png = os.path.join(output_dir, "cover.png")
    cover_pdf = os.path.join(output_dir, "cover.pdf")
    cover_proof = os.path.join(output_dir, "cover_proof.png") if draw_guides else None

    # ── Step 1: Generate full cover spread (PNG) ───────────────────────────────
    # Import here to avoid circular dependencies
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from cover_generator import build_cover  # noqa: E402

    cover_dims = build_cover(
        out_path=cover_png,
        pages=pages,
        trim_w_in=trim_w_in,
        trim_h_in=trim_h_in,
        paper=paper,
        title=title,
        subtitle="",     # Text already on front_png, don't double-render
        author="",       # Text already on front_png, don't double-render
        bg_color=bg_color,
        front_image=front_png,
        draw_guides=draw_guides,
    )

    # ── Step 2: Wrap PNG into PDF ──────────────────────────────────────────────
    from cover_to_pdf import cover_png_to_pdf  # noqa: E402

    pdf_dims = cover_png_to_pdf(cover_png, cover_pdf, dpi=300)

    # ── Return results ─────────────────────────────────────────────────────────
    result = {
        "front_png":    front_png,
        "cover_png":    cover_png,
        "cover_pdf":    cover_pdf,
        "cover_proof":  cover_proof,
        "output_dir":   output_dir,
        "niche":        niche,
        "book":         book,
        "date":         date,
        "cover_dims":   cover_dims,
        "pdf_dims":     pdf_dims,
    }

    return result


if __name__ == "__main__":
    import argparse
    import yaml

    # ── CLI argument parsing ────────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="Build cover: simple mode (validate + wrap) or auto mode (generate)"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config.yaml (default: config.yaml in repo root)"
    )
    args = parser.parse_args()

    # ── Resolve config path ─────────────────────────────────────────────────────
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = args.config if os.path.isabs(args.config) else os.path.join(base, args.config)

    if not os.path.exists(config_path):
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)

    # ── Load config ─────────────────────────────────────────────────────────────
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Resolve cover_file path relative to repo base if not absolute
    if "cover_file" in config and not os.path.isabs(config["cover_file"]):
        config["cover_file"] = os.path.join(base, config["cover_file"])

    # Resolve data_root if not specified
    if "data_root" not in config:
        config["data_root"] = os.path.join(base, "data")

    # ── Run simple mode (wrap_validated_cover) ─────────────────────────────────
    print("=" * 70)
    print("wrap_validated_cover - Simple Mode")
    print("=" * 70)

    try:
        result = wrap_validated_cover(config)

        # Print results
        print(f"\nMode: {result['mode']}")
        print(f"\nInput:")
        print(f"  cover_file: {result['cover_file']}")
        print(f"\nExpected size:")
        print(f"  {result['cover_w']} x {result['cover_h']} {result['unit']} @ {result['dpi']} DPI")
        print(f"  = {result['expected_w_px']} x {result['expected_h_px']} px")
        print(f"\nActual size:")
        print(f"  {result['actual_w_px']} x {result['actual_h_px']} px")

        w_diff = result['actual_w_px'] - result['expected_w_px']
        h_diff = result['actual_h_px'] - result['expected_h_px']
        print(f"\nDelta:")
        print(f"  width:  {w_diff:+d} px")
        print(f"  height: {h_diff:+d} px")
        print(f"  Status: PASS (within ±1 px tolerance)")

        print(f"\nOutput directory:")
        print(f"  {result['output_dir']}")
        print(f"\nGenerated files:")
        print(f"  cover.png: {result['cover_png']}")
        print(f"  cover.pdf: {result['cover_pdf']}")

        pdf = result['pdf_dims']
        print(f"\nPDF dimensions:")
        print(f"  {pdf['w_px']} x {pdf['h_px']} px")
        print(f"  {pdf['page_w_pt']} x {pdf['page_h_pt']} pt")
        print(f"  {pdf['page_w_pt']/72:.4f} x {pdf['page_h_pt']/72:.4f} in")

        print("\n" + "=" * 70)
        print("Done.")

    except ValueError as e:
        print(f"\nERROR: {e}")
        print("\n" + "=" * 70)
        print("FAILED: Size mismatch")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("\n" + "=" * 70)
        print("FAILED: File not found")
        sys.exit(1)
