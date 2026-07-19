"""Command-line interface: `markitup <command>`.

    markitup convert in.md -o out.pdf --theme report --font Georgia
    markitup convert in.md --banner "CONFIDENTIAL" --watermark DRAFT
    markitup fonts
    markitup stamp report.pdf -o stamped.pdf --watermark CONFIDENTIAL --position top
    markitup stamp report.docx -o stamped.docx --watermark-image logo.png

If the first argument is a file path (not a command), `convert` is assumed.
"""
from __future__ import annotations

import argparse
import os
import sys

from .api import MarkItUp
from .stamp import stamp as stamp_file
from .fonts import list_fonts

_COMMANDS = {"convert", "fonts", "stamp"}


def _add_style_args(p):
    p.add_argument("--theme", default="report", help="theme name or path to a theme .yaml")
    p.add_argument("--font", help="body font for the whole document")
    p.add_argument("--heading-font", help="font for headings")
    p.add_argument("--mono-font", help="font for code")
    p.add_argument("--text-color", help="body text color (#RRGGBB)")
    p.add_argument("--heading-color", help="heading color (#RRGGBB)")
    p.add_argument("--accent-color", help="accent color (#RRGGBB)")
    p.add_argument("--base-docx", help="reference .docx whose styles define the design")
    p.add_argument("--banner", help="top-of-document notice, e.g. CONFIDENTIAL")
    p.add_argument("--header", help="running page header text (centered), use {page}/{pages}")
    p.add_argument("--footer", help="running page footer text (centered), use {page}/{pages}")
    p.add_argument("--confidential", action="store_true",
                   help="add a CONFIDENTIAL header and page-number footer on every page")
    p.add_argument("--watermark", help="text watermark")
    p.add_argument("--watermark-image", help="image watermark (path)")
    p.add_argument("--position", default="center", choices=["center", "top", "bottom"])
    p.add_argument("--pdf-engine", default="weasyprint", choices=["weasyprint", "chromium"])


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in _COMMANDS and not argv[0].startswith("-"):
        argv = ["convert"] + argv  # default command

    ap = argparse.ArgumentParser(prog="markitup", description="Markdown -> docx/pdf/html")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("convert", help="convert a markdown file")
    c.add_argument("input", help="path to a .md file")
    c.add_argument("-o", "--output", help="output path (.docx/.pdf/.html); default: ./<name>.docx")
    c.add_argument("--to", default="docx", help="format when no -o given (docx/pdf/html)")
    _add_style_args(c)

    sub.add_parser("fonts", help="list fonts available for rendering")

    s = sub.add_parser("stamp", help="watermark an existing .pdf/.docx")
    s.add_argument("input", help="existing .pdf or .docx")
    s.add_argument("-o", "--output", required=True, help="output path")
    s.add_argument("--watermark", help="text watermark")
    s.add_argument("--watermark-image", help="image watermark (path)")
    s.add_argument("--position", default="center", choices=["center", "top", "bottom"])
    s.add_argument("--opacity", type=float, default=0.10)
    s.add_argument("--rotation", type=int, default=-45)
    s.add_argument("--pages", default="all", help="e.g. all | 1,3 | 2-5 (PDF only)")
    s.add_argument("--password", help="password for an encrypted PDF")
    s.add_argument("--in-front", action="store_true", help="draw over content instead of behind")

    args = ap.parse_args(argv)

    if args.cmd == "fonts":
        return _cmd_fonts()
    if args.cmd == "stamp":
        return _cmd_stamp(args)
    return _cmd_convert(args)


def _cmd_fonts():
    info = list_fonts()
    installed = info["installed"]
    print(f"Installed fonts available for PDF rendering ({len(installed)}):")
    for f in installed:
        print(f"  {f}")
    if not installed:
        print("  (fontconfig not available on this machine)")
    print("\nCross-platform-safe families recommended for .docx:")
    for group, fams in info["safe"].items():
        print(f"  {group:5}: {', '.join(fams)}")
    return 0


def _cmd_convert(args):
    if not os.path.isfile(args.input):
        print(f"input file not found: {args.input}", file=sys.stderr)
        return 2
    wm = None
    if args.watermark_image:
        wm = {"image": args.watermark_image, "position": args.position}
    elif args.watermark:
        wm = {"text": args.watermark, "position": args.position}
    m = MarkItUp(
        theme=args.theme,
        body_font=args.font, heading_font=args.heading_font, mono_font=args.mono_font,
        text_color=args.text_color, heading_color=args.heading_color, accent_color=args.accent_color,
        base_docx=args.base_docx, watermark=wm, banner=args.banner,
        header=args.header, footer=args.footer, confidential=args.confidential,
        pdf_engine=args.pdf_engine,
    )
    out = m.convert(args.input, args.output, to=args.to)
    print(f"Wrote {out}")
    return 0


def _cmd_stamp(args):
    if not os.path.isfile(args.input):
        print(f"input file not found: {args.input}", file=sys.stderr)
        return 2
    if args.watermark_image:
        wm = {"image": args.watermark_image}
    elif args.watermark:
        wm = {"text": args.watermark}
    else:
        print("provide --watermark or --watermark-image", file=sys.stderr)
        return 2
    wm.update({"position": args.position, "opacity": args.opacity, "rotation": args.rotation})
    out = stamp_file(args.input, args.output, wm,
                     password=args.password, behind=not args.in_front, pages=args.pages)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
