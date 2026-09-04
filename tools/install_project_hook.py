#!/usr/bin/env python3
"""Install a project-scoped Codex SessionStart hook for Guiyuan Vibecoding.

Writes <root>/.codex/hooks.json so the currently trusted project loads the
advisory runner at tools/vcm_session_hook.py. The hook only reads the project,
does not auto-takeover, and is non-blocking. Idempotent: re-running with the same
interpreter leaves the file unchanged.

Usage:
  python tools/install_project_hook.py [root] [--dry-run]

The hook command is pinned to the interpreter that ran this installer (or the
project's .venv/Scripts/python.exe if present), because the hook must exist long
after the install command finishes. Re-run after moving the project or changing
the interpreter.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

RUNNER_REL = "tools/vcm_session_hook.py"
HOOKS_REL = ".codex/hooks.json"


def _find_python(root: Path) -> Path:
    for rel in (".venv/Scripts/python.exe", "venv/Scripts/python.exe",
                ".venv/bin/python", "venv/bin/python"):
        candidate = root / rel
        if candidate.is_file():
            return candidate
    return Path(sys.executable)


def render(root: Path, python_exe: Path | None = None) -> dict:
    runner = (root / RUNNER_REL).resolve()
    py = python_exe or _find_python(root)
    command = f'"{py}" "{runner}"'
    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear|compact",
                    "hooks": [
                        {"type": "command", "command": command, "timeout": 20},
                    ],
                }
            ]
        }
    }


def install(root: Path, dry_run: bool = False) -> tuple[str, Path]:
    """Write .codex/hooks.json; return ('ok'|'unchanged'|'missing-runner'|'wrote', path)."""
    root = root.resolve()
    if not (root / RUNNER_REL).is_file():
        return "missing-runner", root / HOOKS_REL
    codex = root / ".codex"
    target = codex / "hooks.json"
    data = json.dumps(render(root), ensure_ascii=False, indent=2) + "\n"
    if target.is_file() and target.read_text(encoding="utf-8") == data:
        return "unchanged", target
    if dry_run:
        return "dry-run", target
    codex.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding="utf-8")
    return "ok", target


def main() -> int:
    ap = argparse.ArgumentParser(description="Install the project-scoped Codex SessionStart hook")
    ap.add_argument("target", nargs="?", default=".", help="project root (default: current)")
    ap.add_argument("--dry-run", action="store_true", help="show what would change")
    args = ap.parse_args()
    root = Path(args.target).resolve()
    rel = (root / HOOKS_REL).relative_to(root)
    status, path = install(root, args.dry_run)
    if status == "missing-runner":
        print(f"[warn] {rel}: {RUNNER_REL} missing; run bootstrap adopt/scaffold first")
        return 1
    print(f"[hook] {rel} ({status})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
