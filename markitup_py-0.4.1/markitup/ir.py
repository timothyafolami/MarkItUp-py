"""Intermediate Representation (IR) for MarkItUp.

The IR is the contract between parsing and rendering. The parser produces a tree
of these nodes from markdown; every renderer (docx, pdf, ...) consumes the same
tree. Nodes carry *structure and intent only* — never visual styling. All visual
decisions live in the Theme.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# --- base -------------------------------------------------------------------
class Node:
    """Marker base class for all IR nodes."""


# --- inline nodes -----------------------------------------------------------
@dataclass
class Text(Node):
    content: str


@dataclass
class Strong(Node):
    children: List[Node] = field(default_factory=list)


@dataclass
class Emphasis(Node):
    children: List[Node] = field(default_factory=list)


@dataclass
class Strike(Node):
    children: List[Node] = field(default_factory=list)


@dataclass
class InlineCode(Node):
    content: str


@dataclass
class Link(Node):
    href: str
    children: List[Node] = field(default_factory=list)


@dataclass
class Image(Node):
    src: str
    alt: str = ""


@dataclass
class LineBreak(Node):
    pass


# --- block nodes ------------------------------------------------------------
@dataclass
class Heading(Node):
    level: int                      # 1..6
    children: List[Node] = field(default_factory=list)


@dataclass
class Paragraph(Node):
    children: List[Node] = field(default_factory=list)


@dataclass
class CodeBlock(Node):
    content: str
    lang: Optional[str] = None


@dataclass
class BlockQuote(Node):
    children: List[Node] = field(default_factory=list)


@dataclass
class ListItem(Node):
    children: List[Node] = field(default_factory=list)


@dataclass
class ListNode(Node):
    ordered: bool = False
    start: int = 1
    items: List[ListItem] = field(default_factory=list)


@dataclass
class TableCell(Node):
    children: List[Node] = field(default_factory=list)
    align: str = "left"            # left | center | right


@dataclass
class TableRow(Node):
    cells: List[TableCell] = field(default_factory=list)


@dataclass
class Table(Node):
    header: Optional[TableRow] = None
    rows: List[TableRow] = field(default_factory=list)


@dataclass
class ThematicBreak(Node):
    pass


@dataclass
class Document(Node):
    children: List[Node] = field(default_factory=list)
    title: Optional[str] = None     # populated from first H1 if present
