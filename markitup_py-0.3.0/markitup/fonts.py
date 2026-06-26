"""Font discovery.

Two different realities to be honest about:

* **PDF** is rendered *here* (WeasyPrint/Chromium), so a font only works if it is
  installed on this machine. `available_fonts()` queries the system via
  fontconfig and tells you what will actually render.
* **DOCX** does not embed fonts by default — it stores a font *name* and Word
  substitutes whatever the reader has installed. So for docx, prefer widely
  available families. `SAFE_FONTS` lists cross-platform-safe choices.

`list_fonts()` returns both so callers can make an informed choice.
"""
from __future__ import annotations

import shutil
import subprocess
from typing import Dict, List

# Families that ship on virtually all Windows/macOS systems (safe for docx).
SAFE_FONTS: Dict[str, List[str]] = {
    "serif": ["Times New Roman", "Georgia", "Cambria", "Garamond", "Book Antiqua"],
    "sans": ["Calibri", "Arial", "Helvetica", "Verdana", "Tahoma", "Trebuchet MS", "Segoe UI"],
    "mono": ["Consolas", "Courier New", "Lucida Console"],
}


def available_fonts() -> List[str]:
    """Font families installed on THIS machine (what PDF rendering can use).
    Returns a sorted, de-duplicated list. Empty if fontconfig is unavailable."""
    if not shutil.which("fc-list"):
        return []
    try:
        out = subprocess.run(
            ["fc-list", ":", "family"], capture_output=True, text=True, timeout=10
        ).stdout
    except Exception:
        return []
    fams = set()
    for line in out.splitlines():
        # a line may list comma-separated localized aliases; take the first
        name = line.split(",")[0].strip()
        if name:
            fams.add(name)
    return sorted(fams, key=str.lower)


def list_fonts() -> Dict[str, object]:
    """Everything a caller needs to choose a font.

    Returns: {"installed": [...], "safe": {...}}
      - installed: families available for PDF rendering on this machine
      - safe: curated cross-platform families recommended for .docx
    """
    return {"installed": available_fonts(), "safe": SAFE_FONTS}


def is_available(family: str) -> bool:
    """True if `family` is installed locally (relevant for PDF)."""
    family_l = family.lower()
    return any(f.lower() == family_l for f in available_fonts())
