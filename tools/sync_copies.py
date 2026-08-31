#!/usr/bin/env python3
"""Propagate source-of-truth files to their distribution payload copies.

The kit ships several self-contained payload copies: the manager skill carries a project
template (assets/project) and a close-loop copy (assets/skills/iteration-close-loop); the
install skill bundles both skills (assets/skills/*) so it can install/update from inside
Codex. check_drift detects drift; this script fixes it by copying source -> payload for the
same SYNC_PAIRS (imported from check_drift to keep one definition), plus the version file.

Usage:
  python tools/sync_copies.py            # propagate source -> payloads, then run check_drift
  python tools/sync_copies.py --dry-run  # show what would change, change nothing (exit 1 if dirty)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from check_drift import BUNDLED_VERSION, ROOT, SYNC_PAIRS, VERSION_FILE


def _sync_tree(src: Path, dst: Path, dry_run: bool) -> list[str]:
    """Mirror src into dst (files only): copy changed/missing, remove files absent in src."""
    actions: list[str] = []
    if not src.is_dir():
        return actions
    src_files = {
        p.relative_to(src)
        for p in src.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }
    dst_files = {
        p.relative_to(dst)
        for p in dst.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }
    for rel in sorted(src_files | dst_files):
        sp, dp = src / rel, dst / rel
        if rel not in dst_files:
            actions.append(f"  + {rel.as_posix()}")
        elif rel not in src_files:
            actions.append(f"  - {rel.as_posix()}  (removed from {dst.name})")
        elif sp.read_bytes() != dp.read_bytes():
            actions.append(f"  ~ {rel.as_posix()}")
    if dry_run:
        return actions
    for rel in sorted(src_files - dst_files):
        dp = dst / rel
        dp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, dp)
    for rel in sorted(dst_files - src_files):
        (dst / rel).unlink()
    for rel in sorted(src_files & dst_files):
        sp, dp = src / rel, dst / rel
        if sp.read_bytes() != dp.read_bytes():
            dp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sp, dp)
    return actions


def _sync_version(dry_run: bool) -> list[str]:
    if not VERSION_FILE.is_file():
        return ["  [version] missing root VERSION; cannot sync"]
    if BUNDLED_VERSION.is_file() and BUNDLED_VERSION.read_text(encoding="utf-8").strip() == VERSION_FILE.read_text(encoding="utf-8").strip():
        return []
    if not dry_run:
        BUNDLED_VERSION.write_text(VERSION_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    return ["  [version] root VERSION -> skills/vibe-coding-install/VERSION"]


def main() -> None:
    ap = argparse.ArgumentParser(description="Propagate source-of-truth files to distribution payload copies")
    ap.add_argument("--dry-run", action="store_true", help="show what would change, change nothing")
    args = ap.parse_args()

    changed = 0
    for src, dst in SYNC_PAIRS:
        label = f"{src.relative_to(ROOT).as_posix()} -> {dst.relative_to(ROOT).as_posix()}"
        actions = _sync_tree(src, dst, args.dry_run)
        if actions:
            print(f"== {label} ==")
            for a in actions:
                print(a)
            changed += len(actions)
        else:
            print(f"[ok] {label}")
    va = _sync_version(args.dry_run)
    for a in va:
        print(a)
    changed += len(va)

    if args.dry_run:
        print(f"\n{changed} item(s) out of sync; run `python tools/sync_copies.py` to apply.")
        sys.exit(1 if changed else 0)
    if changed:
        print(f"\n{changed} item(s) updated; run `python tools/check_drift.py` to verify.")
        sys.exit(1)
    print("\nall distribution copies in sync ✓")


if __name__ == "__main__":
    main()
