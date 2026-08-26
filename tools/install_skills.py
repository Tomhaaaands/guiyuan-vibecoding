#!/usr/bin/env python3
"""Install this repo's skills into the Codex skills directory.

Usage:
  python tools/install_skills.py [--force]

Behavior:
  Copies skills/iteration-close-loop and skills/project-bootstrap into
  $CODEX_HOME/skills (default ~/.codex/skills); skips existing skills, --force overwrites.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
SKILLS = ("iteration-close-loop", "project-bootstrap")


def main() -> None:
    ap = argparse.ArgumentParser(description="Install skills into the Codex skills directory")
    ap.add_argument("--force", action="store_true", help="overwrite existing skills")
    args = ap.parse_args()

    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    dest_root = home / "skills"
    dest_root.mkdir(parents=True, exist_ok=True)

    for name in SKILLS:
        src = ROOT / "skills" / name
        dst = dest_root / name
        if dst.exists() and not args.force:
            print(f"already installed, skipped: {name} (--force to overwrite)")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"installed: {dst}")
    print("done. In a new project's first conversation, invoke $project-bootstrap to start.")


if __name__ == "__main__":
    main()
