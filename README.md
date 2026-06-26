# MarkItUp

[![PyPI version](https://img.shields.io/pypi/v/markitup-py?color=blue)](https://pypi.org/project/markitup-py/)
[![PyPI downloads](https://img.shields.io/pypi/dm/markitup-py?color=blue)](https://pypi.org/project/markitup-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/markitup-py)](https://pypi.org/project/markitup-py/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/upstridelabs/markitup/actions/workflows/ci.yml/badge.svg)](https://github.com/upstridelabs/markitup/actions/workflows/ci.yml)

The reverse of Microsoft's **MarkItDown**: feed it Markdown, get back clean,
well-designed `.docx`, `.pdf`, and `.html` — with running headers, footers,
watermarks, and banners that repeat across every page.

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

---

## Install

```bash
pip install markitup-py                # docx only (lightweight)
pip install "markitup-py[pdf]"         # + PDF and existing-file watermarking
pip install "markitup-py[all]"         # everything including Chromium engine
```

The import name is `markitup`. PDF via WeasyPrint needs system libs (pango, cairo, gdk-pixbuf); see [WeasyPrint docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html).

---

## Quick start (Python)

```python
from markitup import MarkItUp

m = MarkItUp(theme="report")
m.convert("doc.md", "doc.pdf")
m.convert("doc.md")                    # -> ./doc.docx (current directory)
```

### With headers, footers, watermark, and banner

```python
from markitup import MarkItUp
from markitup.theme import Theme, Running, Watermark, Banner

th = Theme.load("report")

# Running header on every page — left/center/right with {page}/{pages}
th.header = Running(
    left="Upstride Labs Limited",
    center="CONFIDENTIAL — INTERNAL USE ONLY",
    right="{page} / {pages}",
    color="888888", size_pt=8.5, rule=True,
)

# Running footer with a divider line
th.footer = Running(
    left="Confidential",
    center="Upstride Labs  |  Lagos  |  upstridelabs.com",
    right="Page {page} of {pages}",
    color="888888", size_pt=8.5, rule=True,
)

# Watermark on every page (text or image)
th.watermark = Watermark(
    enabled=True, text="DRAFT",
    opacity=0.08, rotation=-45, position="center",
)

# In-flow banner at the top of the first page
th.banner = Banner(text="RESTRICTED", color="#FFFFFF", bg="#B00020")

MarkItUp(theme=th).convert("doc.md", "doc.docx")
```

### Per-document overrides

Every knob overrides the theme, so you can set defaults in the theme and
override per document:

```python
m = MarkItUp(
    theme="report",
    body_font="Georgia",
    heading_font="Times New Roman",
    text_color="#222222",
    heading_color="#0B3D2E",
    heading_colors={1: "#0B3D2E", 2: "#1F6FEB"},
    accent_color="#1F6FEB",
    base_size=11, scale=1.2, line_height=1.45,
    page_size="A4", margin_cm=2.54,
)
m.convert("doc.md", "doc.pdf")
```

---

## Themes

| Theme | Body Font | Heading Font | Best For |
|---|---|---|---|
| `report` (default) | Georgia | Calibri | Business reports, general documents |
| `academic` | Times New Roman | Times New Roman | Journal papers, theses, dissertations |

Themes live in YAML files under `markitup/themes/`. You can point to your own:

```python
MarkItUp(theme="path/to/my-theme.yaml")
```

Example custom theme:

```yaml
name: my-brand
page:
  size: LETTER
  margin_cm: 2.0
fonts:
  body: "Palatino Linotype"
  heading: "Garamond"
  mono: "Source Code Pro"
type:
  base_size: 11.5
  line_height: 1.5
  ratio: 1.25
colors:
  text: "222222"
  heading: "0B3D2E"
  accent: "1F6FEB"
  code_bg: "F6F8FA"
table:
  border_color: "000000"
  border_width_pt: 0.5
watermark:
  enabled: true
  text: "DRAFT"
  opacity: 0.08
  rotation: -45
```

---

## Fonts

DOCX stores font *names* and the reader substitutes what they have installed, so
prefer cross-platform families. PDF is rendered here, so a font must be installed
on this machine to appear.

```python
from markitup import list_fonts, is_available, SAFE_FONTS

info = list_fonts()
info["installed"]   # families available for PDF rendering on this machine
info["safe"]        # curated cross-platform families grouped by category:
                    #   serif, sans, mono, academic, modern, typewriter

is_available("Times New Roman")       # True if installed locally

# SAFE_FONTS["academic"] = ["Times New Roman", "Computer Modern", "Palatino Linotype", "Garamond"]
```

```bash
markitup fonts
```

### Quick font picks by use case

| Use Case | Recommended Body Font | Heading Font | Mono Font |
|---|---|---|---|
| Academic paper | Times New Roman | Times New Roman | Courier New |
| Business report | Georgia | Calibri | Consolas |
| Legal document | Times New Roman | Times New Roman | Courier New |
| Technical doc | Segoe UI | Calibri | Consolas |
| Modern / clean | Helvetica | Helvetica | Menlo |
| Traditional | Garamond | Garamond | Courier New |

---

## Running Headers & Footers

Every page can carry a running header and/or footer with:

- **Left / center / right** text slots
- **`{page}`** and **`{pages}`** placeholders for page numbering
- **Rule lines** (a divider under the header or above the footer)
- Configurable **font**, **size**, and **color**

Headers and footers work in **all three output formats** — DOCX (via native
OOXML headers/footers), HTML (via `@page` margin boxes + `position: fixed`
rules), and PDF (same HTML consumed by WeasyPrint or Chromium).

```python
from markitup.theme import Running

theme.header = Running(
    left="Document Title",
    center="CONFIDENTIAL",
    right="Page {page} of {pages}",
    color="888888",      # grey, subtle
    size_pt=8.5,
    rule=True,           # divider line under the header
)
```

---

## Watermarks

A watermark is a theme token, applied to every page of DOCX, PDF, and HTML
output — text or image, with `opacity`, `rotation`, and `position`.

```python
m = MarkItUp(watermark={"text": "DRAFT", "opacity": 0.1, "rotation": -45})
m = MarkItUp(watermark={"image": "logo.png", "opacity": 0.12})
```

### Stamp an EXISTING file

Add a watermark to a `.pdf` or `.docx` you already have — no re-rendering:

```python
from markitup import stamp

stamp("report.pdf", "stamped.pdf", "CONFIDENTIAL",
      position="top", opacity=0.12, pages="all", behind=True)
stamp("report.docx", "stamped.docx", {"image": "logo.png", "opacity": 0.1})
```

```bash
markitup stamp report.pdf -o stamped.pdf --watermark CONFIDENTIAL --position top
markitup stamp report.docx -o stamped.docx --watermark-image logo.png
```

---

## Banners

A short notice rendered in-flow at the very top of the first page:

```python
from markitup import Banner
m = MarkItUp(banner=Banner(text="RESTRICTED", color="#FFFFFF", bg="#B00020"))
m = MarkItUp(banner="CONFIDENTIAL — INTERNAL USE ONLY")  # string shortcut
```

---

## Templates (`base_docx`)

Hand MarkItUp a Word file you designed — brand fonts, colors, a header/footer
with your logo. It opens the file, clears the body, and maps your Markdown onto
*its* named styles. (This is the Pandoc `reference.docx` model.)

```python
m = MarkItUp(base_docx="brand-template.docx")
m.convert("doc.md", "out.docx")
```

---

## CLI

```bash
markitup convert in.md -o out.pdf --theme report --font Georgia
markitup convert in.md --banner "CONFIDENTIAL" --watermark DRAFT
markitup fonts
markitup stamp in.pdf -o out.pdf --watermark "DO NOT COPY" --position bottom
```

---

## Supported Markdown

Headings, paragraphs, **bold**/*italic*/~~strike~~/`code`, links, ordered &
unordered lists (nested), blockquotes, fenced code blocks (with language
classes), GFM tables (with column alignment and clean wrapping), images, and
thematic breaks.

---

## Samples

The `samples/` directory contains detailed example Markdown files and a
conversion script:

```
samples/
├── academic-paper.md       # 20+ page medical journal article with tables
├── legal-contract.md       # Full Master Services Agreement
├── technical-report.md     # Engineering architecture & performance report
├── business-proposal.md    # Enterprise digital transformation proposal
├── sample.ipynb            # Jupyter notebook
└── convert_all.py          # Convert all samples to DOCX/PDF/HTML at once
```

```bash
# Convert all samples to DOCX + PDF + HTML
python samples/convert_all.py

# Use the academic theme (Times New Roman, traditional formatting)
python samples/convert_all.py --theme academic

# PDF only with Chromium
python samples/convert_all.py --pdf-only --engine chromium

# DOCX only
python samples/convert_all.py --docx-only
```

Each sample is pre-configured with appropriate headers, footers, watermarks,
and banners — open `convert_all.py` to see how each look is assembled.

---

## Architecture

| Module                    | Responsibility                                        |
|---------------------------|-------------------------------------------------------|
| `markitup/ir.py`          | Intermediate Representation — structure & intent only |
| `markitup/theme.py`       | Design tokens; computed type scale; watermark/banner  |
| `markitup/parse.py`       | markdown-it-py token stream → IR                       |
| `markitup/render_docx.py` | IR + Theme → `.docx` (OOXML headers, watermarks)      |
| `markitup/render_html.py` | IR + Theme → HTML/CSS (@page margin boxes, rules)     |
| `markitup/render_pdf.py`  | HTML → PDF (pluggable engine: WeasyPrint / Chromium)  |
| `markitup/stamp.py`       | Watermark existing `.pdf`/`.docx`                      |
| `markitup/fonts.py`       | Font discovery + curated cross-platform family lists  |
| `markitup/api.py`         | The `MarkItUp` class                                   |
| `markitup/themes/*.yaml`  | Named themes (report, academic)                        |

---

## License

MIT.
