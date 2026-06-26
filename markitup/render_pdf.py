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
    """Highest-fidelity path via headless Chromium.

    Requires: pip install playwright && playwright install chromium

    Runs the Playwright *sync* API inside a dedicated worker thread. This is the
    key to working inside Jupyter/IPython: notebooks already run an asyncio event
    loop on the main thread, and Playwright's sync API refuses to start there
    ("Sync API inside the asyncio loop"). A fresh thread has no running loop, so
    it works in notebooks and plain scripts alike.
    """
    abs_base = os.path.abspath(base_url).rstrip("/")
    base_href = f"file://{abs_base}/"
    # Inject <base> up front so relative images/watermarks resolve before load.
    if "<head>" in html:
        prepared = html.replace("<head>", f"<head><base href=\"{base_href}\">", 1)
    else:
        prepared = f'<base href="{base_href}">' + html

    result = {}

    def _work():
        try:
            try:
                from playwright.sync_api import sync_playwright
            except ImportError as e:
                raise RuntimeError(
                    "The 'chromium' PDF engine needs Playwright. Install it with:\n"
                    "    pip install playwright\n"
                    "    playwright install chromium"
                ) from e
            try:
                with sync_playwright() as pw:
                    browser = pw.chromium.launch()
                    try:
                        page = browser.new_page()
                        page.set_content(prepared, wait_until="networkidle")
                        page.emulate_media(media="print")  # apply @page / print CSS
                        page.pdf(path=out_path, prefer_css_page_size=True, print_background=True)
                    finally:
                        browser.close()
            except Exception as e:
                msg = str(e)
                if "Executable doesn't exist" in msg or "playwright install" in msg:
                    raise RuntimeError(
                        "Chromium browser is not installed for Playwright. Run:\n"
                        "    playwright install chromium"
                    ) from e
                raise
        except BaseException as e:  # capture to re-raise on caller thread
            result["error"] = e

    import threading
    t = threading.Thread(target=_work, daemon=True)
    t.start()
    t.join()
    if "error" in result:
        raise result["error"]
