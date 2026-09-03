#!/usr/bin/env python3
"""Project-scoped Codex SessionStart hook for VibeCoding_Manager (stdlib only).

A managed project carries this at tools/vcm_session_hook.py and a sibling
.codex/hooks.json that wires it to the SessionStart event. The hook only reads the
project and never writes, so it is advisory: it detects whether the project is
already managed, merely has the VCM methodology skeleton, looks like a coding
project, or is empty/notes-only, then injects a short directive into the agent's
developer context. It deliberately does not auto-takeover empty/ambiguous folders;
it asks the user to declare intent instead.

On SessionStart it prints a JSON object:
  {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}

The deep read-only gates (selfqa / context_budget) run only when VCM_HOOK_CHECK=1 or
<project>/.vibecoding-manager/hook_full exists, to keep every session start cheap.

Usage:
  python tools/vcm_session_hook.py            # read a SessionStart event on stdin
  python tools/vcm_session_hook.py --state     # print detected state for cwd/project
  python tools/vcm_session_hook.py --json-out  # emit advisory JSON without stdin
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

CODING_MARKERS = (
    "package.json", "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg",
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "composer.json", "Gemfile",
    "index.html", "manage.py", "main.py", "app.py", "server.py", "Dockerfile",
)
CODE_DIRS = ("src", "apps", "lib", "app", "server", "workers", "services", "workflow")
CODE_SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb", ".php",
    ".c", ".cpp", ".cs", ".kt", ".swift", ".vue", ".svelte", ".sh",
}
VCM_SKELETON = ("AGENTS.md", "NOW.md", "CHANGELOG.md")


def project_root() -> Path:
    """Resolve the project root from this file's location, then fall back to cwd."""
    me = Path(__file__).resolve()
    candidates = [me.parent, me.parent.parent, me.parent.parent.parent]
    for p in candidates:
        if (p / "AGENTS.md").is_file():
            return p
    for p in candidates:
        if (p / "tools").is_dir() or (p / ".vibecoding-manager").exists():
            return p
    return Path.cwd()


def _has(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def _code_suffix_count(root: Path) -> int:
    if not root.is_dir():
        return 0
    count = 0
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in CODE_SUFFIXES and "node_modules" not in p.parts:
            count += 1
            if count > 3:
                break
    return count


def _coding_signals(root: Path) -> list[str]:
    found: list[str] = []
    for m in CODING_MARKERS:
        if _has(root, m):
            found.append(m)
    for d in CODE_DIRS:
        if (root / d).is_dir() and any((root / d).iterdir()):
            found.append(d + "/")
    suffix_count = _code_suffix_count(root)
    if suffix_count >= 3:
        found.append(f"{suffix_count}+ source files")
    return found


def _detect(root: Path) -> tuple[str, list[str]]:
    if _has(root, ".vibecoding-manager"):
        return "managed", [".vibecoding-manager/"]
    if all(_has(root, p) for p in VCM_SKELETON) and (root / "docs" / "04-workflow").is_dir():
        return "vcm-shaped", ["AGENTS.md", "NOW.md", "CHANGELOG.md", "docs/04-workflow/"]
    signals = _coding_signals(root)
    if signals:
        return "coding", signals
    return "ambiguous", []


def _advisory(state: str, signals: list[str], root: Path, full: str = "") -> str:
    lines = ["[vibe-coding-manager session hook]"]
    if state == "managed":
        lines.append(
            "此项目已由 VibeCoding_Manager 托管（.vibecoding-manager/）。"
            "遵循 AGENTS.md 启动契约：先读 NOW.md，再按路由读所需权威文档；"
            "提交前运行 tools/check_drift.py，发布前运行 tools/selfqa.py。"
        )
    elif state == "vcm-shaped":
        lines.append(
            "项目已有 VCM 结构（AGENTS.md/NOW/CHANGELOG/docs 五层），但尚缺 .vibecoding-manager/，"
            "因此只是 dogfooding，未被正式接管。如需正式托管，显式调用 $vibe-coding-manager 走 adopt"
            "（会写 baseline/备份/回执）；否则按方法论自律即可。"
        )
    elif state == "coding":
        joined = ", ".join(signals[:6])
        lines.append(
            f"识别为 Coding 项目（信号：{joined}），当前未由 VCM 管理。"
            "如需纳入，显式调用 $vibe-coding-manager 做一次无写入 assess，再按确认结果 adopt。"
        )
    else:
        lines.append(
            "目录为空或仅含笔记类文件，无法判定是否 Coding 项目。请确认意图："
            "①灵感/草稿箱——仅记录，不建立 .vibecoding-manager，不接管；"
            "②Coding 项目——走标准 adopt（上下文预算 + selfqa + 项目级 hook）。"
            "vibe-coding-manager 默认不自动接管。"
        )
    if full:
        lines.append(full)
    lines.append(f"(root: {root})")
    return "\n".join(lines)


def _full_check(root: Path) -> str:
    """Run the fast read-only gates and return a one-line report (fail-open)."""
    reports: list[str] = []
    tool = root / "tools"
    for name in ("selfqa.py", "context_budget.py"):
        if not (tool / name).is_file():
            continue
        try:
            proc = subprocess.run(
                [sys.executable, str(tool / name)],
                cwd=root, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=20,
            )
            status = "ok" if proc.returncode == 0 else "fail"
            reports.append(f"{name.replace('.py', '')}={status}")
        except Exception as exc:  # pragma: no cover - defensive
            reports.append(f"{name.replace('.py', '')}=error")
    return "checks: " + (", ".join(reports) if reports else "not available")


def build_advisory(root: Path, event: dict | None = None) -> str:
    state, signals = _detect(root)
    full = ""
    if os.environ.get("VCM_HOOK_CHECK") == "1" or _has(root, ".vibecoding-manager/hook_full"):
        full = _full_check(root)
    return _advisory(state, signals, root, full)


def emit(root: Path, event: dict | None = None) -> int:
    context = build_advisory(root, event)
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="VibeCoding_Manager project-scoped SessionStart hook")
    ap.add_argument("--state", action="store_true", help="print detected state only")
    ap.add_argument("--json-out", action="store_true", help="emit advisory JSON without stdin")
    args = ap.parse_args()

    event: dict | None = None
    if not args.state and not args.json_out:
        try:
            event = json.loads(sys.stdin.read() or "{}")
        except Exception:
            event = {}
    root = project_root()
    if args.state:
        state, signals = _detect(root)
        print(json.dumps({"root": str(root), "state": state, "signals": signals},
                         ensure_ascii=False, indent=2))
        return 0
    try:
        return emit(root, event)
    except Exception:
        # Never break a managed session; emit nothing and exit 0 on unexpected errors.
        return 0


if __name__ == "__main__":
    sys.exit(main())
