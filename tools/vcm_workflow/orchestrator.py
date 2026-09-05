"""Intent router and end-to-end workflow facade for VCM.

The facade keeps user-facing routing small while the repository-backed nine-state machine and
existing module implementations remain authoritative.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from tools.vcm_core.module_protocol import blocked, complete, failed

sys.stdout.reconfigure(encoding="utf-8")


ROUTES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("install", ("安装", "更新 skill", "doctor", "预检")),
    ("uninstall", ("卸载", "删除 guiyuan")),
    ("release", ("release", "发布", "push", "tag", "提交 github", "提交git")),
    ("requirement", ("需求", "prd", "产品方案", "范围", "验收标准", "验收范围")),
    ("planning", ("拆任务", "任务计划", "依赖", "下一步", "上下文")),
    ("qa", ("测试", "qa", "验收", "回归", "检查")),
    ("workflow", ("继续", "执行", "修复", "端到端", "从头到尾")),
)


def route_intent(intent: str) -> str:
    """Choose the narrowest explicit route; default to the workflow facade."""
    text = (intent or "").strip().lower()
    if not text:
        return "requirement"
    for route, keywords in ROUTES:
        if any(keyword.lower() in text for keyword in keywords):
            return route
    return "workflow"


def run_requirement(root: Path, intent: str, provider: str = "local-fallback") -> dict[str, Any]:
    from tools.vcm_requirement.analysis import analyze

    output = analyze(intent, root=root, provider=provider)
    return complete("requirement", artifacts=[output.get("artifact_id", "")], evidence=[output])


def run_planning(root: Path) -> dict[str, Any]:
    from tools.vcm_core.artifact_store import ArtifactStore
    from tools.vcm_planning.context_compiler import compile_context
    from tools.vcm_planning.task_graph import next_task

    store = ArtifactStore(root)
    store.init()
    task = next_task(store)
    context = compile_context(store, phase="PLANNING")
    if not task:
        return blocked("planning", ["no ready task"], next_action="补充任务输入和 acceptance")
    return complete("planning", artifacts=[task["task"]], evidence=[context], next_action=task["task"])


def run_workflow(root: Path, intent: str, *, provider: str = "local-fallback",
                 ceiling: int = 2500) -> dict[str, Any]:
    from tools.vcm_workflow.mvp_walkthrough import run_walkthrough

    report = run_walkthrough(root, intent, provider=provider, ceiling=ceiling)
    status = "complete" if report.get("passed") else "failed"
    envelope = complete("workflow", artifacts=[report.get("analysis_id", "")], evidence=[report])
    envelope["status"] = status
    if status == "failed":
        envelope["blockers"] = report.get("consistency_errors", []) or ["workflow acceptance failed"]
        envelope["next_action"] = "查看 workflow evidence 并创建 repair task"
    return envelope


def run_route(root: Path, intent: str, *, provider: str = "local-fallback",
              ceiling: int = 2500) -> dict[str, Any]:
    route = route_intent(intent)
    try:
        if route == "requirement":
            result = run_requirement(root, intent, provider)
        elif route == "planning":
            result = run_planning(root)
        elif route == "workflow":
            result = run_workflow(root, intent, provider=provider, ceiling=ceiling)
        else:
            result = blocked(route, [f"route {route} is handled by its dedicated lifecycle CLI"],
                             next_action=f"调用 vcm_{route} 模块")
    except Exception as exc:  # preserve a machine-readable failed handoff
        result = failed(route, [f"{type(exc).__name__}: {exc}"], next_action="检查输入和模块证据")
    result["route"] = route
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="VCM internal workflow router")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--provider", default="local-fallback")
    parser.add_argument("--ceiling", type=int, default=2500)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.root is None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_route(Path(tmp), args.intent, provider=args.provider, ceiling=args.ceiling)
    else:
        result = run_route(args.root, args.intent, provider=args.provider, ceiling=args.ceiling)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"route={result['route']} status={result['status']} next={result['next_action'] or '-'}")
    return 0 if result["status"] in ("complete", "ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
