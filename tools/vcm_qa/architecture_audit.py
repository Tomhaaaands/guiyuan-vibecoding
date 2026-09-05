#!/usr/bin/env python3
"""Read-only audit for legacy/canonical project layout conflicts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DOC_ROOT_FILES = {
    "product-spec.md", "product-baseline-v0.1.0.md", "manager-architecture.md",
    "provider-boundary.md", "artifact-context-contract.md", "token-budget.md", "roadmap.md",
}


def audit(root: Path) -> dict:
    docs = root / "docs"
    conflicts = []
    legacy = []
    actual_dirs = {p.name for p in root.iterdir() if p.is_dir()}
    for name in ("Apps", "Workers"):
        if name in actual_dirs:
            legacy.append(f"{name}/ -> {name.lower()}/")
    for name in DOC_ROOT_FILES:
        source = docs / name
        if source.is_file():
            conflicts.append({"source": f"docs/{name}", "reason": "root authority needs classification"})
    for rel in ("00-system", "01-product", "02-technical", "03-reference", "04-workflow"):
        d = docs / rel
        if not d.exists():
            conflicts.append({"source": f"docs/{rel}", "reason": "missing canonical layer"})
    return {
        "project": str(root),
        "legacy_directories": legacy,
        "authority_conflicts": conflicts,
        "author_owned_candidates": [p for p in ("CHANGELOG.md", "NOW.md", "docs") if (root / p).exists()],
        "read_only": True,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit legacy and canonical VCM project layout")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = audit(Path(args.project).resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"project: {result['project']}")
        print("legacy directories: " + (", ".join(result["legacy_directories"]) or "none"))
        print(f"authority conflicts: {len(result['authority_conflicts'])}")
        for item in result["authority_conflicts"]:
            print(f"  - {item['source']}: {item['reason']}")
        print("read-only audit: passed")


if __name__ == "__main__":
    main()
