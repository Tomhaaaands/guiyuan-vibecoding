#!/usr/bin/env python3
"""Install this repo's skills into a user-chosen skills root, and self-check the kit.

Usage:
  python tools/install_skills.py [--skills-dir PATH] [--force]
  python tools/install_skills.py --doctor [--skills-dir PATH]
  python tools/install_skills.py --discover

Behavior:
  Copies skills/iteration-close-loop and skills/vibe-coding-manager into
  the explicit --skills-dir, VIBECODING_SKILLS_HOME, or the Codex fallback;
  skips existing skills, --force overwrites.
  --doctor prints the kit version, checks both skills are installed intact, and runs
  tools/check_drift.py to prove the distribution is healthy.
  --discover lists known agent skill roots read-only without writing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
SKILLS = ("iteration-close-loop", "vibe-coding-manager", "vibe-coding-install")
VERSION_FILE = ROOT / "VERSION"


def version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "unknown"


def resolve_skills_root(skills_dir: str | None) -> Path:
    if skills_dir:
        return Path(skills_dir).expanduser().resolve()
    env = os.environ.get("VIBECODING_SKILLS_HOME")
    if env:
        return Path(env).expanduser().resolve()
    codex = os.environ.get("CODEX_HOME", Path.home() / ".codex")
    return Path(codex).expanduser() / "skills"


def discover() -> None:
    candidates = [
        ("Codex", resolve_skills_root(None)),
        ("Claude Code", Path.home() / ".claude" / "skills"),
        ("Cursor", Path.home() / ".cursor" / "skills"),
    ]
    print("== known agent skill roots (read-only, not exhaustive) ==")
    found = False
    for label, root in candidates:
        print(f"  {label}: {root} ({'exists' if root.exists() else 'not found'})")
        found = found or root.exists()
    if not found:
        print("  none found; use --skills-dir <path> for an explicit global directory")
    else:
        print("  confirm one path with --skills-dir <path> before writing")


def doctor(skills_root: Path) -> int:
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


def install(force: bool, dest_root: Path) -> None:
    dest_root.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = dest_root / ".vibecoding-manager-backups" / stamp
    backed_up = []
    for name in SKILLS:
        src = ROOT / "skills" / name
        dst = dest_root / name
        if dst.exists() and not force:
            print(f"already installed, skipped: {name} (--force to overwrite)")
            continue
        if dst.exists():
            backup = backup_root / name
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(dst, backup)
            backed_up.append(name)
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"installed: {dst}")
    if backed_up:
        print(f"backup: {backup_root} ({', '.join(backed_up)})")
    print(f"VibeCoding_Manager v{version()} installed.")
    print("next: open your project folder (empty or existing), start a new conversation, invoke $vibe-coding-manager.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Install VibeCoding_Manager skills and self-check the kit")
    ap.add_argument("--force", action="store_true", help="overwrite existing skills")
    ap.add_argument("--doctor", action="store_true", help="verify install + repo health (no writes)")
    ap.add_argument("--skills-dir", default=None, help="explicit global skills root")
    ap.add_argument("--discover", action="store_true", help="list known agent skill roots read-only")
    args = ap.parse_args()
    if args.discover:
        discover()
        return
    dest_root = resolve_skills_root(args.skills_dir)
    print(f"skills root: {dest_root}")
    if args.doctor:
        sys.exit(doctor(dest_root))
    install(args.force, dest_root)


if __name__ == "__main__":
    main()
