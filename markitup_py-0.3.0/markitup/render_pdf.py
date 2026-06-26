"""IR + Theme -> PDF.

Architecture: IR -> themed HTML -> print engine. The engine is pluggable behind
one interface so you can trade fidelity for footprint:

  - "weasyprint": pure-Python, no browser binary. Great for document-style
    content; what we ship and test with here.
  - "chromium":  headless Chromium via Playwright. Highest fidelity (full CSS +
    JS). Recommended for production; drop-in once a browser is available.

Both consume the identical HTML from render_html, so output stays consistent.
"""
from __future__ import annotations

import os

from . import ir
from .render_html import render_html


def render_pdf(doc_ir: ir.Document, theme, out_path: str,
               engine: str = "weasyprint", base_url: str = ".") -> str:
    html = render_html(doc_ir, theme)
    if engine == "weasyprint":
        _weasyprint(html, out_path, base_url)
    elif engine == "chromium":
        _chromium(html, out_path, base_url)
    else:
        raise ValueError(f"unknown pdf engine: {engine!r}")
    return out_path


def _weasyprint(html: str, out_path: str, base_url: str):
    from weasyprint import HTML
    HTML(string=html, base_url=os.path.abspath(base_url)).write_pdf(out_path)


def _chromium(html: str, out_path: str, base_url: str):
    # Highest-fidelity path. Requires: pip install playwright && playwright install chromium
    from playwright.sync_api import sync_playwright

    abs_base = os.path.abspath(base_url)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        # let relative asset URLs resolve
        page.evaluate(f"document.head.insertAdjacentHTML('afterbegin', \"<base href='file://{abs_base}/'>\")")
        page.pdf(path=out_path, prefer_css_page_size=True, print_background=True)
        browser.close()
