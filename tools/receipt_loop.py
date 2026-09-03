#!/usr/bin/env python3
"""P5 execution/verification/receipt loop (stdlib only).

Wires a dispatched task to a delivery result that carries evidence:

  checks -> verdict (pass | fail | blocked) -> receipts artifact -> task status -> project-state

All checks ok -> pass (task done, stage DELIVERY, next task computed). A failing check with a
repair budget -> fail (task stays in_progress, evidence kept). A failing check with no budget ->
blocked (task blocked, blocker recorded). Receipts are revisioned and idempotent, so a repeated
dispatch with the same checks reuses the stored evidence instead of re-running.

Usage:
  python tools/receipt_loop.py --root <project> --task tasks/auth-01 --verdict pass --check "tests=ok"
  python tools/receipt_loop.py --root <project> --task tasks/auth-01 --verdict blocked --error "lint fail"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from artifact_store import ArtifactStore
from task_graph import next_task as graph_next

sys.stdout.reconfigure(encoding="utf-8")

_STATUS_RE = re.compile(r"(^##\s*status\s*\n)([^\n]*)(?=\n)", re.MULTILINE)


def _slug(artifact_id: str) -> str:
    return artifact_id.rsplit("/", 1)[-1] if "/" in artifact_id else artifact_id


def _checks_text(checks: list[dict]) -> str:
    lines: list[str] = []
    for c in checks:
        lines.append(f"- {c.get('name', 'check')}: {'ok' if c.get('ok') else 'fail'}")
        if c.get("output"):
            lines.append(f"    {str(c['output'])[:80]}")
    return "\n".join(lines)


def _receipt_content(task_id: str, key: str, verdict: str, checks: list[dict], error: str | None) -> str:
    return (
        f"## idempotency_key\n{key}\n## task\n{task_id}\n## verdict\n{verdict}\n"
        f"## checks\n{_checks_text(checks)}\n## error\n{error or '-'}\n"
    )


def record_receipt(
    store: ArtifactStore,
    task_id: str,
    *,
    verdict: str,
    checks: list[dict],
    error: str | None = None,
    dispatcher: str = "codex",
) -> str:
    if verdict not in ("pass", "fail", "blocked"):
        raise ValueError(f"invalid verdict {verdict!r}")
    key = hashlib.sha256(
        json.dumps([task_id, verdict, checks], ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    receipt_id = f"receipts/{_slug(task_id)}"
    content = (
        f"## dispatcher\n{dispatcher}\n"
        + _receipt_content(task_id, key, verdict, checks, error)
    )
    store.write(receipt_id, "receipts", content, status="accepted", depends_on=[task_id])
    return receipt_id


def _replace_status(content: str, new_status: str) -> str:
    if _STATUS_RE.search(content):
        return _STATUS_RE.sub(lambda m: m.group(1) + new_status, content)
    return content + f"\n## status\n{new_status}\n"


def update_task_status(store: ArtifactStore, task_id: str, new_status: str) -> None:
    artifact = store.get(task_id)
    store.write(task_id, "tasks", _replace_status(artifact.content, new_status), status="accepted")


def update_project_state(
    store: ArtifactStore,
    *,
    stage: str,
    task: str = "",
    blocker: str = "",
    nxt: str = "",
) -> None:
    content = f"## stage\n{stage}\n## task\n{task or '-'}\n## blocker\n{blocker or '-'}\n## next\n{nxt or '-'}\n"
    store.write("project-state", "project-state", content, status="accepted")


def apply_receipt(store: ArtifactStore, task_id: str, verdict: str, error: str | None) -> dict:
    if verdict == "pass":
        update_task_status(store, task_id, "done")
        stage = "DELIVERY"
        blocker = ""
        state_task = ""
        state_next = ""
    elif verdict == "fail":
        update_task_status(store, task_id, "in_progress")
        stage = "EXECUTION"
        blocker = ""
        state_task = task_id
        state_next = task_id
    else:
        update_task_status(store, task_id, "blocked")
        stage = "EXECUTION"
        blocker = error or "checks failing"
        state_task = task_id
        state_next = ""
    update_project_state(store, stage=stage, task=state_task, blocker=blocker, nxt=state_next)
    return {"task_status": _task_status(store, task_id), "stage": stage}


def _task_status(store: ArtifactStore, task_id: str) -> str:
    artifact = store.get(task_id)
    match = _STATUS_RE.search(artifact.content)
    return match.group(2).strip() if match else "unknown"


def run_cycle(
    root: Path,
    task_id: str,
    *,
    checks: list[dict],
    error: str | None = None,
    retry: int = 0,
    dispatcher: str = "codex",
) -> dict:
    store = ArtifactStore(root)
    store.init()
    if not store.exists(task_id):
        raise ValueError(f"task not found: {task_id}")
    verdict = "pass" if all(c.get("ok") for c in checks) else ("fail" if retry > 0 else "blocked")
    receipt_id = record_receipt(
        store, task_id, verdict=verdict, checks=checks, error=error, dispatcher=dispatcher
    )
    applied = apply_receipt(store, task_id, verdict, error)
    nxt = graph_next(store)
    return {
        "task": task_id,
        "verdict": verdict,
        "receipt_id": receipt_id,
        "task_status": applied["task_status"],
        "stage": applied["stage"],
        "next": nxt["task"] if nxt else "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="P5 receipt loop")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--verdict", choices=("pass", "fail", "blocked"), required=True)
    parser.add_argument("--check", action="append", default=[], help="name=ok|fail[:output]")
    parser.add_argument("--error")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    checks = []
    for raw in args.check:
        name, _, rest = raw.partition("=")
        ok = not rest.lower().startswith(("fail", "false", "0"))
        output = rest.split(":", 1)[1] if ":" in rest else ""
        checks.append({"name": name, "ok": ok, "output": output})
    store = ArtifactStore(args.root)
    receipt_id = record_receipt(
        store, args.task, verdict=args.verdict, checks=checks, error=args.error
    )
    applied = apply_receipt(store, args.task, args.verdict, args.error)
    out = {"task": args.task, "verdict": args.verdict, "receipt_id": receipt_id, **applied}
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"task {args.task} -> {args.verdict}: receipt {receipt_id}, status={applied['task_status']}")


if __name__ == "__main__":
    main()
