# Changelog

## 0.3.2 (2026-06-26)

- Added `academic` theme — Times New Roman body/headings, Courier New mono
- Expanded `SAFE_FONTS` with 30+ families across 6 categories (serif, sans, mono, academic, modern, typewriter)
- Added `samples/` directory with 4 detailed sample markdowns covering academic, legal, technical, and business use cases
- Added `samples/convert_all.py` for batch conversion of all samples
- Updated README with comprehensive examples for headers, footers, watermarks, banners, and fonts
- Added font quick-pick table for common use cases

## 0.3.1 (2026-06-26)

- Fixed watermark only being applied to the first DOCX section — now covers all sections
- Fixed HTML/PDF `@page` margin box rules not being emitted for running headers and footers
- Fixed missing CSS for header/footer rule divider lines
- Added automatic page counter fallback when footer does not include `{page}`
- Removed unused `_margin_boxes` helper

## 0.3.0 (2026-06-25)

- Running headers and footers with left/center/right slots, `{page}`/`{pages}` fields, and rule lines
- Watermark support for DOCX, HTML, and PDF (text or image, with opacity, rotation, and position)
- In-flow banner rendering at the top of generated documents
- `Banner`, `Running`, and `Watermark` data classes in the theme model
- DOCX renderer: OOXML page fields, tab-stop-based 3-part header/footer layout, VML watermarks
- HTML renderer: themed CSS, `@page` margin boxes, fixed-position rule divs
- PDF renderer: pluggable engine (WeasyPrint + Chromium/Playwright)

## 0.2.0 (2026-06-20)

- Initial PyPI release
- Markdown → DOCX, HTML, PDF pipeline
- Theme system with YAML configuration
- Computed modular type scale for headings
- GFM tables, fenced code blocks, nested lists, blockquotes
- CLI: `markitup convert`, `markitup fonts`, `markitup stamp`
- `stamp` command for watermarking existing PDFs and DOCX files
