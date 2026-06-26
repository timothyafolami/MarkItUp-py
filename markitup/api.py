"""The public, configured entry point: the MarkItUp class.

Mirrors the ergonomics of Microsoft's MarkItDown — construct once with your
preferences, then convert many files:

    from markitup import MarkItUp, Watermark
    m = MarkItUp(theme="report", body_font="Georgia", text_color="#222")
    m.convert("doc.md", "doc.pdf")
    m.convert("doc.md")            # -> ./doc.docx (current working directory)

Every visual knob is optional and overrides the chosen theme.
"""
from __future__ import annotations

import os
from typing import Dict, Optional, Union

from .theme import Theme, Banner, Running, Watermark, make_watermark, norm_hex
from .parse import parse
from .render_docx import render as _render_docx
from .render_html import render_html as _render_html
from .render_pdf import render_pdf as _render_pdf
from . import stamp as _stamp_mod


class MarkItUp:
    def __init__(
        self,
        theme: Union[str, Theme] = "report",
        *,
        # fonts
        body_font: Optional[str] = None,
        heading_font: Optional[str] = None,
        mono_font: Optional[str] = None,
        # colors (accept '#RRGGBB' or 'RRGGBB')
        text_color: Optional[str] = None,
        heading_color: Optional[str] = None,
        heading_colors: Optional[Dict[int, str]] = None,
        accent_color: Optional[str] = None,
        link_color: Optional[str] = None,
        # type & page
        base_size: Optional[float] = None,
        line_height: Optional[float] = None,
        scale: Optional[float] = None,
        page_size: Optional[str] = None,
        margin_cm: Optional[float] = None,
        # structure & marks
        base_docx: Optional[str] = None,
        watermark: Union[Watermark, str, dict, None] = None,
        banner: Union[Banner, str, dict, None] = None,
        header: Union[Running, str, dict, None] = None,
        footer: Union[Running, str, dict, None] = None,
        confidential: bool = False,
        # pdf
        pdf_engine: str = "weasyprint",
    ):
        th = theme if isinstance(theme, Theme) else Theme.load(theme)

        if body_font:
            th.fonts.body = body_font
        if heading_font:
            th.fonts.heading = heading_font
        if mono_font:
            th.fonts.mono = mono_font

        if text_color:
            th.colors.text = norm_hex(text_color)
        if heading_color:
            th.colors.heading = norm_hex(heading_color)
        if accent_color:
            th.colors.accent = norm_hex(accent_color)
        if link_color:
            th.colors.link = norm_hex(link_color)
        if heading_colors:
            th.colors.headings.update({int(k): norm_hex(v) for k, v in heading_colors.items()})

        if base_size is not None:
            th.type.base_size = base_size
        if line_height is not None:
            th.type.line_height = line_height
        if scale is not None:
            th.type.ratio = scale
        if page_size:
            th.page.size = page_size
        if margin_cm is not None:
            th.page.margin_cm = margin_cm

        if base_docx:
            th.base_docx = base_docx
        if watermark is not None:
            th.watermark = make_watermark(watermark)
        if banner is not None:
            th.banner = _coerce_banner(banner)
        if header is not None:
            th.header = _coerce_running(header)
        if footer is not None:
            th.footer = _coerce_running(footer)
        # `confidential=True` is a shortcut: a muted CONFIDENTIAL header and a
        # page-number footer, only filling slots the caller didn't set.
        if confidential:
            if th.header is None:
                th.header = Running(center="CONFIDENTIAL", color="808080", size_pt=8.5)
            if th.footer is None:
                th.footer = Running(center="Page {page} of {pages}", color="808080", size_pt=8.5)

        self.theme = th
        self.pdf_engine = pdf_engine

    # ---- conversion -------------------------------------------------------
    def convert(self, input_path: str, output_path: Optional[str] = None,
                *, to: str = "docx") -> str:
        """Convert a markdown file. If `output_path` is omitted, the output is
        written to the current working directory as <input-stem>.<to>."""
        with open(input_path, "r", encoding="utf-8") as fh:
            md = fh.read()
        if output_path is None:
            stem = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(os.getcwd(), f"{stem}.{to.lstrip('.')}")
        base_url = os.path.dirname(os.path.abspath(input_path)) or "."
        return self.convert_text(md, output_path, base_url=base_url)

    def convert_text(self, markdown_text: str, output_path: str,
                     *, base_url: str = ".") -> str:
        """Convert a markdown string to the file at output_path (format from ext)."""
        doc = parse(markdown_text)
        ext = os.path.splitext(output_path)[1].lower()
        if ext == ".docx":
            return _render_docx(doc, self.theme, output_path)
        if ext == ".pdf":
            return _render_pdf(doc, self.theme, output_path,
                               engine=self.pdf_engine, base_url=base_url)
        if ext in (".html", ".htm"):
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(_render_html(doc, self.theme))
            return output_path
        raise ValueError(f"unsupported output extension: {ext!r}")

    # ---- existing-file watermarking --------------------------------------
    @staticmethod
    def stamp(input_path: str, output_path: str, watermark, **kwargs) -> str:
        """Watermark an existing .pdf/.docx. See markitup.stamp for options."""
        return _stamp_mod.stamp(input_path, output_path, watermark, **kwargs)


def _coerce_running(value) -> Optional[Running]:
    if value is None:
        return None
    if isinstance(value, Running):
        r = value
    elif isinstance(value, str):
        r = Running(center=value)       # a bare string becomes a centered caption
    elif isinstance(value, dict):
        r = Running(**value)
    else:
        raise TypeError(f"header/footer must be Running | str | dict | None, got {type(value)!r}")
    r.color = norm_hex(r.color)
    return r


def _coerce_banner(value) -> Optional[Banner]:
    if value is None:
        return None
    if isinstance(value, Banner):
        b = value
    elif isinstance(value, str):
        b = Banner(text=value)
    elif isinstance(value, dict):
        b = Banner(**value)
    else:
        raise TypeError(f"banner must be Banner | str | dict | None, got {type(value)!r}")
    b.color = norm_hex(b.color)
    if b.bg:
        b.bg = norm_hex(b.bg)
    return b
