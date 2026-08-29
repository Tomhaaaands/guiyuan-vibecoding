#!/usr/bin/env python3
"""Project-memory distillation pipeline.

Four directions. `pitfalls` is implemented as a deterministic first pass; the other three
are stubs pending their own work.

  pitfalls    坑 → 红线：scan the project's archive volumes + module iteration.md for
              incident/pitfall markers and emit red-line DRAFT candidates. Dry-run by
              default; --apply writes them to a draft file (never auto-edits red-lines.md).

  method      方法 → 模板：promote a proven workflow into templates/ + profiles/.  (stub)
  consolidate 碎片 → 结论：fold repeated module facts into a stable conclusion card. (stub)
  promote     私有 → 共性：lift a reusable lesson from one project into the shared kit. (stub)

Distillation reads the project's own archive/state files only. It does NOT depend on
memory-os or any external memory/embedding service — that coupling was a mistake and is removed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())

# Pitfall/red-line candidate markers. Deliberately specific (not generic negations) so the
# draft stays reviewable; a human (or a later LLM pass) promotes candidates into red lines.
PITFALL_RE = re.compile(
    r"红线|踩坑|坑位|事故|复盘|根因|教训|禁止|不允许|切记|"
    r"pitfall|red[ -]?line|incident|post[- ]?mortem|root cause|lesson learned|anti[- ]?pattern|"
    r"must not|\bforbid",
    re.IGNORECASE,
)

DIRECTIONS = {
    "pitfalls": {
        "desc": "坑 → 红线",
        "inputs": ["docs/04-workflow/archive/", "docs/02-technical/*/iteration.md"],
        "output": "docs/00-system/constitution/red-lines.draft.md",
    },
    "method": {
        "desc": "方法 → 模板",
        "inputs": ["docs/04-workflow/archive/"],
        "output": "templates/iteration-methodology/ + skills/project-bootstrap/profiles/",
    },
    "consolidate": {
        "desc": "碎片 → 结论",
        "inputs": ["docs/02-technical/*/iteration.md"],
        "output": "module state cards",
    },
    "promote": {
        "desc": "项目私有 → 跨项目共性",
        "inputs": ["a project's archive/ + iteration.md"],
        "output": "shared kit (templates/ / skills/)",
    },
}


def _source_root(source: str | None) -> Path:
    if source:
        p = Path(source)
        if not p.is_dir():
            sys.exit(f"error: --source is not a directory: {source}")
        return p.resolve()
    return ROOT


def _scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    archive = root / "docs" / "04-workflow" / "archive"
    if archive.is_dir():
        files.extend(sorted(archive.glob("*.md")))
    tech = root / "docs" / "02-technical"
    if tech.is_dir():
        files.extend(sorted(tech.glob("*/iteration.md")))
    return files


def _candidates(files: list[Path]) -> list[tuple[Path, int, str, str]]:
    out: list[tuple[Path, int, str, str]] = []
    for f in files:
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(lines, 1):
            m = PITFALL_RE.search(line)
            if m:
                out.append((f, i, m.group(0), line.strip()[:160]))
    return out


def _dedupe(cands, limit):
    seen: set[str] = set()
    out = []
    for f, i, tok, excerpt in cands:
        key = excerpt.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append((f, i, tok, excerpt))
        if len(out) >= limit:
            break
    return out


def run_pitfalls(root: Path, limit: int, apply: bool) -> None:
    files = _scan_files(root)
    if not files:
        print("no archive/ or module iteration.md found — nothing to distill yet")
        return
    cands = _dedupe(_candidates(files), limit)
    print(f"scanned {len(files)} file(s); {len(cands)} pitfall candidate(s):\n")
    if not cands:
        return
    rel_lines = []
    for f, i, tok, excerpt in cands:
        rel = f.relative_to(root).as_posix() if f.is_relative_to(root) else f.as_posix()
        line = f"- [AI-DRAFT] {excerpt}  (from {rel}:{i}, matched “{tok}”)"
        print(line)
        rel_lines.append(line)
    red = root / "docs" / "00-system" / "constitution" / "red-lines.md"
    if apply:
        draft = red.with_name("red-lines.draft.md")
        draft.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "# Red-line draft candidates\n\n"
            "> Proposed by `tools/distill.py pitfalls`. Review and promote confirmed items "
            "into `red-lines.md` (never archive red lines).\n\n"
        )
        draft.write_text(header + "\n".join(rel_lines) + "\n", encoding="utf-8")
        print(f"\nwrote draft: {draft.relative_to(root).as_posix()}")
        if red.exists():
            print("hint: review against the existing red-lines.md before promoting")
    else:
        print("\n(dry-run; rerun with --apply to write red-lines.draft.md)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Project-memory distillation")
    sub = ap.add_subparsers(dest="direction", required=True)

    p = sub.add_parser("pitfalls", help=DIRECTIONS["pitfalls"]["desc"])
    p.add_argument("--source", default=None, help="project dir to distill (default: repo root)")
    p.add_argument("--limit", type=int, default=20, help="max candidate lines to emit")
    p.add_argument("--apply", action="store_true", help="write candidates to red-lines.draft.md (default: dry-run)")

    for name in ("method", "consolidate", "promote"):
        q = sub.add_parser(name, help=DIRECTIONS[name]["desc"])
        q.add_argument("--source", default=None, help="project dir (reserved)")

    args = ap.parse_args()
    meta = DIRECTIONS[args.direction]

    if args.direction == "pitfalls":
        run_pitfalls(_source_root(args.source), args.limit, args.apply)
        return

    print(f"distill/{args.direction}: {meta['desc']}")
    print(f"  inputs : {', '.join(meta['inputs'])}")
    print(f"  output : {meta['output']}")
    print("  status : stub — implement next; not blocked on memory-os")


if __name__ == "__main__":
    main()
