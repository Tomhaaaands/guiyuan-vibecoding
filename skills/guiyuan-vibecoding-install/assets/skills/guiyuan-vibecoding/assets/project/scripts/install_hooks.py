#!/usr/bin/env python3
"""Install the Guiyuan Vibecoding pre-commit gate into .git/hooks (idempotent).

Usage:
  python scripts/install_hooks.py

Every commit then runs `tools/git_safety_gate.py` followed by `tools/check_drift.py`; a failing
check blocks the commit (Git's `--no-verify` remains an explicit emergency escape hatch).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "hooks" / "pre-commit"
DST = ROOT / ".git" / "hooks" / "pre-commit"


def main() -> int:
    if not DST.parent.exists():
        print("[gate] no .git directory - run `git init` first")
        return 1
    if not SRC.exists():
        print(f"[gate] hook source missing: {SRC}")
        return 1
    shutil.copy2(SRC, DST)
    print(f"[gate] pre-commit installed: {DST}")
    print("       every commit runs staged safety + drift checks (bypass: git commit --no-verify)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
