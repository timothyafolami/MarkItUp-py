# MarkItUp

The reverse of Microsoft's **MarkItDown**: feed it Markdown, get back clean,
well-designed `.docx` and `.pdf` (and `.html`).

Unlike an LLM that "codes and executes" a document on every request, MarkItUp is
a **deterministic pipeline**. The same Markdown + same theme always produces the
same document. All design decisions are front-loaded into a theme, once — they
are never re-derived per document.

```
markdown ──parse──▶ IR ──render──┬──▶ .docx   (python-docx → OOXML)
                                 ├──▶ .html   (theme → CSS)
                                 └──▶ .pdf    (IR → themed HTML → print engine)
```

PDF uses a **pluggable engine**: `weasyprint` (pure-Python, default) or
`chromium` (headless, highest fidelity). Both consume the same HTML.

## Install

```bash
pip install markitup-py            # docx only (lightweight)
pip install "markitup-py[pdf]"     # + PDF and existing-file watermarking
```

The import name is `markitup`. PDF needs system libs for WeasyPrint
(pango, cairo, gdk-pixbuf).

## Quick start (Python)

```python
from markitup import MarkItUp

m = MarkItUp(theme="report")
m.convert("doc.md", "doc.pdf")
m.convert("doc.md")                 # -> ./doc.docx (current directory)
```

Configure once, convert many. Every knob overrides the theme:

```python
from markitup import MarkItUp, Watermark

m = MarkItUp(
    theme="report",
    body_font="Georgia",
    heading_font="Calibri",
    text_color="#222222",
    heading_color="#0B3D2E",
    heading_colors={1: "#0B3D2E", 2: "#1F6FEB"},   # per-level overrides
    accent_color="#1F6FEB",
    base_size=11, scale=1.2, line_height=1.45,
    page_size="A4", margin_cm=2.54,
    banner="CONFIDENTIAL — INTERNAL USE ONLY",
    watermark=Watermark(enabled=True, text="DRAFT", opacity=0.08, position="center"),
)
m.convert("doc.md", "doc.pdf")
```

## Fonts

DOCX stores font *names* and the reader substitutes what they have installed, so
prefer cross-platform families. PDF is rendered here, so a font must be installed
on this machine to appear.

```python
from markitup import list_fonts, is_available
info = list_fonts()
info["installed"]   # families available for PDF rendering on this machine
info["safe"]        # curated cross-platform families for .docx
is_available("Georgia")
```

```bash
markitup fonts
```

## Watermarks

A watermark is a theme token, applied identically to docx and PDF — text or image,
with `opacity`, `rotation`, `position` (`center`/`top`/`bottom`).

```python
m = MarkItUp(watermark={"text": "DRAFT", "opacity": 0.1, "rotation": -45})
m = MarkItUp(watermark={"image": "logo.png", "opacity": 0.12})
```

### Stamp an EXISTING file

Add a watermark to a `.pdf` or `.docx` you already have — no re-rendering. It's an
overlay/append, so the document's content is left intact.

```python
from markitup import stamp

stamp("report.pdf", "stamped.pdf", "CONFIDENTIAL",
      position="top", opacity=0.12, pages="1-3", behind=True)
stamp("report.docx", "stamped.docx", {"image": "logo.png", "opacity": 0.1})
# encrypted PDF: pass password=...
```

```bash
markitup stamp report.pdf -o stamped.pdf --watermark CONFIDENTIAL --position top
markitup stamp report.docx -o stamped.docx --watermark-image logo.png
```

Encrypted PDFs are refused unless you supply a password. Scanned/image PDFs are
fine — the overlay lands on top.

## Banners

A short notice rendered in-flow at the very top of a generated document:

```python
from markitup import Banner
m = MarkItUp(banner=Banner(text="RESTRICTED", color="#FFFFFF", bg="#B00020"))
```

## Templates (`base_docx`)

Hand MarkItUp a Word file you designed — brand fonts, colors, a header/footer with
your logo. It opens the file, clears the body, and maps your Markdown onto *its*
named styles. The template owns the design; Markdown just fills it. (This is the
Pandoc `reference.docx` model.)

```python
m = MarkItUp(base_docx="brand-template.docx")
m.convert("doc.md", "out.docx")
```

## CLI

```bash
markitup convert in.md -o out.pdf --theme report --font Georgia
markitup convert in.md --banner "CONFIDENTIAL" --watermark DRAFT
markitup fonts
markitup stamp in.pdf -o out.pdf --watermark "DO NOT COPY" --position bottom --pages 1-2
```

## Supported Markdown

Headings, paragraphs, **bold**/*italic*/~~strike~~/`code`, links, ordered &
unordered lists (nested), blockquotes, fenced code blocks, GFM tables (with
column alignment and clean wrapping), and thematic breaks.

## Architecture

| Module                    | Responsibility                                        |
|---------------------------|-------------------------------------------------------|
| `markitup/ir.py`          | Intermediate Representation — structure & intent only |
| `markitup/theme.py`       | Design tokens; computed type scale; watermark/banner  |
| `markitup/parse.py`       | markdown-it-py token stream → IR                       |
| `markitup/render_docx.py` | IR + Theme → `.docx`                                   |
| `markitup/render_html.py` | IR + Theme → HTML/CSS (PDF intermediate)              |
| `markitup/render_pdf.py`  | HTML → PDF (pluggable engine)                          |
| `markitup/stamp.py`       | Watermark existing `.pdf`/`.docx`                      |
| `markitup/fonts.py`       | Font discovery                                         |
| `markitup/api.py`         | The `MarkItUp` class                                   |
| `markitup/themes/*.yaml`  | Named themes                                           |

## License

MIT.
