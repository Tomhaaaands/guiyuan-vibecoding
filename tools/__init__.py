"""Guiyuan Vibecoding tool packages with legacy import compatibility."""
from __future__ import annotations

import sys
from pathlib import Path

_TOOLS_ROOT = str(Path(__file__).resolve().parent)
if _TOOLS_ROOT not in sys.path:
    sys.path.insert(0, _TOOLS_ROOT)
