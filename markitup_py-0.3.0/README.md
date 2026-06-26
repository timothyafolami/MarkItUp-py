# MarkItUp

The reverse of Microsoft's **MarkItDown**: feed it markdown, get back clean,
well-designed `.docx` (and, soon, `.pdf`).

Unlike an LLM that "codes and executes" a document on every request, MarkItUp is
a **deterministic pipeline**. The same markdown + same theme always produces the
same document. All design decisions are front-loaded into a theme, once — they
are never re-derived per document.

```
markdown ──parse──▶ IR ──render──┬──▶ .docx   (python-docx → OOXML)
                                 ├──▶ .html   (theme → CSS)
                                 └──▶ .pdf    (IR → themed HTML → print engine)
```

PDF uses a **pluggable engine**: `weasyprint` (pure-Python, default) or
`chromium` (headless, highest fidelity — `pip install playwright && playwright
install chromium`). Both consume the same HTML, so output stays consistent.

## Architecture

| Module            | Responsibility                                              |
|-------------------|-------------------------------------------------------------|
| `markitup/ir.py`        | Intermediate Representation — structure & intent only |
| `markitup/theme.py`     | Design tokens; heading sizes computed from a modular scale |
| `markitup/parse.py`     | markdown-it-py token stream → IR                     |
| `markitup/render_docx.py` | IR + Theme → `.docx`                              |
| `markitup/themes/*.yaml`  | Named themes (e.g. `report`)                       |

The IR is the contract: add a new renderer (PDF, HTML) without touching the
parser; add a new theme without touching any code.

## Why design lives in the theme

A theme is the single source of truth for every visual decision. Heading sizes
aren't guessed — they're computed as `base_size * ratio^(6 - level)`, which is
why the output looks typographically harmonious. Watermarks, draft stamps, fonts,
colors, and margins are all tokens, applied identically by every renderer.

## Install

```bash
pip install -r requirements.txt
```

## Usage

CLI (output format is inferred from the extension):

```bash
python -m markitup.cli examples/sample.md -o out.docx --theme report
python -m markitup.cli examples/sample.md -o out.pdf  --watermark CONFIDENTIAL
python -m markitup.cli examples/sample.md -o out.docx --watermark-image logo.png
python -m markitup.cli examples/sample.md -o out.docx --base-docx brand.docx
python -m markitup.cli examples/sample.md -o out.pdf  --pdf-engine chromium
```

Library:

```python
import markitup
markitup.convert(open("doc.md").read(), "doc.docx", theme="report")
markitup.convert(open("doc.md").read(), "doc.pdf",  theme="report")
```

## Templates and watermarks

**Templates** (`--base-docx` / `theme.base_docx`): hand MarkItUp a Word file you
designed — brand fonts, colors, a header/footer with your logo. It opens the
file, clears the body, and maps your markdown onto *its* named styles. The
template owns the design; markdown just fills it. (This is the Pandoc
`reference.docx` model.)

**Watermarks** are theme tokens, applied identically to docx and PDF:

- Text: `watermark.text` (or `--watermark DRAFT`).
- Image: `watermark.image` (or `--watermark-image logo.png`) — in docx this is
  the canonical Word header watermark with washout; in PDF it's a faded,
  per-page fixed image.

## Supported markdown

Headings, paragraphs, **bold**/*italic*/~~strike~~/`code`, links, ordered &
unordered lists (nested), blockquotes, fenced code blocks, GFM tables (with
column alignment), and thematic breaks.

## Roadmap

1. **More themes** — `letter`, `memo`, `article`.
2. **Inline images** — embed local/remote images in docx (PDF already does).
3. **Chromium engine** — wire the high-fidelity PDF path for production.
4. **Service shell** — `/render` API, async queue, object storage, idempotency.
