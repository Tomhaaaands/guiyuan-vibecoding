#!/usr/bin/env python3
"""One-click installer for the Guiyuan Vibecoding kit.

Usage:
  python tools/one_click_install.py                 # install skills + doctor
  python tools/one_click_install.py --target <dir>  # ... then scaffold that project
  install.bat  (Windows) / ./install.sh (macOS/Linux)

Behavior:
  1. Verifies Python >= 3.11 (tomllib needed by profile loading);
  2. Installs the three kit skills (guiyuan-iteration-close-loop, guiyuan-vibecoding, guiyuan-vibecoding-install)
     into --skills-dir, VIBECODING_SKILLS_HOME, or the Codex fallback (idempotent; --force overwrites);
  3. Runs the built-in --doctor self-check (no writes);
  4. With --target: scaffolds that project via bootstrap.py (pass-through args);
  5. Prints next steps.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
INSTALL = ROOT / "tools" / "install_skills.py"
BOOTSTRAP = ROOT / "skills" / "guiyuan-vibecoding" / "scripts" / "bootstrap.py"
MIN_PY = (3, 11)


def version() -> str:
    v = ROOT / "VERSION"
    return v.read_text(encoding="utf-8").strip() if v.exists() else "unknown"


def check_python() -> None:
    if sys.version_info < MIN_PY:
        print(f"[error] Python {MIN_PY[0]}.{MIN_PY[1]}+ required (found {sys.version.split()[0]}).")
        print("        Install Python 3.11+ first: https://www.python.org/downloads/")
        sys.exit(1)


def run(args: list[str]) -> None:
    print(f"$ python {' '.join(args)}")
    subprocess.run([sys.executable, *args], check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="One-click install + optional project scaffold for Guiyuan Vibecoding")
    ap.add_argument("--target", default=None, help="project folder to scaffold after install (optional)")
    ap.add_argument("--name", default=None, help="project name (default: target folder name)")
    ap.add_argument("--profile", default=None, help="project-type preset or custom .toml path")
    ap.add_argument("--dimension", action="append", default=[], metavar="key=value",
                    help="dimension override (repeatable): deploy/data/runtime/surface")
    ap.add_argument("--module", action="append", default=[], metavar="name=kw1,kw2",
                    help="business module (repeatable)")
    ap.add_argument("--code", action="append", default=[], metavar="name=dir",
                    help="module code dir (repeatable)")
    ap.add_argument("--intent", default=None,
                    help="one-sentence project description used by scaffold intent resolution")
    ap.add_argument("--template", choices=["default"], default=None,
                    help="default template: web + api + db + worker + tests")
    ap.add_argument("--python", default="auto", metavar="auto|system|install|<path>",
                    help="Python runtime for the scaffolded project (default: auto)")
    ap.add_argument("--env", choices=["auto", "shared", "isolated", "reuse", "skip", "create", "uv"],
                    default="auto", help="dependency policy for the scaffolded project (default: auto)")
    ap.add_argument("--no-venv", action="store_true", help="alias for --env skip")
    ap.add_argument("--mode", choices=["auto", "assess", "adopt", "scaffold"], default=None,
                    help="project mode: existing code is assessed read-only before an explicit adopt")
    ap.add_argument("--assessment", default=None, help="assessment JSON required by --mode adopt")
    ap.add_argument("--workflow", action="append", default=[], metavar="name=keep|map|managed",
                    help="confirmed workflow choice for --mode adopt (repeatable)")
    ap.add_argument("--existing-system", action="append", default=[], metavar="NAME",
                    help="similar project-management system declared by the user (repeatable)")
    ap.add_argument("--compat-policy", choices=["full-takeover", "takeover", "defer", "abandon"], default=None,
                    help="low-match decision from the compatibility gate")
    ap.add_argument("--system-policy", choices=["keep-map", "auto-takeover", "abandon"], default=None,
                    help="similar-system decision from the compatibility gate")
    ap.add_argument("--json", action="store_true", help="print JSON in --mode assess")
    ap.add_argument("--deps", choices=["auto", "commands", "skip"], default=None,
                    help="dependency installs for the target project: auto/commands/skip")
    ap.add_argument("--github", default=None, help="GitHub repo URL to set as origin")
    ap.add_argument("--push", action="store_true", help="attempt initial push after git init/remote")
    ap.add_argument("--force", action="store_true", help="overwrite existing skills")
    ap.add_argument("--no-doctor", action="store_true", help="skip the post-install doctor")
    ap.add_argument("--skills-dir", default=None, help="explicit global skills root")
    ap.add_argument("--skill-location", choices=["auto", "project", "global", "skip"], default=None,
                    help="close-loop install location for the scaffolded project")
    ap.add_argument("--discover", action="store_true", help="list known agent skill roots read-only")
    ap.add_argument("--preflight", action="store_true", help="read-only inventory before install/update")
    ap.add_argument("--uninstall", action="store_true", help="remove only Guiyuan-owned skills; no confirmation")
    args = ap.parse_args()

    check_python()
    if args.discover:
        run([str(INSTALL), "--discover"])
        return
    if args.preflight or args.uninstall:
        cmd = [str(INSTALL), "--preflight" if args.preflight else "--uninstall"]
        if args.skills_dir:
            cmd += ["--skills-dir", args.skills_dir]
        run(cmd)
        return
    print(f"Guiyuan Vibecoding one-click installer v{version()}")
    print(f"kit root : {ROOT}")
    print("skills   : explicit --skills-dir > VIBECODING_SKILLS_HOME > Codex fallback")
    print()

    # Diagnostics must not change either the target project or the global skill root.
    if args.target and args.mode == "assess":
        assess = [str(BOOTSTRAP), args.target, "--mode", "assess"]
        if args.name:
            assess += ["--name", args.name]
        for name in args.existing_system:
            assess += ["--existing-system", name]
        if args.json:
            assess.append("--json")
        run(assess)
        return

    install_cmd = [str(INSTALL), *(["--force"] if args.force else [])]
    if args.skills_dir:
        install_cmd += ["--skills-dir", args.skills_dir]
    run(install_cmd)

    if not args.no_doctor:
        doctor_cmd = [str(INSTALL), "--doctor"]
        if args.skills_dir:
            doctor_cmd += ["--skills-dir", args.skills_dir]
        run(doctor_cmd)

    if args.target:
        bootstrap_args = [str(BOOTSTRAP), args.target]
        if args.name:
            bootstrap_args += ["--name", args.name]
        if args.profile:
            bootstrap_args += ["--profile", args.profile]
        for d in args.dimension:
            bootstrap_args += ["--dimension", d]
        for m in args.module:
            bootstrap_args += ["--module", m]
        for c in args.code:
            bootstrap_args += ["--code", c]
        if args.intent:
            bootstrap_args += ["--intent", args.intent]
        if args.template:
            bootstrap_args += ["--template", args.template]
        if args.skills_dir:
            bootstrap_args += ["--skills-dir", args.skills_dir]
        if args.skill_location:
            bootstrap_args += ["--skill-location", args.skill_location]
        if args.python != "auto":
            bootstrap_args += ["--python", args.python]
        if args.env != "auto":
            bootstrap_args += ["--env", args.env]
        if args.no_venv:
            bootstrap_args.append("--no-venv")
        if args.mode:
            bootstrap_args += ["--mode", args.mode]
        if args.assessment:
            bootstrap_args += ["--assessment", args.assessment]
        for choice in args.workflow:
            bootstrap_args += ["--workflow", choice]
        if args.compat_policy:
            bootstrap_args += ["--compat-policy", args.compat_policy]
        if args.system_policy:
            bootstrap_args += ["--system-policy", args.system_policy]
        if args.json:
            bootstrap_args.append("--json")
        if args.deps:
            bootstrap_args += ["--deps", args.deps]
        if args.github:
            bootstrap_args += ["--github", args.github]
        if args.push:
            bootstrap_args.append("--push")
        run(bootstrap_args)

    print()
    print("one-click install complete ✓")
    if args.target:
        print("  next: open a NEW conversation in that project and start your first real task.")
    else:
        print("  next: invoke $guiyuan-vibecoding in your project conversation (empty folder = scaffold,")
        print("        existing code = adopt), or rerun with --target <folder> to manage it now.")


if __name__ == "__main__":
    main()
