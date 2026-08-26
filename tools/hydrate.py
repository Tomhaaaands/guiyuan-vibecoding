#!/usr/bin/env python3
"""Progressive retrieval: pull the most relevant docs sections by keyword, avoiding full injection.

Usage:
  python tools/hydrate.py inspiration niche
  python tools/hydrate.py "api contract" --top 5 --lines 3

Behavior:
  1. Scan docs/**/*.md (skip archive/ and _archive/);
  2. Rank files by keyword hit count, print top N files and their matching lines;
  3. Print each file's approximate token size (chars/4) for context budgeting.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
DOCS = ROOT / "docs"
SKIP_PARTS = {"archive", "_archive"}


def _files():
    return [p for p in DOCS.rglob("*.md") if not any(part in SKIP_PARTS for part in p.parts)]


def main() -> None:
    ap = argparse.ArgumentParser(description="Retrieve relevant docs sections by keyword")
    ap.add_argument("keywords", nargs="+", help="search keywords (any match counts)")
    ap.add_argument("--top", type=int, default=8, help="max files to print")
    ap.add_argument("--lines", type=int, default=3, help="max matching lines per file")
    args = ap.parse_args()

    pats = [re.compile(re.escape(k), re.IGNORECASE) for k in args.keywords]
    hits: list[tuple[int, Path, list[str]]] = []
    for p in _files():
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lines = text.splitlines()
        matched = [ln.strip() for ln in lines if any(pat.search(ln) for pat in pats)]
        if matched:
            hits.append((len(matched), p, matched[: args.lines]))

    if not hits:
        print(f"no docs matched: {args.keywords}")
        return

    hits.sort(key=lambda x: x[0], reverse=True)
    print(f"{len(hits)} files matched (keywords: {' '.join(args.keywords)}), ranked by relevance:\n")
    for count, path, lines in hits[: args.top]:
        rel = path.relative_to(ROOT).as_posix()
        tokens = max(1, len(path.read_text(encoding="utf-8")) // 4)
        print(f"== {rel}  [{count} hits · ~{tokens} tokens]")
        for ln in lines:
            print(f"   - {ln[:120]}")
        print()


if __name__ == "__main__":
    main()
