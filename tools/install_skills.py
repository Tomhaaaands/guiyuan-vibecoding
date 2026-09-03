#!/usr/bin/env python3
"""Install this repo's skills into a user-chosen skills root, and self-check the kit.

Usage:
  python tools/install_skills.py [--skills-dir PATH] [--force]
  python tools/install_skills.py --doctor [--skills-dir PATH]
  python tools/install_skills.py --discover

Behavior:
  Copies reusable skills/iteration-close-loop and skills/vibe-coding-manager into
  the explicit --skills-dir, VIBECODING_SKILLS_HOME, or the local agent fallback;
  skips existing skills, --force overwrites.
  --doctor prints the kit version, checks both skills are installed intact, and runs
  tools/check_drift.py to prove the distribution is healthy.
  --discover lists known agent skill roots read-only without writing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
SKILLS = ("iteration-close-loop", "vibe-coding-manager", "vibe-coding-install")
VERSION_FILE = ROOT / "VERSION"


def version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "unknown"


def _validate_installed(dest_root: Path) -> list[str]:
    """Return installability errors for the installed tree (empty means healthy)."""
    errors: list[str] = []
    for name in SKILLS:
        if not (dest_root / name / "SKILL.md").is_file():
            errors.append(f"{name}: missing SKILL.md")
    mgr = dest_root / "vibe-coding-manager"
    if not (mgr / "assets" / "project").is_dir():
        errors.append("vibe-coding-manager: missing assets/project")
    if not (mgr / "profiles").is_dir():
        errors.append("vibe-coding-manager: missing profiles")
    # The published project template must carry the self-QA gate.
    if not (mgr / "assets" / "project" / "tools" / "selfqa.py").is_file():
        errors.append("vibe-coding-manager: assets/project/tools/selfqa.py missing")
    # ...and the project-scoped SessionStart hook runner.
    if not (mgr / "assets" / "project" / "tools" / "vcm_session_hook.py").is_file():
        errors.append("vibe-coding-manager: assets/project/tools/vcm_session_hook.py missing")
    if not (dest_root / "vibe-coding-install" / "VERSION").is_file():
        errors.append("vibe-coding-install: missing VERSION")
    return errors


def resolve_skills_root(skills_dir: str | None) -> Path:
    if skills_dir:
        return Path(skills_dir).expanduser().resolve()
    env = os.environ.get("VIBECODING_SKILLS_HOME")
    if env:
        return Path(env).expanduser().resolve()
    codex = os.environ.get("CODEX_HOME", Path.home() / ".codex")
    return Path(codex).expanduser() / "skills"


def discover() -> None:
    candidates = [
        ("Local agent default", resolve_skills_root(None)),
        ("Claude Code", Path.home() / ".claude" / "skills"),
        ("Cursor", Path.home() / ".cursor" / "skills"),
    ]
    print("== known agent skill roots (read-only, not exhaustive) ==")
    found = False
    for label, root in candidates:
        print(f"  {label}: {root} ({'exists' if root.exists() else 'not found'})")
        found = found or root.exists()
    if not found:
        print("  none found; use --skills-dir <path> for an explicit shared or agent directory")
    else:
        print("  confirm one path with --skills-dir <path> before writing")


def doctor(skills_root: Path) -> int:
    print(f"VibeCoding_Manager v{version()} · doctor")
    ok = True
    for name in SKILLS:
        sk = skills_root / name / "SKILL.md"
        if sk.is_file():
            print(f"  [ok] skill installed: {name}")
        else:
            print(f"  [missing] skill not installed: {name} (run: python tools/install_skills.py)")
            ok = False
    for err in _validate_installed(skills_root):
        print(f"  [broken] {err}")
        ok = False
    rc = subprocess.run([sys.executable, str(ROOT / "tools" / "check_drift.py")], cwd=ROOT).returncode
    if rc == 0:
        print("  [ok] check_drift passed (repo is healthy)")
    else:
        print("  [fail] check_drift failed — fix before distributing")
        ok = False
    print("doctor " + ("passed" if ok else "found issues"))
    return 0 if ok else 1


def install(force: bool, dest_root: Path) -> None:
    args, rc = _install_transactional(dest_root, ROOT / "skills", SKILLS, force)
    if rc != 0:
        raise SystemExit(rc)
    if backed_up := args["backed_up"]:
        print(f"backup: {args['backup_root']} ({', '.join(backed_up)})")
    print(f"VibeCoding_Manager v{version()} installed.")
    print("next: open your project folder (empty or existing), start a new conversation, invoke $vibe-coding-manager.")


def _install_transactional(dest_root: Path, src_root: Path, names: tuple[str, ...], force: bool) -> tuple[dict, int]:
    """Back up, atomically swap, validate, and roll back on failure."""
    dest_root.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = dest_root / ".vibecoding-manager-backups" / stamp
    plan: list[tuple[str, Path, Path, bool]] = []
    for name in names:
        src = src_root / name
        dst = dest_root / name
        if not src.is_dir():
            print(f"[error] missing source skill: {src}")
            return {"backup_root": backup_root, "backed_up": []}, 1
        if dst.exists() and not force:
            print(f"already installed, skipped: {name} (--force to overwrite)")
            continue
        plan.append((name, src, dst, dst.exists()))

    if not plan:
        return {"backup_root": backup_root, "backed_up": []}, _install_finish(dest_root, force)

    staged: list[tuple[str, Path, Path, bool, Path]] = []
    try:
        for name, src, dst, existed in plan:
            tmp = dst.with_name(dst.name + f".tmp-{stamp}")
            if tmp.exists():
                shutil.rmtree(tmp)
            shutil.copytree(src, tmp)
            staged.append((name, dst, existed, tmp))
    except OSError as exc:
        for _name, _dst, _existed, tmp in staged:
            if tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)
        print(f"[error] staging failed: {exc}")
        return {"backup_root": backup_root, "backed_up": []}, 1

    backed_up: list[str] = []
    installed: list[tuple[str, Path, bool]] = []
    try:
        for name, dst, existed, tmp in staged:
            if existed:
                backup = backup_root / name
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(dst, backup)
                backed_up.append(name)
                shutil.rmtree(dst)
            os.replace(tmp, dst)
            installed.append((name, dst, existed))
            print(f"installed: {dst}")
        errors = _validate_installed(dest_root)
        if errors:
            raise RuntimeError("; ".join(errors))
    except (OSError, RuntimeError) as exc:
        _rollback(installed, backup_root)
        print(f"[rollback] install failed: {exc}")
        print(f"[rollback] backup retained at: {backup_root}")
        return {"backup_root": backup_root, "backed_up": backed_up}, 1

    return {"backup_root": backup_root, "backed_up": backed_up}, 0


def _rollback(installed: list[tuple[str, Path, bool]], backup_root: Path) -> None:
    for name, dst, existed in reversed(installed):
        backup = backup_root / name
        if existed and backup.is_dir():
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(backup, dst)
            print(f"  restored: {name}")
        elif not existed:
            shutil.rmtree(dst, ignore_errors=True)
            print(f"  removed newly installed: {name}")


def _install_finish(dest_root: Path, force: bool) -> int:
    errors = _validate_installed(dest_root)
    if errors:
        for e in errors:
            print(f"  [broken] {e}")
        return 1
    print("all skills already installed and healthy; use --force to overwrite")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Install VibeCoding_Manager skills and self-check the kit")
    ap.add_argument("--force", action="store_true", help="overwrite existing skills")
    ap.add_argument("--doctor", action="store_true", help="verify install + repo health (no writes)")
    ap.add_argument("--skills-dir", default=None, help="explicit global skills root")
    ap.add_argument("--discover", action="store_true", help="list known agent skill roots read-only")
    args = ap.parse_args()
    if args.discover:
        discover()
        return
    dest_root = resolve_skills_root(args.skills_dir)
    print(f"skills root: {dest_root}")
    if args.doctor:
        sys.exit(doctor(dest_root))
    install(args.force, dest_root)


if __name__ == "__main__":
    main()
