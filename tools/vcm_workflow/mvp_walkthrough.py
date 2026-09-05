#!/usr/bin/env python3
"""P8 end-to-end MVP: one scripted journey through the whole local loop (stdlib only).

Runs a small product intent through analysis -> authority-artifact generation -> consistency ->
task dispatch -> execution/verification receipt -> experience reflection, then reports a context
budget gate and an overall pass/fail. Defaults to the deterministic `local-fallback` backend so it
runs with no key; `--provider siliconflow` adds real model quality (requires the key env var).

Usage:
  python tools/mvp_walkthrough.py --intent "Add an admin dashboard with role-based access."
  python tools/mvp_walkthrough.py --provider siliconflow --json
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from artifact_store import ArtifactStore
from analysis import analyze
from artifact_generate import generate as generate_artifacts
from artifact_consistency import check as check_consistency
from task_graph import next_task
from receipt_loop import run_cycle
from experience_loop import collect_experience, write_experience
from context_compiler import compile_context

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_INTENT = "Add an admin dashboard with role-based access for user growth metrics."


def _seed_tasks(store: ArtifactStore) -> None:
    if store.exists("tasks/auth-01"):
        return
    store.write(
        "tasks/auth-01",
        "tasks",
        "## id\ntasks/auth-01\n## title\nimpl auth gate\n## acceptance\nadmin gate works\n"
        "## status\nproposed\n## priority\n1\n## depends_on\n\n",
        status="accepted",
    )


def run_walkthrough(
    root: Path,
    intent: str = DEFAULT_INTENT,
    *,
    provider: str = "local-fallback",
    ceiling: int = 2500,
) -> dict:
    store = ArtifactStore(root)
    store.init()

    analysis_out = analyze(intent, root=root, provider=provider)
    analysis_id = analysis_out["artifact_id"]
    generated = generate_artifacts(root, analysis_id)

    consistency = [i for i in check_consistency(store) if i["severity"] == "error"]

    _seed_tasks(store)
    nxt = next_task(store)
    receipt = None
    if nxt:
        outcome = run_cycle(root, nxt["task"], checks=[{"name": "tests", "ok": True, "output": "green"}])
        receipt = {
            "task": outcome["task"],
            "verdict": outcome["verdict"],
            "task_status": outcome["task_status"],
            "stage": outcome["stage"],
        }

    experience = collect_experience(store)
    if experience:
        write_experience(store, experience[0]["slug"], experience[0])

    ctx = compile_context(store, phase="EXECUTION")
    context_tokens = ctx["estimated_tokens"]
    passed = (not consistency) and context_tokens <= ceiling and receipt is not None

    return {
        "intent": intent,
        "provider": analysis_out["provider"],
        "analysis_id": analysis_id,
        "generated": generated,
        "degraded": analysis_out["degraded"],
        "red_line_touch": analysis_out.get("red_line_touch", False),
        "buckets": {k: len(analysis_out["result"][k]) for k in analysis_out["result"] if k != "intent"},
        "consistency_errors": consistency,
        "next_task": nxt["task"] if nxt else "",
        "receipt": receipt,
        "experience_candidates": len(experience),
        "context_tokens": context_tokens,
        "ceiling": ceiling,
        "passed": passed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="P8 end-to-end MVP walkthrough")
    parser.add_argument("--intent", default=DEFAULT_INTENT)
    parser.add_argument("--provider", default="local-fallback")
    parser.add_argument("--ceiling", type=int, default=2500)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        report = run_walkthrough(
            Path(tmp), args.intent, provider=args.provider, ceiling=args.ceiling
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"== MVP walkthrough: {report['intent']} ==")
            print(f"  analysis {report['analysis_id']} provider={report['provider']} "
                  f"degraded={report['degraded']} red_line_touch={report['red_line_touch']}")
            print(f"  buckets {report['buckets']}")
            print(f"  generated {report['generated']['product_id']} + {report['generated']['decisions_id']}")
            print(f"  consistency_errors={len(report['consistency_errors'])}")
            print(f"  next_task={report['next_task']} receipt={report['receipt']}")
            print(f"  experience_candidates={report['experience_candidates']}")
            print(f"  context_tokens={report['context_tokens']}/{report['ceiling']}")
            print(f"  overall={'PASS' if report['passed'] else 'FAIL'}")
        if not report["passed"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
