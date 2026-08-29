#!/usr/bin/env python3
"""One-click installer bundled as the luban-install skill (self-contained).

Usage:
  python <skill>/scripts/install.py                 # install/update skills + doctor
  python <skill>/scripts/install.py --target <dir>  # ... then scaffold that project
  python <skill>/scripts/install.py --force         # overwrite existing skill copies

Behavior:
  1. Verifies Python >= 3.11 (bootstrap profile loading needs tomllib);
  2. Installs the two bundled skills (iteration-close-loop, project-bootstrap) from this
     skill's assets into $CODEX_HOME/skills (idempotent; --force overwrites);
  3. Doctor: verifies both skills are installed and the bundled template is complete
     (review-checklist.md + roadmap.md present);
  4. With --target: scaffolds that project via the installed project-bootstrap skill;
  5. Prints next steps.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SKILL_ROOT = Path(__file__).resolve().parent.parent
BUNDLED = SKILL_ROOT / "assets" / "skills"
SKILLS = ("iteration-close-loop", "project-bootstrap")
VERSION = "1.0.0"
MIN_PY = (3, 11)


def codex_skills() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills"


def doctor(dest: Path) -> int:
    ok = True
    for name in SKILLS:
        sk = dest / name / "SKILL.md"
        if sk.is_file():
            print(f"  [ok] skill installed: {name}")
        else:
            print(f"  [missing] skill not installed: {name} (run install.py)")
            ok = False
    template = dest / "project-bootstrap" / "assets" / "project" / "docs" / "04-workflow"
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
    for name in SKILLS:
        src = BUNDLED / name
        dst = dest / name
        if dst.exists() and not force:
            print(f"already installed, skipped: {name} (--force to overwrite)")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"installed: {dst}")
    print(f"luban-install v{VERSION} done.")


def main() -> None:
    ap = argparse.ArgumentParser(description="One-click install of the _bootstrap kit skills")
    ap.add_argument("--target", default=None, help="project folder to scaffold after install (optional)")
    ap.add_argument("--name", default=None, help="project name (default: target folder name)")
    ap.add_argument("--profile", default=None, help="project-type preset or custom .toml path")
    ap.add_argument("--dimension", action="append", default=[], metavar="key=value")
    ap.add_argument("--module", action="append", default=[], metavar="name=kw1,kw2")
    ap.add_argument("--code", action="append", default=[], metavar="name=dir")
    ap.add_argument("--template", choices=["default"], default=None)
    ap.add_argument("--python", default="auto", metavar="auto|system|install|<path>")
    ap.add_argument("--env", choices=["auto", "shared", "isolated", "reuse", "skip", "create", "uv"],
                    default="auto")
    ap.add_argument("--no-venv", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite existing skills")
    ap.add_argument("--no-doctor", action="store_true", help="skip the doctor self-check")
    args = ap.parse_args()

    if sys.version_info < MIN_PY:
        print(f"[error] Python {MIN_PY[0]}.{MIN_PY[1]}+ required (found {sys.version.split()[0]}).")
        sys.exit(1)

    dest = codex_skills()
    print(f"luban-install v{VERSION}")
    print(f"skill root : {SKILL_ROOT}")
    print(f"skills dest: {dest}")
    print()

    install(dest, args.force)
    if not args.no_doctor:
        rc = doctor(dest)
        if rc != 0:
            sys.exit(rc)

    if args.target:
        bootstrap = dest / "project-bootstrap" / "scripts" / "bootstrap.py"
        if not bootstrap.is_file():
            print(f"[error] project-bootstrap skill missing: {bootstrap}")
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
        if args.template:
            cmd += ["--template", args.template]
        if args.python != "auto":
            cmd += ["--python", args.python]
        if args.env != "auto":
            cmd += ["--env", args.env]
        if args.no_venv:
            cmd.append("--no-venv")
        print(f"$ python {' '.join(cmd)}")
        subprocess.run([sys.executable, *cmd], check=True)

    print()
    print("one-click install complete ✓")
    if args.target:
        print("  next: open a NEW conversation in that project and start your first real task.")
    else:
        print("  next: invoke $project-bootstrap in a new project conversation, or")
        print("        rerun with --target <folder> to scaffold an existing project.")


if __name__ == "__main__":
    main()
