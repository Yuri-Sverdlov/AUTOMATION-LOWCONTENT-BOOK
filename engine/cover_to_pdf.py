"""
engine/cover_to_pdf.py

Wraps a KDP cover PNG into a single-page PDF at exact physical dimensions.
Task: tasks/TASK.md (2026-06-05).

DPI is taken as a parameter — PNG metadata is not trusted (integer dots/meter
rounding in the PNG spec causes 300 DPI to read back as 299.9994).

Dependency: reportlab (already in requirements.txt), Pillow
"""

import os
from PIL import Image
from reportlab.pdfgen import canvas

PT_PER_INCH = 72.0


def cover_png_to_pdf(
    png_path: str,
    pdf_out: str,
    dpi: int = 300,
) -> dict:
    """
    Wrap a cover PNG into a single-page PDF.

    The PDF page size is derived from the PNG pixel dimensions and dpi so that
    the physical size matches exactly.  The image fills the page edge-to-edge
    with no margins.

    Returns a dict with computed values for logging and verification.
    """
    img = Image.open(png_path)
    w_px, h_px = img.size

    page_w_pt = w_px / dpi * PT_PER_INCH
    page_h_pt = h_px / dpi * PT_PER_INCH

    os.makedirs(os.path.dirname(os.path.abspath(pdf_out)), exist_ok=True)

    c = canvas.Canvas(pdf_out, pagesize=(page_w_pt, page_h_pt))
    # drawImage places the image with (0,0) at the reportlab origin (bottom-left).
    # width/height = page size → image fills the page edge-to-edge, no resampling.
    c.drawImage(png_path, 0, 0, width=page_w_pt, height=page_h_pt)
    c.showPage()
    c.save()

    return {
        "w_px":      w_px,
        "h_px":      h_px,
        "dpi":       dpi,
        "page_w_pt": round(page_w_pt, 4),
        "page_h_pt": round(page_h_pt, 4),
    }


if __name__ == "__main__":
    import sys
    import os

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    png_path = os.path.join(base, "output", "cover_test.png")

    if not os.path.exists(png_path):
        sys.path.insert(0, os.path.join(base, "engine"))
        from cover_generator import build_cover
        build_cover(png_path, title="Test Notebook")

    pdf_out = os.path.join(base, "output", "cover_test.pdf")
    dims = cover_png_to_pdf(png_path, pdf_out)
    print(f"Done: {pdf_out}")
    print(f"  w_px={dims['w_px']}, h_px={dims['h_px']}, dpi={dims['dpi']}")
    print(f"  MediaBox: {dims['page_w_pt']} x {dims['page_h_pt']} pt")
