"""Convert all sample markdown files to DOCX, PDF, and HTML.

Usage:
    python samples/convert_all.py              # all formats, all samples
    python samples/convert_all.py --pdf-only   # PDF only
    python samples/convert_all.py --theme academic  # use academic theme

Each sample picks a sensible theme and watermark by default. Output lands in
samples/output/ alongside the source files.
"""
from __future__ import annotations

import argparse
import os
import sys

# Ensure the local markitup package is importable (not the PyPI one)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from markitup import MarkItUp
from markitup.theme import Theme, Running, Watermark, Banner

SAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SAMPLES_DIR, "output")

# Each sample gets a pre-configured look.
SAMPLES = {
    "academic-paper.md": {
        "theme": "academic",
        "header": Running(
            left="ACL Treatment Evaluation Study",
            center="CONFIDENTIAL — PEER REVIEW DRAFT",
            right="{page}",
            color="555555", size_pt=8.5, rule=True,
        ),
        "footer": Running(
            left="Anderson et al. — Five-Year Follow-up",
            center="",
            right="Page {page} of {pages}",
            color="555555", size_pt=8.5, rule=True,
        ),
        "watermark": Watermark(enabled=True, text="DRAFT", opacity=0.07, rotation=-45, color="999999"),
        "banner": Banner(text="PEER REVIEW DRAFT — NOT FOR DISTRIBUTION", color="FFFFFF", bg="B00020"),
    },
    "legal-contract.md": {
        "theme": "report",
        "header": Running(
            left="CONFIDENTIAL",
            center="Master Services Agreement — Upstride Labs & Acme Global",
            right="{page} / {pages}",
            color="888888", size_pt=8, rule=True,
        ),
        "footer": Running(
            left="MSA-2026-UPSTRIDE-ACME-001",
            center="",
            right="Execution Version",
            color="888888", size_pt=8, rule=True,
        ),
        "watermark": Watermark(enabled=True, text="CONFIDENTIAL", opacity=0.06, rotation=-45, color="BFBFBF"),
        "banner": None,
    },
    "technical-report.md": {
        "theme": "report",
        "header": Running(
            left="Upstride Labs — Engineering",
            center="CONFIDENTIAL — INTERNAL USE ONLY",
            right="{page} / {pages}",
            color="888888", size_pt=8.5, rule=True,
        ),
        "footer": Running(
            left="Cloud-Native Risk Pipeline — Technical Report",
            center="",
            right="TECH-REP-2026-001",
            color="888888", size_pt=8.5, rule=True,
        ),
        "watermark": Watermark(enabled=True, text="CONFIDENTIAL", opacity=0.06, rotation=-45, color="BFBFBF"),
        "banner": Banner(text="CONFIDENTIAL — INTERNAL USE ONLY", color="FFFFFF", bg="B00020"),
    },
    "business-proposal.md": {
        "theme": "report",
        "header": Running(
            left="Upstride Labs Limited",
            center="COMMERCIAL IN CONFIDENCE",
            right="{page} / {pages}",
            color="888888", size_pt=8.5, rule=True,
        ),
        "footer": Running(
            left="GAP Intelligent Document Platform — Phase 1 Proposal",
            center="",
            right="UPSTRIDE-GAP-2026-042",
            color="888888", size_pt=8.5, rule=True,
        ),
        "watermark": Watermark(enabled=True, text="COMMERCIAL IN CONFIDENCE", opacity=0.06, rotation=-45, color="BFBFBF"),
        "banner": Banner(text="COMMERCIAL IN CONFIDENCE", color="FFFFFF", bg="B00020"),
    },
}


def main():
    ap = argparse.ArgumentParser(description="Convert all sample markdown files")
    ap.add_argument("--pdf-only", action="store_true", help="Only generate PDFs")
    ap.add_argument("--docx-only", action="store_true", help="Only generate DOCX")
    ap.add_argument("--html-only", action="store_true", help="Only generate HTML")
    ap.add_argument("--theme", help="Override theme for all samples")
    ap.add_argument("--engine", default="weasyprint",
                    choices=["weasyprint", "chromium"],
                    help="PDF engine (default: weasyprint)")
    args = ap.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.docx_only:
        exts = ("docx",)
    elif args.pdf_only:
        exts = ("pdf",)
    elif args.html_only:
        exts = ("html",)
    else:
        exts = ("docx", "pdf", "html")

    for md_name, config in SAMPLES.items():
        md_path = os.path.join(SAMPLES_DIR, md_name)
        if not os.path.isfile(md_path):
            print(f"⚠  SKIP {md_name} — file not found")
            continue

        theme_name = args.theme or config["theme"]
        th = Theme.load(theme_name)

        # Apply the sample-specific look
        if config.get("header"):
            th.header = config["header"]
        if config.get("footer"):
            th.footer = config["footer"]
        if config.get("watermark"):
            th.watermark = config["watermark"]
        if config.get("banner") is not None:
            th.banner = config["banner"]

        m = MarkItUp(theme=th, pdf_engine=args.engine)

        stem = os.path.splitext(md_name)[0]
        for ext in exts:
            out = os.path.join(OUTPUT_DIR, f"{stem}.{ext}")
            try:
                m.convert(md_path, out)
                size_kb = os.path.getsize(out) / 1024
                print(f"✅ {stem}.{ext}  ({size_kb:.0f} KiB)")
            except Exception as e:
                print(f"❌ {stem}.{ext}  — {e}")

    print(f"\nDone — output in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
