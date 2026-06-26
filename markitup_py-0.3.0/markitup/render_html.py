"""IR + Theme -> HTML/CSS.

This is the shared intermediate for the PDF path (and a useful output on its
own). The CSS is generated from the *same* theme tokens the docx renderer uses,
so docx and PDF stay visually in sync. Page geometry, the type scale, code,
tables and the watermark are all emitted from tokens — never hand-tuned here.
"""
from __future__ import annotations

from html import escape

from . import ir


def render_html(doc_ir: ir.Document, theme) -> str:
    css = _css(theme)
    body = "".join(_block(b, theme) for b in doc_ir.children)
    wm = _watermark(theme.watermark)
    banner = _banner(theme.banner)
    title = escape(doc_ir.title or "Document")
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{title}</title><style>{css}</style></head>"
        f"<body>{wm}{banner}{body}</body></html>"
    )


def _banner(b) -> str:
    if not b or not b.text:
        return ""
    bg = f"background:#{b.bg};" if b.bg else ""
    pad = "padding:6px 10px;" if b.bg else ""
    weight = "bold" if b.bold else "normal"
    size = f"{b.size_pt}pt" if b.size_pt else "1.1em"
    return (
        f"<div class='banner' style='text-align:{b.align};color:#{b.color};{bg}{pad}"
        f"font-weight:{weight};font-size:{size};margin:0 0 1em;'>{escape(b.text)}</div>"
    )


# --- CSS from tokens --------------------------------------------------------
def _css(t) -> str:
    c = t.colors
    page_size = "letter" if t.page.size.upper() == "LETTER" else "A4"
    heads = "\n".join(
        f"h{lvl}{{font-size:{t.type.heading_size(lvl)}pt;color:#{c.heading_color(lvl)};}}"
        for lvl in range(1, 7)
    )
    return f"""
@page {{
  size: {page_size};
  margin: {t.page.margin_cm}cm;
  @bottom-center {{
    content: counter(page);
    font-family: "{t.fonts.body}"; font-size: 9pt; color: #{c.text};
  }}
}}
* {{ box-sizing: border-box; }}
body {{
  font-family: "{t.fonts.body}", serif;
  font-size: {t.type.base_size}pt;
  line-height: {t.type.line_height};
  color: #{c.text};
  margin: 0;
}}
h1,h2,h3,h4,h5,h6 {{
  font-family: "{t.fonts.heading}", sans-serif;
  color: #{c.heading};
  line-height: 1.2;
  margin: 0.8em 0 0.3em;
  page-break-after: avoid;
}}
{heads}
p {{ margin: 0 0 0.6em; }}
a {{ color: #{c.link}; text-decoration: underline; }}
code {{
  font-family: "{t.fonts.mono}", monospace;
  font-size: {t.code_size}pt;
  background: #{c.code_bg}; color: #{c.code_text};
  padding: 0.1em 0.3em; border-radius: 3px;
}}
pre {{
  background: #{c.code_bg}; color: #{c.code_text};
  padding: 10px 12px; border-radius: 5px;
  overflow-x: auto; line-height: 1.4;
  page-break-inside: avoid;
}}
pre code {{ background: none; padding: 0; font-size: {t.code_size}pt; }}
blockquote {{
  margin: 0 0 0.6em; padding: 0.2em 0 0.2em 1em;
  border-left: 3px solid #{c.accent};
  color: #{c.text}; font-style: italic;
}}
ul,ol {{ margin: 0 0 0.6em 1.4em; padding: 0; }}
li {{ margin: 0.15em 0; }}
table {{
  border-collapse: collapse; width: 100%;
  table-layout: fixed;                       /* equal columns; wrap instead of overflow */
  margin: 0 0 0.8em;
  font-size: {t.type.base_size * t.table.font_scale:.1f}pt;
  page-break-inside: avoid;
}}
th,td {{
  border: {t.table.border_width_pt}pt solid #{t.table.border_color};
  padding: 5px 7px; vertical-align: top;
  overflow-wrap: break-word; hyphens: auto;
}}
th {{ background: #{t.table.header_bg}; color: #{t.table.header_text};
     {"font-weight: bold;" if t.table.header_bold else "font-weight: normal;"} }}
td {{ color: #{t.table.body_text}; }}
hr {{ border: none; border-top: 1px solid #{c.rule}; margin: 1em 0; }}
img {{ max-width: 100%; }}
.watermark {{
  position: fixed; top: {("12%" if t.watermark.position == "top" else "88%" if t.watermark.position == "bottom" else "50%")}; left: 50%;
  transform: translate(-50%, -50%) rotate({t.watermark.rotation}deg);
  opacity: {t.watermark.opacity}; z-index: -1; pointer-events: none;
  text-align: center;
}}
.watermark-text {{
  font-family: "{t.fonts.heading}", sans-serif; font-weight: bold;
  font-size: {t.watermark.width_pt * 0.22:.0f}pt; color: #{t.watermark.color};
  white-space: nowrap;
}}
.watermark img {{ width: {t.watermark.width_pt}pt; }}
""".strip()


