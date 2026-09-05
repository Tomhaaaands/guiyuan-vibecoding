#!/usr/bin/env python3
"""P4 task graph: readiness and next-task dispatch over tasks authority artifacts.

A task artifact carries its contract in content fields: id, title, acceptance, status
(proposed|in_progress|done|blocked), priority, and depends_on. This tool builds the dependency
graph, computes readiness (all dependencies done), and picks the next executable task with an
explanation - so the manager can choose work without a user-maintained board.

Usage:
  python tools/task_graph.py --root <project> --action graph
  python tools/task_graph.py --root <project> --action ready
  python tools/task_graph.py --root <project> --action next --json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
from pathlib import Path

from artifact_store import ArtifactStore

sys.stdout.reconfigure(encoding="utf-8")

STATUSES = ("proposed", "in_progress", "done", "blocked")
_SECTION_RE = re.compile(r"^##\s+([^\n]+)$")


@dataclasses.dataclass
class Task:
    task_id: str
    title: str
    acceptance: str
    status: str
    priority: int
    depends_on: list[str]


def _lines_under(content: str, name: str) -> list[str]:
    out: list[str] = []
    active = False
    for line in content.splitlines():
        match = _SECTION_RE.match(line)
        if match:
            active = match.group(1).strip().lower() == name.lower()
            continue
        if active and line.strip():
            out.append(line.strip())
    return out


def _first(content: str, name: str) -> str:
    lines = _lines_under(content, name)
    return lines[0] if lines else ""


def _deps(content: str) -> list[str]:
    ids: list[str] = []
    for raw in _lines_under(content, "depends_on"):
        for token in raw.lstrip("-* ").replace(",", " ").split():
            if token and token not in ids:
                ids.append(token)
    return ids


def parse_task(task_id: str, content: str) -> Task:
    status = _first(content, "status").lower() or "proposed"
    if status not in STATUSES:
        status = "proposed"
    try:
        priority = int(_first(content, "priority"))
    except ValueError:
        priority = 999
    return Task(
        task_id=task_id,
        title=_first(content, "title"),
        acceptance=_first(content, "acceptance"),
        status=status,
        priority=priority,
        depends_on=_deps(content),
    )


def load_tasks(store: ArtifactStore) -> dict[str, Task]:
    out: dict[str, Task] = {}
    for meta in store.list():
        if meta.kind != "tasks":
            continue
        artifact = store.get(meta.artifact_id)
        out[meta.artifact_id] = parse_task(meta.artifact_id, artifact.content)
    return out


def build_graph(store: ArtifactStore) -> dict:
    tasks = load_tasks(store)
    return {
        "nodes": {tid: t.status for tid, t in tasks.items()},
        "edges": [
            {"from": dep, "to": tid}
            for tid, t in tasks.items()
            for dep in t.depends_on
            if dep != tid
        ],
    }


def readiness(store: ArtifactStore) -> dict[str, dict]:
    tasks = load_tasks(store)
    result: dict[str, dict] = {}
    for tid, task in tasks.items():
        missing = [d for d in task.depends_on if tasks.get(d, Task(d, "", "", "proposed", 999, [])).status != "done"]
        unknown = [d for d in task.depends_on if d not in tasks]
        result[tid] = {
            "task": tid,
            "status": task.status,
            "priority": task.priority,
            "ready": not missing and not unknown,
            "missing_deps": missing,
            "unknown_deps": unknown,
        }
    return result


def next_task(store: ArtifactStore) -> dict | None:
    """Pick the first done-dependency-satisfied task by (priority, id); explain the choice."""
    tasks = load_tasks(store)
    ready = readiness(store)
    candidates = [
        (tid, t)
        for tid, t in tasks.items()
        if t.status != "done" and t.status != "blocked" and ready[tid]["ready"]
    ]
    selected = sorted(candidates, key=lambda pair: (pair[1].priority, pair[0]))
    if not selected:
        return None
    tid, task = selected[0]
    return {
        "task": tid,
        "title": task.title,
        "acceptance": task.acceptance,
        "priority": task.priority,
        "reason": "all dependencies done; highest-priority ready task",
    }


def validate(store: ArtifactStore) -> list[str]:
    issues: list[str] = []
    tasks = load_tasks(store)
    for tid, task in tasks.items():
        if task.status == "done" and not task.acceptance:
            issues.append(f"{tid}: done but missing acceptance clause")
        for dep in task.depends_on:
            if dep not in tasks:
                issues.append(f"{tid}: depends on unknown task {dep}")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="P4 task graph: readiness and next-task dispatch")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--action", choices=("graph", "ready", "next"), default="next")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    store = ArtifactStore(args.root)
    if not store.dir.is_dir():
        raise SystemExit(f"no artifacts store at {args.root}")
    if args.action == "graph":
        payload = build_graph(store)
    elif args.action == "ready":
        payload = {"tasks": readiness(store)} if args.json else readiness(store)
    else:
        payload = next_task(store)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.action == "next":
        if payload:
            print(
                f"next: {payload['task']} [{payload['title']}] "
                f"(priority {payload['priority']}) - {payload['reason']}"
            )
        else:
            print("next: no ready task")
    elif args.action == "ready":
        for tid, r in payload.items():
            marker = "READY" if r["ready"] else "WAIT"
            print(f"  [{marker}] {tid}: {r['status']} (missing={','.join(r['missing_deps']) or '-'})")
    else:
        print(f"nodes={len(payload['nodes'])} edges={len(payload['edges'])}")


if __name__ == "__main__":
    main()
