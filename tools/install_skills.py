#!/usr/bin/env python3
"""Install this repo's skills into the Codex skills directory, and self-check the kit.

Usage:
  python tools/install_skills.py [--force]   # install the two skills
  python tools/install_skills.py --doctor    # verify install + repo health (no writes)

Behavior:
  Copies skills/iteration-close-loop and skills/project-bootstrap into
  $CODEX_HOME/skills (default ~/.codex/skills); skips existing skills, --force overwrites.
  --doctor prints the kit version, checks both skills are installed intact, and runs
  tools/check_drift.py to prove the distribution is healthy.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
SKILLS = ("iteration-close-loop", "project-bootstrap", "vibe-coding-install")
VERSION_FILE = ROOT / "VERSION"


def version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "unknown"


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def doctor() -> int:
    home = codex_home()
    skills_root = home / "skills"
    print(f"VibeCoding_Manager v{version()} · doctor")
    ok = True
    for name in SKILLS:
        sk = skills_root / name / "SKILL.md"
        if sk.is_file():
            print(f"  [ok] skill installed: {name}")
        else:
            print(f"  [missing] skill not installed: {name} (run: python tools/install_skills.py)")
            ok = False
    rc = subprocess.run([sys.executable, str(ROOT / "tools" / "check_drift.py")], cwd=ROOT).returncode
    if rc == 0:
        print("  [ok] check_drift passed (repo is healthy)")
    else:
        print("  [fail] check_drift failed — fix before distributing")
        ok = False
    print("doctor " + ("passed" if ok else "found issues"))
    return 0 if ok else 1


def install(force: bool) -> None:
    dest_root = codex_home() / "skills"
    dest_root.mkdir(parents=True, exist_ok=True)
    for name in SKILLS:
        src = ROOT / "skills" / name
        dst = dest_root / name
        if dst.exists() and not force:
            print(f"already installed, skipped: {name} (--force to overwrite)")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"installed: {dst}")
    print(f"VibeCoding_Manager v{version()} installed.")
    print("next: open a NEW empty project folder, start a new conversation, invoke $project-bootstrap.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Install VibeCoding_Manager skills and self-check the kit")
    ap.add_argument("--force", action="store_true", help="overwrite existing skills")
    ap.add_argument("--doctor", action="store_true", help="verify install + repo health (no writes)")
    args = ap.parse_args()
    if args.doctor:
        sys.exit(doctor())
    install(args.force)


if __name__ == "__main__":
    main()
