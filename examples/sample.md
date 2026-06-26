# MarkItUp Demo Report

This document exercises the full feature set of the **MarkItUp** renderer. It is
generated from plain markdown, with all styling supplied by the *report* theme.

## Inline formatting

You can use **bold**, *italic*, ***bold italic***, ~~strikethrough~~, `inline code`,
and [links](https://example.com) anywhere in a paragraph.

## Lists

Unordered, with nesting:

- First item
- Second item
  - Nested item A
  - Nested item B
- Third item

Ordered:

1. Clarify constraints
2. Reason from first principles
3. Commit to a design

## A blockquote

> Design is front-loaded into themes, once — not re-derived per document.
> That is what makes the output deterministic.

## Code

Here is a fenced code block:

```python
def convert(md: str, out: str, theme: str = "report") -> str:
    doc = parse(md)
    return render_docx(doc, Theme.load(theme), out)
```

## A table

| Format | Strategy            | Engine            |
|:-------|:--------------------|:------------------|
| docx   | IR -> OOXML         | python-docx       |
| pdf    | IR -> HTML -> print | headless Chromium |

---

That horizontal rule above is a thematic break.
