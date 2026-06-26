"""Stamp a watermark onto an EXISTING .pdf or .docx — no re-rendering.

This is an overlay/append operation, so we never have to understand the
document's content:

* **DOCX**: add the watermark shape to each section's page header (same VML used
  when generating). Existing body content is untouched.
* **PDF**: build a transparent overlay page with ReportLab and merge it onto each
  selected page with pypdf. `behind=True` keeps it under the text.

Controlled inputs: opacity, rotation, position, page selection, and (for
encrypted PDFs) a password. Encrypted PDFs without a password are refused.
"""
from __future__ import annotations

import io
import os
from typing import Iterable, Optional, Set

from .theme import Watermark, make_watermark, norm_hex


def stamp(input_path: str, output_path: str, watermark, *,
          password: Optional[str] = None, behind: bool = True,
          pages: str = "all", **overrides) -> str:
    """Watermark an existing .pdf/.docx. `watermark` may be a Watermark, a string
    (text), or a dict. Returns output_path."""
    wm = make_watermark(watermark, **overrides)
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".docx":
        _stamp_docx(input_path, output_path, wm)
    elif ext == ".pdf":
        _stamp_pdf(input_path, output_path, wm, password=password, behind=behind, pages=pages)
    else:
        raise ValueError(f"stamp supports .pdf and .docx, not {ext!r}")
    return output_path


# --- docx -------------------------------------------------------------------
def _stamp_docx(input_path: str, output_path: str, wm: Watermark) -> None:
    from docx import Document
    from .render_docx import _add_watermark  # reuse the generator's VML builder

    doc = Document(input_path)
    for section in doc.sections:
        _add_watermark(section, wm, "Calibri")
    doc.save(output_path)


# --- pdf --------------------------------------------------------------------
def _stamp_pdf(input_path: str, output_path: str, wm: Watermark, *,
               password: Optional[str], behind: bool, pages: str) -> None:
    from pypdf import PdfReader, PdfWriter, PageObject

    reader = PdfReader(input_path)
    if reader.is_encrypted:
        if password is None:
            raise ValueError("PDF is encrypted; pass password= to stamp it.")
        reader.decrypt(password)

    n = len(reader.pages)
    selected = _parse_pages(pages, n)
    writer = PdfWriter()

    for idx, page in enumerate(reader.pages):
        if idx in selected:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            overlay = PdfReader(_overlay(w, h, wm)).pages[0]
            if behind:
                base = PageObject.create_blank_page(width=w, height=h)
                base.merge_page(overlay)   # watermark first (under)
                base.merge_page(page)      # original content on top
                writer.add_page(base)
            else:
                page.merge_page(overlay)   # watermark on top
                writer.add_page(page)
        else:
            writer.add_page(page)

    with open(output_path, "wb") as fh:
        writer.write(fh)


def _overlay(width: float, height: float, wm: Watermark) -> io.BytesIO:
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase.pdfmetrics import stringWidth

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.saveState()
    c.setFillAlpha(wm.opacity)
    c.setStrokeAlpha(wm.opacity)

    cy = {"top": height * 0.85, "bottom": height * 0.15}.get(wm.position, height / 2)
    c.translate(width / 2, cy)
    c.rotate(wm.rotation)

    if wm.image:
        img = ImageReader(wm.image)
        iw, ih = img.getSize()
        scale = wm.width_pt / iw if iw else 1.0
        w, h = wm.width_pt, ih * scale
        c.drawImage(img, -w / 2, -h / 2, width=w, height=h, mask="auto")
    else:
        font = "Helvetica-Bold"
        size = 60.0
        tw = stringWidth(wm.text, font, size) or 1.0
        size = size * (wm.width_pt / tw)        # scale text to target width
        c.setFont(font, size)
        c.setFillColor(HexColor("#" + norm_hex(wm.color)))
        c.drawCentredString(0, -size * 0.33, wm.text)

    c.restoreState()
    c.showPage()
    c.save()
    buf.seek(0)
    return buf


def _parse_pages(pages: str, total: int) -> Set[int]:
    """'all' -> every page; otherwise 1-based list/ranges like '1,3,5-8' -> 0-based set."""
    if not pages or pages.strip().lower() == "all":
        return set(range(total))
    out: Set[int] = set()
    for part in pages.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            for p in range(int(a), int(b) + 1):
                if 1 <= p <= total:
                    out.add(p - 1)
        elif part:
            p = int(part)
            if 1 <= p <= total:
                out.add(p - 1)
    return out
