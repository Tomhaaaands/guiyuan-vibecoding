#!/usr/bin/env python3
"""P3 production: turn an accepted analysis artifact into authoritative artifact drafts.

Takes a labeled `analysis` artifact (known_facts / assumptions / options / decisions /
open_questions) and writes the authority artifacts that own those facts:

  - `product/<slug>`  (product-spec): acceptance, scope, requirements, open questions
  - `decisions/<slug>` (decisions): the accepted trade-offs / constraints

Generated artifacts are written at `draft` and depend on the source analysis artifact, so the
cross-artifact consistency check can validate them without a human gate. This is a deterministic
structural mapping (no provider call); it does not invent facts the analysis did not label.

Usage:
  python tools/artifact_generate.py --root <project> --analysis-id analysis/build-an-email-login
  python tools/artifact_generate.py --root <project> --analysis-id analysis/build-an-email-login --status draft
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from artifact_store import ArtifactStore
from analysis import parse_analysis

sys.stdout.reconfigure(encoding="utf-8")


def _slug(analysis_id: str) -> str:
    return analysis_id.rsplit("/", 1)[-1] if "/" in analysis_id else analysis_id


def _product_spec(intent: str, facts: list[dict], decisions: list[dict], questions: list[dict]) -> str:
    acceptance = (
        "; ".join(d.get("statement", "") for d in decisions)
        or "; ".join(f.get("statement", "") for f in facts)
        or "TBD"
    )
    lines = [
        "# Product spec",
        "",
        "## acceptance",
        acceptance,
        "",
        "## scope",
        intent or "(not stated)",
        "",
        "## requirements",
    ]
    for item in facts:
        lines.append(f"- {item.get('statement', '')}")
    for item in decisions:
        lines.append(f"- {item.get('statement', '')}")
    if questions:
        lines += ["", "## open questions"]
        for item in questions:
            lines.append(f"- {item.get('statement', '')}")
    return "\n".join(lines).rstrip() + "\n"


def _decisions(decisions: list[dict]) -> str:
    lines = ["# Decisions", "", "## constraint"]
    if decisions:
        for item in decisions:
            lines.append(f"- {item.get('statement', '')}")
    else:
        lines.append("(none)")
    return "\n".join(lines) + "\n"


def generate(root: Path, analysis_id: str, *, status: str = "draft") -> dict:
    store = ArtifactStore(root)
    store.init()
    analysis = store.get(analysis_id)
    result = parse_analysis(analysis.content)
    slug = _slug(analysis_id)
    product_id = f"product/{slug}"
    decisions_id = f"decisions/{slug}"

    product_content = _product_spec(
        result.get("intent", ""),
        result.get("known_facts", []),
        result.get("decisions", []),
        result.get("open_questions", []),
    )
    decisions_content = _decisions(result.get("decisions", []))

    product_meta = store.write(
        product_id, "product-spec", product_content, status=status, depends_on=[analysis_id]
    )
    decisions_meta = store.write(
        decisions_id, "decisions", decisions_content, status=status, depends_on=[analysis_id]
    )
    return {
        "analysis_id": analysis_id,
        "product_id": f"{product_id}@{product_meta.revision}",
        "decisions_id": f"{decisions_id}@{decisions_meta.revision}",
        "status": status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn an analysis artifact into authority drafts")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--analysis-id", required=True)
    parser.add_argument("--status", default="draft")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out = generate(args.root, args.analysis_id, status=args.status)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"generated {out['product_id']} and {out['decisions_id']} [{out['status']}]")


if __name__ == "__main__":
    main()
