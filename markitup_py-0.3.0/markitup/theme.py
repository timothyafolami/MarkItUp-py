"""Theme = the single source of truth for every visual decision.

Design is front-loaded here, once, instead of being re-derived per document.
Both the docx and (future) pdf renderers read these tokens. Heading sizes are
*computed* from a base size and a modular ratio, which is why output looks
typographically harmonious rather than arbitrary.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional

import yaml


@dataclass
class Fonts:
    body: str = "Calibri"
    heading: str = "Calibri"
    mono: str = "Consolas"


@dataclass
class TypeScale:
    base_size: float = 11.0     # body size in points
    line_height: float = 1.45   # multiple of font size
    ratio: float = 1.25         # modular scale ratio for headings

    def heading_size(self, level: int) -> float:
        """h6==base, each step up multiplies by `ratio`.

        h1 is the largest. With base=11, ratio=1.25:
        h1≈26.9  h2≈21.5  h3≈17.2  h4≈13.75  h5≈11  h6≈11
        """
        steps = max(0, 6 - level)
        return round(self.base_size * (self.ratio ** steps), 1)


@dataclass
class Watermark:
    enabled: bool = False
    text: str = "DRAFT"
    image: Optional[str] = None  # path to an image; takes precedence over text
    opacity: float = 0.10        # 0..1
    rotation: int = -45          # degrees
    color: str = "BFBFBF"        # hex, no '#'
    width_pt: float = 400.0      # target width on the page (image or text box)
    position: str = "center"     # center | top | bottom


@dataclass
class Banner:
    """A short in-flow notice rendered at the very top of a generated document,
    e.g. CONFIDENTIAL or DRAFT — RESERVED."""
    text: str = ""
    color: str = "FFFFFF"
    bg: Optional[str] = "B00020"   # box background; None for plain text
    align: str = "center"          # left | center | right
    bold: bool = True
    size_pt: Optional[float] = None  # defaults to base_size * 1.1


@dataclass
class Page:
    size: str = "A4"            # A4 | LETTER
    margin_cm: float = 2.54


@dataclass
class Colors:
    text: str = "1A1A1A"
    heading: str = "000000"
    accent: str = "0B5D3B"
    rule: str = "DDDDDD"
    code_bg: str = "F6F8FA"
    code_text: str = "24292E"
    link: str = "0B5D3B"
    # Optional per-level heading color overrides, e.g. {1: "0B3D2E", 2: "555555"}.
    # Levels not listed fall back to `heading`.
    headings: Dict[int, str] = field(default_factory=dict)

    def heading_color(self, level: int) -> str:
        return self.headings.get(level, self.heading)


@dataclass
class Table:
    border_color: str = "000000"   # black
    border_width_pt: float = 0.5
    header_bg: str = "FFFFFF"      # white header
    header_text: str = "000000"    # black header text
    header_bold: bool = True
    body_text: str = "000000"      # black body text
    font_scale: float = 1.0        # multiply base size for table text


@dataclass
class Theme:
    name: str = "default"
    page: Page = field(default_factory=Page)
    fonts: Fonts = field(default_factory=Fonts)
    type: TypeScale = field(default_factory=TypeScale)
    colors: Colors = field(default_factory=Colors)
    table: Table = field(default_factory=Table)
    watermark: Watermark = field(default_factory=Watermark)
    banner: Optional[Banner] = None
    code_size: float = 9.5
    # Path to a .docx whose styles/branding/headers define the design. When set,
    # the docx renderer maps markdown onto THIS file's named styles (Pandoc-style
    # reference.docx). The template owns the look; markdown just fills it.
    base_docx: Optional[str] = None

    # ---- loading ----------------------------------------------------------
    @classmethod
    def from_dict(cls, d: Dict) -> "Theme":
        d = d or {}
        colors_d = dict(d.get("colors") or {})
        if "headings" in colors_d and colors_d["headings"]:
            colors_d["headings"] = {int(k): str(v) for k, v in colors_d["headings"].items()}
        banner_d = d.get("banner")
        return cls(
            name=d.get("name", "default"),
            page=Page(**(d.get("page") or {})),
            fonts=Fonts(**(d.get("fonts") or {})),
            type=TypeScale(**(d.get("type") or {})),
            colors=Colors(**colors_d),
            table=Table(**(d.get("table") or {})),
            watermark=Watermark(**(d.get("watermark") or {})),
            banner=Banner(**banner_d) if banner_d else None,
            code_size=d.get("code_size", 9.5),
            base_docx=d.get("base_docx"),
        )

    @classmethod
    def load(cls, name_or_path: str) -> "Theme":
        """Load by theme name (from bundled themes/) or by explicit file path."""
        if os.path.isfile(name_or_path):
            path = name_or_path
        else:
            here = os.path.dirname(__file__)
            path = os.path.join(here, "themes", f"{name_or_path}.yaml")
            if not os.path.isfile(path):
                raise FileNotFoundError(f"No theme named '{name_or_path}' at {path}")
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(yaml.safe_load(fh))


def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def norm_hex(value: Optional[str]) -> Optional[str]:
    """Accept '#RRGGBB' or 'RRGGBB'; return 'RRGGBB' (no hash)."""
    return value.lstrip("#").upper() if value else value


def make_watermark(value, **overrides) -> Watermark:
    """Coerce a flexible user value into a Watermark.

    `value` may be a Watermark, a string (treated as watermark text), a dict of
    fields, or None. `overrides` (image=, opacity=, rotation=, color=, position=,
    width_pt=) are applied when not None.
    """
    if value is None:
        wm = Watermark()
    elif isinstance(value, Watermark):
        wm = value
    elif isinstance(value, str):
        wm = Watermark(enabled=True, text=value)
    elif isinstance(value, dict):
        wm = Watermark(**value)
        wm.enabled = True
    else:
        raise TypeError(f"watermark must be Watermark | str | dict | None, got {type(value)!r}")
    for k, v in overrides.items():
        if v is not None:
            setattr(wm, k, v)
    if "color" in overrides and overrides["color"]:
        wm.color = norm_hex(wm.color)
    if value is not None:
        wm.enabled = True
    return wm