def _watermark(wm) -> str:
    if not wm.enabled:
        return ""
    if wm.image:
        return f"<div class='watermark'><img src='{escape(wm.image)}' alt=''></div>"
    return f"<div class='watermark'><div class='watermark-text'>{escape(wm.text)}</div></div>"


# --- block + inline ---------------------------------------------------------
def _block(n, t) -> str:
    if isinstance(n, ir.Heading):
        lvl = min(n.level, 6)
        return f"<h{lvl}>{_inline(n.children)}</h{lvl}>"
    if isinstance(n, ir.Paragraph):
        return f"<p>{_inline(n.children)}</p>"
    if isinstance(n, ir.CodeBlock):
        cls = f" class='language-{escape(n.lang)}'" if n.lang else ""
        return f"<pre><code{cls}>{escape(n.content)}</code></pre>"
    if isinstance(n, ir.BlockQuote):
        return "<blockquote>" + "".join(_block(c, t) for c in n.children) + "</blockquote>"
    if isinstance(n, ir.ListNode):
        tag = "ol" if n.ordered else "ul"
        start = f" start='{n.start}'" if n.ordered and n.start != 1 else ""
        items = "".join(
            "<li>" + "".join(_li_child(c, t) for c in it.children) + "</li>" for it in n.items
        )
        return f"<{tag}{start}>{items}</{tag}>"
    if isinstance(n, ir.Table):
        return _table(n, t)
    if isinstance(n, ir.ThematicBreak):
        return "<hr>"
    return ""


def _li_child(c, t) -> str:
    # tighten: a list item's leading paragraph renders inline (no <p> wrapper)
    if isinstance(c, ir.Paragraph):
        return _inline(c.children)
    return _block(c, t)


def _table(n, t) -> str:
    out = ["<table>"]
    if n.header:
        out.append("<thead><tr>")
        for cell in n.header.cells:
            out.append(f"<th style='text-align:{cell.align}'>{_inline(cell.children)}</th>")
        out.append("</tr></thead>")
    out.append("<tbody>")
    for row in n.rows:
        out.append("<tr>")
        for cell in row.cells:
            out.append(f"<td style='text-align:{cell.align}'>{_inline(cell.children)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def _inline(nodes) -> str:
    out = []
    for n in nodes:
        if isinstance(n, ir.Text):
            out.append(escape(n.content))
        elif isinstance(n, ir.LineBreak):
            out.append("<br>")
        elif isinstance(n, ir.InlineCode):
            out.append(f"<code>{escape(n.content)}</code>")
        elif isinstance(n, ir.Strong):
            out.append(f"<strong>{_inline(n.children)}</strong>")
        elif isinstance(n, ir.Emphasis):
            out.append(f"<em>{_inline(n.children)}</em>")
        elif isinstance(n, ir.Strike):
            out.append(f"<s>{_inline(n.children)}</s>")
        elif isinstance(n, ir.Link):
            out.append(f"<a href='{escape(n.href)}'>{_inline(n.children)}</a>")
        elif isinstance(n, ir.Image):
            out.append(f"<img src='{escape(n.src)}' alt='{escape(n.alt)}'>")
    return "".join(out)
