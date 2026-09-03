#!/usr/bin/env python3
"""Suggest, never apply, small workflow improvements from milestone receipts.

Usage:
  python tools/workflow_optimize.py --receipt docs/receipts/m1.md
  python tools/workflow_optimize.py --receipt receipt.md --json
  python tools/workflow_optimize.py --dismiss <candidate-id>

The tool reads the project's .vibecoding-manager/adoption.json.  It emits at
most three evidence-backed suggestions and does not write project workflow
files.  A dismissal is an explicit user decision and suppresses that exact
candidate in future reviews.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
STATE = ROOT / ".vibecoding-manager"
ADOPTION = STATE / "adoption.json"
DECISIONS = STATE / "optimization-decisions.json"

RULES = (
    ("tooling", ("test fail", "build fail", "check_drift", "todo", "fixme"),
     "Add the manager's tooling workflow so checks and receipts are easier to repeat."),
    ("ledger", ("handoff", "history", "release", "regression"),
     "Map or manage the ledger workflow to preserve decisions and delivery evidence."),
    ("startup", ("context", "restate", "forgot", "onboard"),
     "Map the startup workflow so the next conversation receives only the relevant project context."),
)


def load(path: Path, fallback: object) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def choices(adoption: dict) -> dict[str, str]:
    return adoption.get("workflows", {}) if isinstance(adoption.get("workflows"), dict) else {}


def candidate_id(workflow: str, evidence: str) -> str:
    return f"{workflow}-{hashlib.sha256(evidence.encode('utf-8')).hexdigest()[:12]}"


def build(receipts: list[Path], adoption: dict, dismissed: set[str]) -> list[dict[str, str]]:
    modes = choices(adoption)
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for receipt in receipts:
        try:
            lines = receipt.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for workflow, keywords, benefit in RULES:
            if modes.get(workflow, "keep") == "managed":
                continue
            evidence = next((line.strip() for line in lines if any(word in line.lower() for word in keywords)), "")
            if not evidence:
                continue
            cid = candidate_id(workflow, evidence)
            if cid in dismissed or cid in seen:
                continue
            seen.add(cid)
            candidates.append({
                "id": cid,
                "workflow": workflow,
                "evidence": evidence,
                "benefit": benefit,
                "change": f"Ask the user whether {workflow} should remain keep, become map, or become managed.",
                "rollback": "No change is applied by this tool; a later adoption change is backed up and receipted.",
            })
            if len(candidates) == 3:
                return candidates
    return candidates


def main() -> None:
    ap = argparse.ArgumentParser(description="Suggest a small, user-approved workflow optimization bundle")
    ap.add_argument("--receipt", action="append", default=[], help="milestone receipt to inspect (repeatable)")
    ap.add_argument("--dismiss", action="append", default=[], help="explicitly dismiss a candidate id (repeatable)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a human-readable bundle")
    args = ap.parse_args()
    adoption = load(ADOPTION, {})
    if not isinstance(adoption, dict) or not adoption:
        ap.error("no adoption record found; run the confirmed adopt flow first")
    decision_data = load(DECISIONS, {"dismissed": []})
    dismissed = set(decision_data.get("dismissed", [])) if isinstance(decision_data, dict) else set()
    if args.dismiss:
        STATE.mkdir(exist_ok=True)
        dismissed.update(args.dismiss)
        DECISIONS.write_text(json.dumps({"dismissed": sorted(dismissed)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"dismissed {len(args.dismiss)} candidate(s)")
        return
    receipts = [(ROOT / item).resolve() if not Path(item).is_absolute() else Path(item) for item in args.receipt]
    bundle = build(receipts, adoption, dismissed)
    if args.json:
        print(json.dumps({"candidates": bundle}, ensure_ascii=False, indent=2))
        return
    print("== workflow optimization bundle ==")
    if not bundle:
        print("  no evidence-backed suggestions; nothing was changed.")
        return
    for item in bundle:
        print(f"  - {item['id']} ({item['workflow']})")
        print(f"    evidence: {item['evidence']}")
        print(f"    benefit : {item['benefit']}")
        print(f"    change  : {item['change']}")
        print(f"    rollback: {item['rollback']}")


if __name__ == "__main__":
    main()
