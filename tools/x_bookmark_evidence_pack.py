#!/usr/bin/env python3
"""CLI wrapper for X Bookmark Evidence Pack."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from x_bookmark_tools.evidence_pack import main


if __name__ == "__main__":
    raise SystemExit(main())
