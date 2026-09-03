#!/usr/bin/env python3
"""One-click installer bundled as the vibe-coding-install skill (self-contained).

Usage:
  python <skill>/scripts/install.py [--skills-dir PATH]  # install/update + doctor
  python <skill>/scripts/install.py --discover           # read-only candidate list
  python <skill>/scripts/install.py --target <dir>       # ... then scaffold that project
  python <skill>/scripts/install.py --force              # overwrite existing skill copies

Behavior:
  1. Verifies Python >= 3.11 (bootstrap profile loading needs tomllib);
  2. Installs the two bundled skills (iteration-close-loop, vibe-coding-manager) from this
     skill's assets into --skills-dir, VIBECODING_SKILLS_HOME, or the Codex fallback
     (idempotent; --force overwrites);
  3. Doctor: verifies both skills are installed and the bundled template is complete
     (review-checklist.md + roadmap.md present);
  4. With --target: scaffolds that project via the installed vibe-coding-manager skill;
  5. Prints next steps.
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

SKILL_ROOT = Path(__file__).resolve().parent.parent
BUNDLED = SKILL_ROOT / "assets" / "skills"
SKILLS = ("iteration-close-loop", "vibe-coding-manager")
MIN_PY = (3, 11)


def version() -> str:
    """Kit version, single-sourced from this skill's VERSION file (bundled with the skill).

    The file travels with the self-contained skill into the installed skills root; check_drift gates it
    against the repo root VERSION so the two never drift.
    """
    v = SKILL_ROOT / "VERSION"
    return v.read_text(encoding="utf-8").strip() if v.is_file() else "unknown"


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
        ("Codex", resolve_skills_root(None)),
        ("Claude Code", Path.home() / ".claude" / "skills"),
        ("Cursor", Path.home() / ".cursor" / "skills"),
    ]
    print("== known agent skill roots (read-only, not exhaustive) ==")
    found = False
    for label, root in candidates:
        print(f"  {label}: {root} ({'exists' if root.exists() else 'not found'})")
        found = found or root.exists()
    if not found:
        print("  none found; use --skills-dir <path> for an explicit global directory")
    else:
        print("  confirm one path with --skills-dir <path> before writing")


def doctor(dest: Path) -> int:
    ok = True
    for name in SKILLS:
        sk = dest / name / "SKILL.md"
        if sk.is_file():
            print(f"  [ok] skill installed: {name}")
        else:
            print(f"  [missing] skill not installed: {name} (run install.py)")
            ok = False
    template = dest / "vibe-coding-manager" / "assets" / "project" / "docs" / "04-workflow"
    for f in ("review-checklist.md", "roadmap.md"):
        if (template / f).is_file():
            print(f"  [ok] template file: docs/04-workflow/{f}")
        else:
            print(f"  [missing] template file: docs/04-workflow/{f}")
            ok = False
    print("doctor " + ("passed" if ok else "found issues"))
    return 0 if ok else 1


def install(dest: Path, force: bool) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = dest / ".vibecoding-manager-backups" / stamp
    backed_up = []
    for name in SKILLS:
        src = BUNDLED / name
        dst = dest / name
        if dst.exists() and not force:
            print(f"already installed, skipped: {name} (--force to overwrite)")
            continue
        if dst.exists():
            backup = backup_root / name
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(dst, backup)
            backed_up.append(name)
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"installed: {dst}")
    if backed_up:
        print(f"backup: {backup_root} ({', '.join(backed_up)})")
    print(f"vibe-coding-install v{version()} done.")


def main() -> None:
    ap = argparse.ArgumentParser(description="One-click install of the VibeCoding_Manager kit skills")
    ap.add_argument("--target", default=None, help="project folder to scaffold after install (optional)")
    ap.add_argument("--name", default=None, help="project name (default: target folder name)")
    ap.add_argument("--profile", default=None, help="project-type preset or custom .toml path")
    ap.add_argument("--dimension", action="append", default=[], metavar="key=value")
    ap.add_argument("--module", action="append", default=[], metavar="name=kw1,kw2")
    ap.add_argument("--code", action="append", default=[], metavar="name=dir")
    ap.add_argument("--intent", default=None, help="one-sentence project description")
    ap.add_argument("--template", choices=["default"], default=None)
    ap.add_argument("--python", default="auto", metavar="auto|system|install|<path>")
    ap.add_argument("--env", choices=["auto", "shared", "isolated", "reuse", "skip", "create", "uv"],
                    default="auto")
    ap.add_argument("--no-venv", action="store_true")
    ap.add_argument("--mode", choices=["auto", "assess", "adopt", "scaffold"], default=None)
    ap.add_argument("--assessment", default=None)
    ap.add_argument("--workflow", action="append", default=[], metavar="name=keep|map|managed")
    ap.add_argument("--existing-system", action="append", default=[], metavar="NAME")
    ap.add_argument("--compat-policy", choices=["full-takeover", "takeover", "defer", "abandon"], default=None)
    ap.add_argument("--system-policy", choices=["keep-map", "auto-takeover", "abandon"], default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--deps", choices=["auto", "commands", "skip"], default=None)
    ap.add_argument("--github", default=None, help="GitHub repo URL to set as origin")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite existing skills")
    ap.add_argument("--no-doctor", action="store_true", help="skip the doctor self-check")
    ap.add_argument("--skills-dir", default=None, help="explicit global skills root")
    ap.add_argument("--skill-location", choices=["auto", "project", "global", "skip"], default=None,
                    help="close-loop install location for the scaffolded project")
    ap.add_argument("--discover", action="store_true", help="list known agent skill roots read-only")
    args = ap.parse_args()

    if sys.version_info < MIN_PY:
        print(f"[error] Python {MIN_PY[0]}.{MIN_PY[1]}+ required (found {sys.version.split()[0]}).")
        sys.exit(1)
    if args.discover:
        discover()
        return

    # Assessment is safe to run from the bundled copy and must not alter global skills.
    if args.target and args.mode == "assess":
        bootstrap = BUNDLED / "vibe-coding-manager" / "scripts" / "bootstrap.py"
        cmd = [str(bootstrap), args.target, "--mode", "assess"]
        if args.name:
            cmd += ["--name", args.name]
        for name in args.existing_system:
            cmd += ["--existing-system", name]
        if args.json:
            cmd.append("--json")
        subprocess.run([sys.executable, *cmd], check=True)
        return

    dest = resolve_skills_root(args.skills_dir)
    print(f"vibe-coding-install v{version()}")
    print(f"skill root : {SKILL_ROOT}")
    print(f"skills dest: {dest}")
    print()

    install(dest, args.force)
    if not args.no_doctor:
        rc = doctor(dest)
        if rc != 0:
            sys.exit(rc)

    if args.target:
        bootstrap = dest / "vibe-coding-manager" / "scripts" / "bootstrap.py"
        if not bootstrap.is_file():
            print(f"[error] vibe-coding-manager skill missing: {bootstrap}")
            sys.exit(1)
        cmd = [str(bootstrap), args.target]
        if args.name:
            cmd += ["--name", args.name]
        if args.profile:
            cmd += ["--profile", args.profile]
        for d in args.dimension:
            cmd += ["--dimension", d]
        for m in args.module:
            cmd += ["--module", m]
        for c in args.code:
            cmd += ["--code", c]
        if args.intent:
            cmd += ["--intent", args.intent]
        if args.template:
            cmd += ["--template", args.template]
        if args.skills_dir:
            cmd += ["--skills-dir", args.skills_dir]
        if args.skill_location:
            cmd += ["--skill-location", args.skill_location]
        if args.python != "auto":
            cmd += ["--python", args.python]
        if args.env != "auto":
            cmd += ["--env", args.env]
        if args.no_venv:
            cmd.append("--no-venv")
        if args.mode:
            cmd += ["--mode", args.mode]
        if args.assessment:
            cmd += ["--assessment", args.assessment]
        for choice in args.workflow:
            cmd += ["--workflow", choice]
        if args.compat_policy:
            cmd += ["--compat-policy", args.compat_policy]
        if args.system_policy:
            cmd += ["--system-policy", args.system_policy]
        if args.json:
            cmd.append("--json")
        if args.deps:
            cmd += ["--deps", args.deps]
        if args.github:
            cmd += ["--github", args.github]
        if args.push:
            cmd.append("--push")
        print(f"$ python {' '.join(cmd)}")
        subprocess.run([sys.executable, *cmd], check=True)

    print()
    print("one-click install complete ✓")
    if args.target:
        print("  next: open a NEW conversation in that project and start your first real task.")
    else:
        print("  next: invoke $vibe-coding-manager in a new project conversation, or")
        print("        rerun with --target <folder> to scaffold an existing project.")


if __name__ == "__main__":
    main()
