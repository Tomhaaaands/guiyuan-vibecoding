#!/usr/bin/env python3
"""Doc-rot prevention: scan stale markers + validate llms.txt links.

Usage:
  python tools/check_drift.py            # full scan (markers + llms.txt links)
  python tools/check_drift.py --markers  # markers only
  python tools/check_drift.py --links    # llms.txt links only

Stale-marker levels:
  - hard (fails): `[OUTDATED]`, TODO, TBD, FIXME;
  - soft (warn only): 待补 / 待补充 (usually intentional placeholder wording; human judgment).
Teaching files that explain these markers are skipped to avoid false positives.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
DOCS = ROOT / "docs"
LLMS = ROOT / "llms.txt"
SKIP_PARTS = {"archive", "_archive"}
SYNC_PAIRS = (
    (ROOT / "templates" / "iteration-methodology",
     ROOT / "skills" / "project-bootstrap" / "assets" / "project"),
    (ROOT / "skills" / "iteration-close-loop",
     ROOT / "skills" / "project-bootstrap" / "assets" / "skills" / "iteration-close-loop"),
    (ROOT / "skills" / "iteration-close-loop",
     ROOT / "skills" / "vibe-coding-install" / "assets" / "skills" / "iteration-close-loop"),
    (ROOT / "skills" / "project-bootstrap",
     ROOT / "skills" / "vibe-coding-install" / "assets" / "skills" / "project-bootstrap"),
)
SKIP_FILES = {
    "docs/04-workflow/review-checklist.md",
    "docs/04-workflow/product-update-protocol.md",
    "docs/04-workflow/iteration-methodology.md",
    "docs/04-workflow/AGENTS_WORKFLOW.md",
    "docs/iteration-methodology.md",
}
STALE_RE = re.compile(r"\[OUTDATED\]|\bTODO\b|\bTBD\b|\bFIXME\b")
SOFT_RE = re.compile(r"待补(?:充)?")
LINK_RE = re.compile(r"\]\(([^)#]+?)\)")


def _files():
    return [p for p in DOCS.rglob("*.md") if not any(part in SKIP_PARTS for part in p.parts)]


def check_markers() -> tuple[int, int]:
    hard = 0
    soft = 0
    for p in _files():
        rel = p.relative_to(ROOT).as_posix()
        if rel in SKIP_FILES:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if STALE_RE.search(line):
                print(f"  [marker] {rel}:{i}: {line.strip()[:100]}")
                hard += 1
            elif SOFT_RE.search(line):
                print(f"  [warn] {rel}:{i}: {line.strip()[:100]}")
                soft += 1
    return hard, soft


def check_links() -> int:
    if not LLMS.exists():
        print("  [info] no llms.txt; skipping link check (run tools/gen_llms_txt.py to generate)")
        return 0
    found = 0
    for i, line in enumerate(LLMS.read_text(encoding="utf-8").splitlines(), 1):
        for target in LINK_RE.findall(line):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = (ROOT / target).resolve()
            if not path.exists():
                print(f"  [link] llms.txt:{i}: missing link -> {target}")
                found += 1
    return found


def _relative_map(root: Path) -> dict[str, str]:
    """Return {relative_posix_path: sha256} for every file under root."""
    out: dict[str, str] = {}
    if not root.is_dir():
        return out
    for p in root.rglob("*"):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def check_sync() -> int:
    """Distribution sync gate: the template and its asset copies must stay identical."""
    issues = 0
    for a, b in SYNC_PAIRS:
        if not a.exists() and not b.exists():
            print(f"  [skip] sync pair not present here: {a.name} <-> {b.name}")
            continue
        ma, mb = _relative_map(a), _relative_map(b)
        label_a, label_b = a.name, b.name
        for rel in sorted(set(ma) | set(mb)):
            if rel not in ma:
                print(f"  [sync] missing in {label_a}: {rel}")
                issues += 1
            elif rel not in mb:
                print(f"  [sync] missing in {label_b}: {rel}")
                issues += 1
            elif ma[rel] != mb[rel]:
                print(f"  [sync] differs: {rel} ({label_a} vs {label_b})")
                issues += 1
    if issues:
        print("  [fail] template/asset copies are out of sync")
    else:
        print("  [ok] template + asset copies are in sync")
    return issues


def main() -> None:
    ap = argparse.ArgumentParser(description="Scan doc stale markers and llms.txt link validity")
    ap.add_argument("--markers", action="store_true", help="markers only")
    ap.add_argument("--links", action="store_true", help="llms.txt links only")
    args = ap.parse_args()

    do_markers = args.markers or not args.links
    do_links = args.links or not args.markers
    do_sync = not (args.markers or args.links)
    total = 0
    if do_markers:
        print("== stale-marker scan ==")
        hard, soft = check_markers()
        total += hard
        print(f"  hard {hard} / soft {soft} (soft markers are informational, not blocking)")
    if do_links:
        print("== llms.txt link check ==")
        total += check_links()
    if do_sync:
        print("== template/asset sync check ==")
        total += check_sync()
    if total:
        print(f"\n{total} issue(s) found; clean them up and rerun.")
        sys.exit(1)
    print("\ndoc-drift check passed ✓")


if __name__ == "__main__":
    main()
