#!/usr/bin/env python3
"""Estimate and enforce a conservative management-context token budget.

Usage:
  python tools/context_budget.py
  python tools/context_budget.py AGENTS.md NOW.md --target 1800 --budget 2500
  python tools/context_budget.py path/to/context.md --strict-target --json

With no paths, audits the startup contract: AGENTS.md plus NOW.md (root or workflow card).
The estimator counts each non-ASCII non-whitespace character as one token and each four ASCII
non-whitespace characters as one token. Provider-native tokenizers may replace the estimate later;
this conservative, dependency-free gate remains reproducible across platforms.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    from project_manifest import artifact_path
except ImportError:  # pragma: no cover
    artifact_path = None

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(
    p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents)
    if (p / "README.md").is_file()
)
DEFAULT_TARGET = 1_800
DEFAULT_BUDGET = 2_500


def estimate_tokens(text: str) -> int:
    """Return a deterministic conservative estimate suitable for a blocking local gate."""
    unicode_chars = sum(1 for ch in text if not ch.isspace() and ord(ch) > 127)
    ascii_chars = sum(1 for ch in text if not ch.isspace() and ord(ch) <= 127)
    return unicode_chars + math.ceil(ascii_chars / 4)


def default_startup_paths(root: Path = ROOT) -> list[Path]:
    paths = [root / "AGENTS.md"]
    if artifact_path:
        paths.append(artifact_path(root, "project_state", must_exist=True))
    else:
        root_now = root / "NOW.md"
        workflow_now = root / "docs" / "04-workflow" / "NOW.md"
        paths.append(root_now if root_now.is_file() else workflow_now)
    return paths


def resolve_paths(raw_paths: list[str], root: Path = ROOT) -> list[Path]:
    if not raw_paths:
        return default_startup_paths(root)
    resolved: list[Path] = []
    for raw in raw_paths:
        path = Path(raw)
        resolved.append(path if path.is_absolute() else root / path)
    return resolved


def audit(paths: list[Path]) -> tuple[list[dict[str, int | str]], int]:
    rows: list[dict[str, int | str]] = []
    total = 0
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8")
        tokens = estimate_tokens(text)
        total += tokens
        try:
            label = path.relative_to(ROOT).as_posix()
        except ValueError:
            label = str(path)
        rows.append({"path": label, "characters": len(text), "estimated_tokens": tokens})
    return rows, total


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit management-context token budgets")
    parser.add_argument("paths", nargs="*", help="UTF-8 context files; defaults to AGENTS + NOW")
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET, help="operating target")
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET, help="blocking hard ceiling")
    parser.add_argument("--strict-target", action="store_true", help="fail above target, not only ceiling")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    if args.target <= 0 or args.budget <= 0 or args.target > args.budget:
        parser.error("require 0 < target <= budget")

    try:
        rows, total = audit(resolve_paths(args.paths))
    except (FileNotFoundError, UnicodeDecodeError) as exc:
        print(f"context-budget error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    status = "pass" if total <= args.target else "warn" if total <= args.budget else "fail"
    result = {
        "status": status,
        "target": args.target,
        "hard_ceiling": args.budget,
        "estimated_tokens": total,
        "remaining_to_ceiling": args.budget - total,
        "files": rows,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("== context budget ==")
        for row in rows:
            print(f"  {row['path']}: ~{row['estimated_tokens']} tokens ({row['characters']} chars)")
        print(
            f"  total ~{total} / target {args.target} / hard {args.budget} "
            f"[{status}]"
        )

    if total > args.budget or (args.strict_target and total > args.target):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
