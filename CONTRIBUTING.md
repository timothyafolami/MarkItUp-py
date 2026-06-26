# Contributing

Thanks for contributing to MarkItUp. Here's how to get set up.

## Setup

```bash
git clone https://github.com/upstridelabs/markitup.git
cd markitup
pip install -e ".[all]"    # editable install with all extras
```

## Architecture

```
markdown ──parse──▶ IR ──render──┬──▶ .docx   (render_docx.py)
                                 ├──▶ .html   (render_html.py)
                                 └──▶ .pdf    (render_pdf.py → WeasyPrint or Chromium)
```

| Module | Responsibility |
|---|---|
| `ir.py` | Intermediate Representation — structure & intent, no styling |
| `theme.py` | Design tokens, type scale, watermark/banner models |
| `parse.py` | markdown-it-py token stream → IR |
| `render_docx.py` | IR + Theme → OOXML via python-docx |
| `render_html.py` | IR + Theme → themed HTML/CSS |
| `render_pdf.py` | HTML → PDF via pluggable engine |
| `stamp.py` | Watermark existing PDFs/DOCX without re-rendering |
| `fonts.py` | Cross-platform font discovery and curated family lists |

## Adding a theme

Create a YAML file in `markitup/themes/`. It's loaded automatically:

```yaml
name: my-theme
fonts:
  body: "Garamond"
  heading: "Garamond"
  mono: "Courier New"
# ... all fields are optional; missing ones fall back to defaults in theme.py
```

## Adding a sample

Drop a `.md` file in `samples/` and add its config to `samples/convert_all.py`.

## Running the sample converter

```bash
python samples/convert_all.py              # all formats
python samples/convert_all.py --docx-only  # just DOCX
python samples/convert_all.py --theme academic
```

## Before submitting

- Test DOCX, HTML, and PDF (at least one engine) for any rendering changes
- Use `ruff check markitup/` if you have it installed
- Follow the existing code style — match the docstrings, naming, and structure

## Release process (maintainers)

1. Bump version in `pyproject.toml` and `markitup/__init__.py`
2. Update `CHANGELOG.md`
3. Build: `python -m build`
4. Publish: `twine upload dist/*`
5. Tag: `git tag v0.X.Y && git push --tags`
