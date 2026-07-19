"""Markdown -> IR.

markdown-it-py emits a *flat* token stream (``*_open`` / ``*_close`` pairs and
self-closing tokens). This module walks that stream into the nested IR tree.
We use the ``gfm-like`` preset so tables, strikethrough and autolinks work.
"""
from __future__ import annotations

from typing import List, Optional

from markdown_it import MarkdownIt

from . import ir


def parse(text: str) -> ir.Document:
    # commonmark + GFM tables and strikethrough, without linkify (no extra dep).
    md = MarkdownIt("commonmark").enable("table").enable("strikethrough")
    tokens = md.parse(text)
    p = _Walker(tokens)
    doc = ir.Document(children=p.blocks_until(None))
    for c in doc.children:
        if isinstance(c, ir.Heading) and c.level == 1:
            doc.title = _plain_text(c.children)
            break
    return doc


class _Walker:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0

    # ---- block level ------------------------------------------------------
    def blocks_until(self, close_type: Optional[str]) -> List[ir.Node]:
        out: List[ir.Node] = []
        while self.i < len(self.toks):
            t = self.toks[self.i]
            if close_type and t.type == close_type:
                self.i += 1
                return out
            node = self.block()
            if node is not None:
                out.append(node)
        return out

    def block(self) -> Optional[ir.Node]:
        t = self.toks[self.i]
        ty = t.type
        if ty == "heading_open":
            level = int(t.tag[1])
            self.i += 1
            children = self.inline()
            self._expect("heading_close")
            return ir.Heading(level=level, children=children)
        if ty == "paragraph_open":
            self.i += 1
            children = self.inline()
            self._expect("paragraph_close")
            return ir.Paragraph(children=children)
        if ty in ("fence", "code_block"):
            self.i += 1
            lang = (t.info.strip() or None) if getattr(t, "info", "") else None
            return ir.CodeBlock(content=t.content.rstrip("\n"), lang=lang)
        if ty in ("bullet_list_open", "ordered_list_open"):
            return self._list()
        if ty == "blockquote_open":
            self.i += 1
            return ir.BlockQuote(children=self.blocks_until("blockquote_close"))
        if ty == "hr":
            self.i += 1
            return ir.ThematicBreak()
        if ty == "table_open":
            return self._table()
        # unknown / html_block / etc -> skip safely
        self.i += 1
        return None

    def _list(self) -> ir.ListNode:
        t = self.toks[self.i]
        ordered = t.type == "ordered_list_open"
        start = 1
        if ordered:
            s = t.attrGet("start")
            if s:
                start = int(s)
        self.i += 1
        close = "ordered_list_close" if ordered else "bullet_list_close"
        items: List[ir.ListItem] = []
        while self.i < len(self.toks) and self.toks[self.i].type != close:
            if self.toks[self.i].type == "list_item_open":
                self.i += 1
                items.append(ir.ListItem(children=self.blocks_until("list_item_close")))
            else:
                self.i += 1
        self._expect(close)
        return ir.ListNode(ordered=ordered, start=start, items=items)

    def _table(self) -> ir.Table:
        self.i += 1  # table_open
        header: Optional[ir.TableRow] = None
        rows: List[ir.TableRow] = []
        while self.i < len(self.toks) and self.toks[self.i].type != "table_close":
            ty = self.toks[self.i].type
            if ty == "thead_open":
                self.i += 1
                while self.toks[self.i].type != "thead_close":
                    if self.toks[self.i].type == "tr_open":
                        header = self._row()
                    else:
                        self.i += 1
                self.i += 1  # thead_close
            elif ty == "tbody_open":
                self.i += 1
                while self.toks[self.i].type != "tbody_close":
                    if self.toks[self.i].type == "tr_open":
                        rows.append(self._row())
                    else:
                        self.i += 1
                self.i += 1  # tbody_close
            else:
                self.i += 1
        self._expect("table_close")
        return ir.Table(header=header, rows=rows)

    def _row(self) -> ir.TableRow:
        self.i += 1  # tr_open
        cells: List[ir.TableCell] = []
        while self.toks[self.i].type != "tr_close":
            t = self.toks[self.i]
            if t.type in ("th_open", "td_open"):
                style = t.attrGet("style") or ""
                align = "center" if "center" in style else "right" if "right" in style else "left"
                self.i += 1
                children = self.inline()
                self._expect(t.type.replace("_open", "_close"))
                cells.append(ir.TableCell(children=children, align=align))
            else:
                self.i += 1
        self._expect("tr_close")
        return ir.TableRow(cells=cells)

    # ---- inline level -----------------------------------------------------
    def inline(self) -> List[ir.Node]:
        if self.i >= len(self.toks) or self.toks[self.i].type != "inline":
            return []
        t = self.toks[self.i]
        self.i += 1
        return _inline_children(t.children or [], [0], None)

    # ---- helpers ----------------------------------------------------------
    def _expect(self, ty: str) -> None:
        if self.i < len(self.toks) and self.toks[self.i].type == ty:
            self.i += 1


def _inline_children(toks, pos, close_type) -> List[ir.Node]:
    out: List[ir.Node] = []
    while pos[0] < len(toks):
        t = toks[pos[0]]
        if close_type and t.type == close_type:
            pos[0] += 1
            return out
        pos[0] += 1
        ty = t.type
        if ty == "text":
            out.append(ir.Text(t.content))
        elif ty == "code_inline":
            out.append(ir.InlineCode(t.content))
        elif ty == "softbreak":
            out.append(ir.Text(" "))
        elif ty == "hardbreak":
            out.append(ir.LineBreak())
        elif ty == "strong_open":
            out.append(ir.Strong(_inline_children(toks, pos, "strong_close")))
        elif ty == "em_open":
            out.append(ir.Emphasis(_inline_children(toks, pos, "em_close")))
        elif ty == "s_open":
            out.append(ir.Strike(_inline_children(toks, pos, "s_close")))
        elif ty == "link_open":
            href = t.attrGet("href") or ""
            out.append(ir.Link(href=href, children=_inline_children(toks, pos, "link_close")))
        elif ty == "image":
            out.append(ir.Image(src=t.attrGet("src") or "", alt=t.content or ""))
        # unknown inline tokens are ignored
    return out


def _plain_text(nodes) -> str:
    parts = []
    for n in nodes:
        if isinstance(n, (ir.Text, ir.InlineCode)):
            parts.append(n.content)
        elif hasattr(n, "children"):
            parts.append(_plain_text(n.children))
    return "".join(parts).strip()
