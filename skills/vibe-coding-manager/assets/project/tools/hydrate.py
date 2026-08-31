#!/usr/bin/env python3
"""Progressive retrieval: pull the most relevant docs sections by keyword, avoiding full injection.

Usage:
  python tools/hydrate.py inspiration niche
  python tools/hydrate.py "api contract" --top 5 --lines 3
  python tools/hydrate.py "api contract" --semantic   # reserved interface, keyword fallback

Behavior:
  1. Scan docs/**/*.md (skip archive/ and _archive/);
  2. Rank files by keyword hit count, print top N files and their matching lines;
  3. Print each file's approximate token size (chars/4) for context budgeting.

Semantic retrieval is an optional, not-yet-wired backend: `--semantic` is accepted for
forward-compatibility but currently falls back to keyword. Set `HYDRATE_SEMANTIC_BACKEND`
to reserve a backend identifier; the call contract will be implemented when the shared
memory/embedding service stabilizes.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
DOCS = ROOT / "docs"
SKIP_PARTS = {"archive", "_archive"}


def _files():
    return [p for p in DOCS.rglob("*.md") if not any(part in SKIP_PARTS for part in p.parts)]


def _semantic_backend() -> str | None:
    """Return the configured semantic backend identifier, if any."""
    return os.environ.get("HYDRATE_SEMANTIC_BACKEND")


def _semantic_search(query: str, top: int) -> list[tuple[int, Path, list[str]]] | None:
    """Optional semantic retrieval — interface only; falls back to keyword for now."""
    backend = _semantic_backend()
    if not backend:
        print("[semantic] no backend configured (set HYDRATE_SEMANTIC_BACKEND); falling back to keyword")
        return None
    print(f"[semantic] backend '{backend}' reserved but not wired yet; falling back to keyword")
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Retrieve relevant docs sections by keyword")
    ap.add_argument("keywords", nargs="+", help="search keywords (any match counts)")
    ap.add_argument("--top", type=int, default=8, help="max files to print")
    ap.add_argument("--lines", type=int, default=3, help="max matching lines per file")
    ap.add_argument("--semantic", action="store_true",
                    help="optional semantic retrieval (reserved interface; falls back to keyword)")
    args = ap.parse_args()

    if args.semantic:
        _semantic_search(" ".join(args.keywords), args.top)

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
