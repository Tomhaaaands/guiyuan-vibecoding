#!/usr/bin/env python3
"""Self-contained QA gate for any project scaffolded by VibeCoding_Manager (stdlib only).

This tool ships with the published project template so an adopted project can verify its own
manager install and gates without depending on VibeCoding_Manager's internal test suite. It is
deliberately project-agnostic: it only reads the current project's files and prints a
machine-readable (or human-readable) pass/fail/warn summary.

Usage:
  python tools/selfqa.py
  python tools/selfqa.py --json
  python tools/selfqa.py --skip context_budget

Checks:
  - required project tools present;
  - AGENTS.md startup contract present;
  - docs five-layer skeleton present;
  - check_drift.py passes (markers + links + sync + version + budget);
  - context_budget.py stays within its ceiling;
  - llms.txt links resolve (if the file exists);
  - non-teaching docs contain no hard stale markers;
  - declared red-lines file is present.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "AGENTS.md").is_file())
TOOLS = ROOT / "tools"
DOCS_LAYERS = ("00-system", "01-product", "02-technical", "03-reference", "04-workflow")
REQUIRED_TOOLS = (
    "architecture_audit.py",
    "check_drift.py",
    "context_budget.py",
    "distill.py",
    "gen_llms_txt.py",
    "hydrate.py",
    "rollup_round.py",
    "selfqa.py",
    "vcm_session_hook.py",
    "workflow_optimize.py",
)
SKIP_PARTS = {"archive", "_archive"}
HARD_RE = re.compile(r"\[OUTDATED\]|\bTODO\b|\bTBD\b|\bFIXME\b")
LINK_RE = re.compile(r"\]\(([^)#]+?)\)")
PY = sys.executable


def _result(name: str, ok: bool, detail: str = "", level: str = "pass") -> dict:
    return {"check": name, "status": level if not ok else "pass", "ok": bool(ok), "detail": detail}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _run_tool(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def check_tools() -> list[dict]:
    missing = [t for t in REQUIRED_TOOLS if not (TOOLS / t).is_file()]
    if missing:
        return [_result("tools", False, f"missing: {', '.join(missing)}", level="fail")]
    return [_result("tools", True, f"all {len(REQUIRED_TOOLS)} present")]


def check_agents() -> list[dict]:
    if (ROOT / "AGENTS.md").is_file():
        return [_result("agents", True, "AGENTS.md present")]
    return [_result("agents", False, "missing AGENTS.md", level="fail")]


def check_docs_skeleton() -> list[dict]:
    docs = ROOT / "docs"
    missing = [d for d in DOCS_LAYERS if not (docs / d).is_dir()]
    if missing:
        return [_result("docs-skeleton", False, f"missing layers: {', '.join(missing)}", level="fail")]
    return [_result("docs-skeleton", True, "five-layer skeleton present")]


def check_drift() -> list[dict]:
    tool = TOOLS / "check_drift.py"
    if not tool.is_file():
        return [_result("check-drift", False, "tools/check_drift.py missing", level="fail")]
    proc = _run_tool([PY, str(tool)])
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip()[-600:]
        return [_result("check-drift", False, tail, level="fail")]
    return [_result("check-drift", True, "passed")]


def check_context_budget() -> list[dict]:
    tool = TOOLS / "context_budget.py"
    if not tool.is_file():
        return [_result("context-budget", False, "tools/context_budget.py missing", level="fail")]
    proc = _run_tool([PY, str(tool)])
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip()[-400:]
        return [_result("context-budget", False, tail, level="fail")]
    return [_result("context-budget", True, "within ceiling")]


def check_llms() -> list[dict]:
    llms = ROOT / "llms.txt"
    if not llms.is_file():
        return [_result("llms-links", True, "no llms.txt; skipped")]
    missing = []
    for i, line in enumerate(_text(llms).splitlines(), 1):
        for target in LINK_RE.findall(line):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if not (ROOT / target).resolve().exists():
                missing.append(f"{target}")
    if missing:
        return [_result("llms-links", False, f"broken links: {', '.join(missing[:8])}", level="fail")]
    return [_result("llms-links", True, "links resolve")]


def _md_files() -> list[Path]:
    docs = ROOT / "docs"
    if not docs.is_dir():
        return []
    return [p for p in docs.rglob("*.md") if not any(part in SKIP_PARTS for part in p.parts)]


def check_markers() -> list[dict]:
    hits = []
    for p in _md_files():
        rel = p.relative_to(ROOT).as_posix()
        if rel in {"docs/04-workflow/review-checklist.md",
                   "docs/04-workflow/product-update-protocol.md",
                   "docs/04-workflow/iteration-methodology.md",
                   "docs/04-workflow/AGENTS_WORKFLOW.md",
                   "docs/iteration-methodology.md",
                   "docs/02-technical/qa-contract.md"}:
            continue
        for i, line in enumerate(_text(p).splitlines(), 1):
            if HARD_RE.search(line):
                hits.append(f"{rel}:{i}")
    if hits:
        return [_result("markers", False, f"hard markers: {', '.join(hits[:8])}", level="fail")]
    return [_result("markers", True, "no hard stale markers")]


def check_red_lines() -> list[dict]:
    for p in (ROOT / "red-lines.md",
              ROOT / "docs" / "00-system" / "constitution" / "red-lines.md"):
        if p.is_file():
            return [_result("red-lines", True, f"present: {p.relative_to(ROOT).as_posix()}")]
    return [_result("red-lines", False, "no red-lines.md declared", level="warn")]


def check_hook() -> list[dict]:
    """The project-scoped Codex hook is optional; absent is a warning, not a failure."""
    hooks = ROOT / ".codex" / "hooks.json"
    if not hooks.is_file():
        return [_result("hook", False, "no .codex/hooks.json; project hook not installed", level="warn")]
    text = _text(hooks)
    if "vcm_session_hook.py" not in text or "SessionStart" not in text:
        return [_result("hook", False, ".codex/hooks.json present but not a VCM SessionStart hook",
                        level="warn")]
    return [_result("hook", True, "project-scoped SessionStart hook present")]


def run(skip: set[str]) -> list[dict]:
    checks: list[list[dict]] = []
    if "tools" not in skip:
        checks.append(check_tools())
    if "agents" not in skip:
        checks.append(check_agents())
    if "docs-skeleton" not in skip:
        checks.append(check_docs_skeleton())
    if "check_drift" not in skip:
        checks.append(check_drift())
    if "context_budget" not in skip:
        checks.append(check_context_budget())
    if "llms" not in skip:
        checks.append(check_llms())
    if "markers" not in skip:
        checks.append(check_markers())
    if "red-lines" not in skip:
        checks.append(check_red_lines())
    if "hook" not in skip:
        checks.append(check_hook())
    return [item for group in checks for item in group]


def main() -> int:
    ap = argparse.ArgumentParser(description="Self-QA gate for a VibeCoding_Manager project")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--skip", action="append", default=[], metavar="CHECK",
                    help="exclude a check by name")
    args = ap.parse_args()

    results = run(set(args.skip))
    failed = [r for r in results if r["status"] == "fail"]
    should_exit = bool(failed)

    if args.json:
        print(json.dumps({"root": str(ROOT), "passed": not failed, "checks": results},
                         ensure_ascii=False, indent=2))
    else:
        print(f"== self QA for {ROOT} ==")
        for r in results:
            status = "PASS" if r["status"] == "pass" else ("WARN" if r["status"] == "warn" else "FAIL")
            print(f"  [{status}] {r['check']}: {r['detail']}")
        print("self QA " + ("passed ✓" if not failed else f"failed: {len(failed)} check(s)"))

    if should_exit:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
