"""MarkItUp — markdown -> docx/pdf/html, the reverse of Microsoft's MarkItDown.

Quick start:

    from markitup import MarkItUp
    MarkItUp(theme="report").convert("doc.md", "doc.pdf")

Pipeline:  markdown --parse--> IR --render--> .docx / .pdf / .html
All visual decisions live in a Theme; the renderers are mechanical.
"""
import os

from .api import MarkItUp
from .theme import Theme, Watermark, Banner, Running, Table, make_watermark
from .parse import parse
from .render_docx import render as render_docx
from .render_html import render_html
from .render_pdf import render_pdf
from .stamp import stamp
from .fonts import list_fonts, available_fonts, is_available, SAFE_FONTS

__version__ = "0.4.1"
__all__ = [
    "MarkItUp", "Theme", "Watermark", "Banner", "Running", "Table",
    "parse", "render_docx", "render_html", "render_pdf",
    "stamp", "convert", "make_watermark",
    "list_fonts", "available_fonts", "is_available", "SAFE_FONTS",
]


def convert(markdown_text: str, out_path: str, theme="report",
            base_url: str = ".", pdf_engine: str = "weasyprint") -> str:
    """One-shot helper: markdown string -> file (format from extension)."""
    doc = parse(markdown_text)
    th = theme if isinstance(theme, Theme) else Theme.load(theme)
    ext = os.path.splitext(out_path)[1].lower()
    if ext == ".docx":
        return render_docx(doc, th, out_path)
    if ext == ".pdf":
        return render_pdf(doc, th, out_path, engine=pdf_engine, base_url=base_url)
    if ext in (".html", ".htm"):
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(render_html(doc, th))
        return out_path
    raise ValueError(f"unsupported output extension: {ext!r}")
