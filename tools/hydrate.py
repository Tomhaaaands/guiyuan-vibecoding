#!/usr/bin/env python3
"""Progressive retrieval: pull the most relevant docs sections by keyword, avoiding full injection.

Usage:
  python tools/hydrate.py inspiration niche
  python tools/hydrate.py "api contract" --top 5 --lines 3
  python tools/hydrate.py "api contract" --semantic   # PB semantic ranking, keyword fallback

Behavior:
  1. Scan docs/**/*.md (skip archive/ and _archive/);
  2. Rank files by keyword hit count, print top N files and their matching lines;
  3. Print each file's approximate token size (chars/4) for context budgeting.

Semantic retrieval is an optional PB-backed backend: `--semantic` calls the versioned
`guiyuan_butler_similarity` tool when `HYDRATE_SEMANTIC_BACKEND=pb` (or `guiyuan_butler`).
When PB is disabled, unavailable, or over its request limits, the command falls back to
deterministic keyword ranking.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from project_manifest import root_path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
DOCS = root_path(ROOT, "human_docs", "docs")
SKIP_PARTS = {"archive", "_archive"}
SIMILARITY_MAX_BYTES = 64 * 1024


def _files():
    return [p for p in DOCS.rglob("*.md") if not any(part in SKIP_PARTS for part in p.parts)]


def _semantic_backend() -> str | None:
    """Return the configured semantic backend identifier, if any."""
    return os.environ.get("HYDRATE_SEMANTIC_BACKEND")


def _semantic_search(query: str, top: int) -> list[tuple[float, Path, list[str]]] | None:
    """Optional semantic retrieval via the PB bridge; falls back to keyword."""
    backend = _semantic_backend()
    if not backend:
        print("[semantic] no backend configured (set HYDRATE_SEMANTIC_BACKEND=pb); falling back to keyword")
        return None
    if backend not in ("pb", "guiyuan_butler"):
        print(f"[semantic] backend '{backend}' not wired; falling back to keyword")
        return None
    try:
        from pb_bridge import TOOL_SIMILARITY, config as pb_config, pb_capabilities, pb_similarity
    except ImportError:
        print("[semantic] pb_bridge unavailable; falling back to keyword")
        return None
    cfg = pb_config()
    if not cfg["pb_enabled"]:
        print("[semantic] PB disabled; falling back to keyword")
        return None
    discovered = pb_capabilities(timeout=4)
    if not discovered:
        print("[semantic] PB discovery handshake failed; falling back to keyword")
        return None
    if TOOL_SIMILARITY not in set(discovered.get("tools", [])):
        print(f"[semantic] PB does not expose {TOOL_SIMILARITY}; falling back to keyword")
        return None
    candidates: list[tuple[Path, str]] = []
    # PB enforces a byte (not character) budget.  Counting characters would let
    # CJK-heavy projects exceed the 64 KiB request limit and trigger avoidable
    # fallback.  Leave the query's UTF-8 bytes in the same budget.
    remaining_bytes = SIMILARITY_MAX_BYTES - len(query.encode("utf-8"))
    if remaining_bytes <= 0:
        print("[semantic] query exceeds PB similarity byte budget; falling back to keyword")
        return None
    for path in _files()[:100]:
        try:
            text = path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError):
            continue
        if not text:
            continue
        sample = text[:1200]
        sample_bytes = len(sample.encode("utf-8"))
        if sample_bytes > remaining_bytes:
            # A later document may fit even if this one does not; skip this
            # candidate instead of ending the scan on a character/byte mismatch.
            continue
        candidates.append((path, sample))
        remaining_bytes -= sample_bytes
        if remaining_bytes <= 0:
            break
    res = pb_similarity(query, [text for _, text in candidates], timeout=4)
    if res is None:
        print("[semantic] PB similarity unavailable; falling back to keyword")
    elif res.get("unavailable"):
        print(f"[semantic] {res.get('reason', 'PB similarity unavailable')}; falling back to keyword")
    elif res.get("error"):
        print(f"[semantic] PB similarity error: {res['error']}; falling back to keyword")
    else:
        hits: list[tuple[float, Path, list[str]]] = []
        for row in res.get("results", []):
            try:
                index, score = int(row["index"]), float(row["score"])
                path, text = candidates[index]
            except (KeyError, IndexError, TypeError, ValueError):
                continue
            snippets = [line.strip() for line in text.splitlines() if line.strip()][:3]
            hits.append((score, path, snippets))
        if hits:
            print(f"[semantic] PB ranked {len(hits)} candidate documents")
            return hits[: max(1, top)]
        print("[semantic] PB returned no candidate scores; falling back to keyword")
    return None


def _print_hits(hits: list[tuple[float, Path, list[str]]], *, semantic: bool = False) -> None:
    for score, path, lines in hits:
        rel = path.relative_to(ROOT).as_posix()
        marker = f"score={score:.4f} " if semantic else ""
        tokens = max(1, len(path.read_text(encoding="utf-8")) // 4)
        print(f"== {rel}  [{marker}~{tokens} tokens]")
        for line in lines:
            print(f"   - {line[:120]}")
        print()


def main() -> None:
    ap = argparse.ArgumentParser(description="Retrieve relevant docs sections by keyword")
    ap.add_argument("keywords", nargs="+", help="search keywords (any match counts)")
    ap.add_argument("--top", type=int, default=8, help="max files to print")
    ap.add_argument("--lines", type=int, default=3, help="max matching lines per file")
    ap.add_argument("--semantic", action="store_true",
                    help="optional PB semantic retrieval; falls back to keyword when unavailable")
    args = ap.parse_args()

    if args.semantic:
        semantic_hits = _semantic_search(" ".join(args.keywords), args.top)
        if semantic_hits:
            _print_hits(semantic_hits, semantic=True)
            return

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
