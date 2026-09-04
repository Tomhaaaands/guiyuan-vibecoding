#!/usr/bin/env python3
"""One-click installer bundled as the guiyuan-vibecoding-install skill (self-contained).

Usage:
  python <skill>/scripts/install.py [--skills-dir PATH]  # install/update + doctor
  python <skill>/scripts/install.py --discover           # read-only candidate list
  python <skill>/scripts/install.py --target <dir>       # ... then scaffold that project
  python <skill>/scripts/install.py --force              # overwrite existing skill copies

Behavior:
  1. Verifies Python >= 3.11 (bootstrap profile loading needs tomllib);
  2. Installs the two bundled skills (guiyuan-iteration-close-loop, guiyuan-vibecoding) from this
     skill's assets into --skills-dir, VIBECODING_SKILLS_HOME, or the Codex fallback
     (idempotent; --force overwrites);
  3. Doctor: verifies both skills are installed and the bundled template is complete
     (review-checklist.md + roadmap.md present);
  4. With --target: scaffolds that project via the installed guiyuan-vibecoding skill;
  5. Prints next steps.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SKILL_ROOT = Path(__file__).resolve().parent.parent
BUNDLED = SKILL_ROOT / "assets" / "skills"
SKILLS = ("guiyuan-iteration-close-loop", "guiyuan-vibecoding")
LEGACY_SKILLS = {
    "vibe-coding-manager": "guiyuan-vibecoding",
    "vibe-coding-install": "guiyuan-vibecoding-install",
    "iteration-close-loop": "guiyuan-iteration-close-loop",
}
MANIFEST_NAME = ".guiyuan-vibecoding-install.json"
MIN_PY = (3, 11)


def version() -> str:
    """Kit version, single-sourced from this skill's VERSION file (bundled with the skill).

    The file travels with the self-contained skill into the installed skills root; check_drift gates it
    against the repo root VERSION so the two never drift.
    """
    v = SKILL_ROOT / "VERSION"
    return v.read_text(encoding="utf-8").strip() if v.is_file() else "unknown"


def _validate_installed(dest: Path) -> list[str]:
    """Return installability errors for the installed tree (empty means healthy)."""
    errors: list[str] = []
    for name in SKILLS:
        if not (dest / name / "SKILL.md").is_file():
            errors.append(f"{name}: missing SKILL.md")
    mgr = dest / "guiyuan-vibecoding"
    if not (mgr / "assets" / "project").is_dir():
        errors.append("guiyuan-vibecoding: missing assets/project")
    if not (mgr / "profiles").is_dir():
        errors.append("guiyuan-vibecoding: missing profiles")
    # The published project template must carry the self-QA gate.
    if not (mgr / "assets" / "project" / "tools" / "selfqa.py").is_file():
        errors.append("guiyuan-vibecoding: assets/project/tools/selfqa.py missing")
    # ...and the project-scoped SessionStart hook runner.
    if not (mgr / "assets" / "project" / "tools" / "vcm_session_hook.py").is_file():
        errors.append("guiyuan-vibecoding: assets/project/tools/vcm_session_hook.py missing")
    if not (mgr / "assets" / "project" / "tools" / "render_project_home.py").is_file():
        errors.append("guiyuan-vibecoding: assets/project/tools/render_project_home.py missing")
    if not (mgr / "assets" / "project" / "templates" / "guiyuan-vibecoding-home.html").is_file():
        errors.append("guiyuan-vibecoding: project-home template missing")
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


def _tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc":
            digest.update(item.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def _skill_frontmatter_name(path: Path) -> str | None:
    skill = path / "SKILL.md"
    if not skill.is_file():
        return None
    for line in skill.read_text(encoding="utf-8", errors="replace").splitlines()[:12]:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def _write_manifest(dest: Path) -> None:
    payload = {
        "schema_version": 1,
        "product": "guiyuan-vibecoding",
        "version": version(),
        "skills": {
            name: {"path": name, "sha256": _tree_hash(dest / name)}
            for name in SKILLS if (dest / name).is_dir()
        },
    }
    (dest / MANIFEST_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def preflight(dest: Path) -> int:
    print(f"Guiyuan Vibecoding preflight: {dest}")
    if not dest.exists():
        print("  target root: absent (clean install)")
        return 0
    found = False
    for name in SKILLS:
        path = dest / name
        if path.exists():
            found = True
            print(f"  [current] {name}: {_skill_frontmatter_name(path) or 'unverified'}")
    for old, new in LEGACY_SKILLS.items():
        path = dest / old
        if path.exists():
            found = True
            print(f"  [legacy] {old} -> {new}: {_skill_frontmatter_name(path) or 'unverified'}")
    print(f"  manifest: {'present' if (dest / MANIFEST_NAME).is_file() else 'absent (legacy/untracked install)'}")
    others = [p.name for p in dest.iterdir() if p.is_dir() and p.name not in set(SKILLS) | set(LEGACY_SKILLS) and (p / "SKILL.md").is_file()]
    if others:
        print("  [similar/other] untouched: " + ", ".join(sorted(others)))
    if not found:
        print("  no Guiyuan Vibecoding skills found")
    return 0


def uninstall(dest: Path) -> int:
    preflight(dest)
    removed, preserved = [], []
    expected = set(SKILLS) | set(LEGACY_SKILLS)
    manifest_path = dest / MANIFEST_NAME
    manifest = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = {}
    for name in sorted(expected):
        path = dest / name
        if not path.is_dir() or _skill_frontmatter_name(path) not in expected:
            continue
        expected_hash = manifest.get("skills", {}).get(name, {}).get("sha256")
        if name in SKILLS and expected_hash and expected_hash != _tree_hash(path):
            preserved.append(name)
            continue
        shutil.rmtree(path)
        removed.append(name)
    if manifest_path.is_file() and not preserved:
        manifest_path.unlink()
    print("uninstall: " + (", ".join(removed) if removed else "no owned skills removed"))
    if preserved:
        print("preserved user-modified VCM skills: " + ", ".join(preserved))
    remaining = [
        name for name in sorted(expected)
        if (dest / name).is_dir() and _skill_frontmatter_name(dest / name) in expected
    ]
    if remaining:
        print("post-uninstall: owned paths remaining (preserved or unverified): " + ", ".join(remaining))
    else:
        print("post-uninstall: agent skill root clean of owned Guiyuan paths")
    print("user skills, plugins, project files, and Butler MCP were not touched.")
    return 0


def doctor(dest: Path) -> int:
    ok = True
    for name in SKILLS:
        sk = dest / name / "SKILL.md"
        if sk.is_file():
            print(f"  [ok] skill installed: {name}")
        else:
            print(f"  [missing] skill not installed: {name} (run install.py)")
            ok = False
    for err in _validate_installed(dest):
        print(f"  [broken] {err}")
        ok = False
    template = dest / "guiyuan-vibecoding" / "assets" / "project" / "docs" / "04-workflow"
    for f in ("review-checklist.md", "roadmap.md"):
        if (template / f).is_file():
            print(f"  [ok] template file: docs/04-workflow/{f}")
        else:
            print(f"  [missing] template file: docs/04-workflow/{f}")
            ok = False
    print("doctor " + ("passed" if ok else "found issues"))
    return 0 if ok else 1


def install(dest: Path, force: bool) -> None:
    args, rc = _install_transactional(dest, BUNDLED, SKILLS, force)
    if rc != 0:
        raise SystemExit(rc)
    if backed_up := args["backed_up"]:
        print(f"backup: {args['backup_root']} ({', '.join(backed_up)})")
    _write_manifest(dest)
    print(f"guiyuan-vibecoding-install v{version()} done.")


def _install_transactional(dest: Path, src_root: Path, names: tuple[str, ...], force: bool) -> tuple[dict, int]:
    """Back up, atomically swap, validate, and roll back on failure."""
    dest.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = dest / ".guiyuan-vibecoding-backups" / stamp
    plan: list[tuple[str, Path, Path, bool]] = []
    for name in names:
        src = src_root / name
        dst = dest / name
        if not src.is_dir():
            print(f"[error] missing source skill: {src}")
            return {"backup_root": backup_root, "backed_up": []}, 1
        if dst.exists() and not force:
            print(f"already installed, skipped: {name} (--force to overwrite)")
            continue
        plan.append((name, src, dst, dst.exists()))

    if not plan:
        return {"backup_root": backup_root, "backed_up": []}, _install_finish(dest)

    staged: list[tuple[str, Path, bool, Path]] = []
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
        errors = _validate_installed(dest)
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


def _install_finish(dest: Path) -> int:
    errors = _validate_installed(dest)
    if errors:
        for e in errors:
            print(f"  [broken] {e}")
        return 1
    print("all skills already installed and healthy; use --force to overwrite")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="One-click install of the Guiyuan Vibecoding kit skills")
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
    ap.add_argument("--preflight", action="store_true", help="read-only inventory of old/current/similar skills")
    ap.add_argument("--uninstall", action="store_true", help="remove only Guiyuan-owned skills; no confirmation")
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
        bootstrap = BUNDLED / "guiyuan-vibecoding" / "scripts" / "bootstrap.py"
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
    if args.preflight:
        sys.exit(preflight(dest))
    if args.uninstall:
        sys.exit(uninstall(dest))
    print(f"guiyuan-vibecoding-install v{version()}")
    print(f"skill root : {SKILL_ROOT}")
    print(f"skills dest: {dest}")
    print()

    install(dest, args.force)
    if not args.no_doctor:
        rc = doctor(dest)
        if rc != 0:
            sys.exit(rc)

    if args.target:
        bootstrap = dest / "guiyuan-vibecoding" / "scripts" / "bootstrap.py"
        if not bootstrap.is_file():
            print(f"[error] guiyuan-vibecoding skill missing: {bootstrap}")
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
        print("  next: invoke $guiyuan-vibecoding in a new project conversation, or")
        print("        rerun with --target <folder> to scaffold an existing project.")


if __name__ == "__main__":
    main()
