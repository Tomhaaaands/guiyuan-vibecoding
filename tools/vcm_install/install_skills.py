#!/usr/bin/env python3
"""Install this repo's skills into a user-chosen skills root, and self-check the kit.

Usage:
  python tools/install_skills.py [--skills-dir PATH] [--force]
  python tools/install_skills.py --preflight [--skills-dir PATH]
  python tools/install_skills.py --uninstall [--skills-dir PATH]
  python tools/install_skills.py --doctor [--skills-dir PATH]
  python tools/install_skills.py --discover

Behavior:
  Installs the single public skills/guiyuan-vibecoding entry point into the explicit
  --skills-dir, VIBECODING_SKILLS_HOME, or the local agent fallback; skips an existing
  skill, --force overwrites. The close-loop payload is internal and materialized only
  inside managed projects.
  --doctor prints the kit version, checks the public skill is installed intact, and runs
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
PUBLIC_SKILL = "guiyuan-vibecoding"
SKILLS = (PUBLIC_SKILL,)
# These names were public in <=0.1.x.  They are retired from the global discovery root but
# remain recognized for safe migration/uninstall; their contents are preserved outside that root.
AUXILIARY_SKILLS = ("guiyuan-iteration-close-loop", "guiyuan-vibecoding-install")
OWNED_SKILLS = SKILLS + AUXILIARY_SKILLS
LEGACY_SKILLS = {
    "vibe-coding-manager": "guiyuan-vibecoding",
    "vibe-coding-install": "guiyuan-vibecoding-install",
    "iteration-close-loop": "guiyuan-iteration-close-loop",
}
VERSION_FILE = ROOT / "VERSION"
MANIFEST_NAME = ".guiyuan-vibecoding-install.json"


def version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "unknown"


def _validate_installed(dest_root: Path) -> list[str]:
    """Return installability errors for the installed tree (empty means healthy)."""
    errors: list[str] = []
    for name in SKILLS:
        if not (dest_root / name / "SKILL.md").is_file():
            errors.append(f"{name}: missing SKILL.md")
    mgr = dest_root / "guiyuan-vibecoding"
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
    if not (mgr / "VERSION").is_file():
        errors.append("guiyuan-vibecoding: missing VERSION")
    if not (mgr / "assets" / "internal" / "iteration-close-loop" / "SKILL.md.template").is_file():
        errors.append("guiyuan-vibecoding: missing internal close-loop payload")
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


def _tree_hash(path: Path) -> str:
    """Stable hash for ownership checks; file names and bytes both matter."""
    import hashlib

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


def _write_manifest(dest_root: Path) -> None:
    import json

    payload = {
        "schema_version": 1,
        "product": "guiyuan-vibecoding",
        "version": version(),
        "skills": {
            name: {"path": name, "sha256": _tree_hash(dest_root / name)}
            for name in SKILLS if (dest_root / name).is_dir()
        },
    }
    (dest_root / MANIFEST_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def preflight(skills_root: Path) -> int:
    """Read-only inventory used before install/update and by Agent-native removal."""
    print(f"Guiyuan Vibecoding preflight: {skills_root}")
    if not skills_root.exists():
        print("  target root: absent (clean install)")
        return 0
    found = False
    for name in SKILLS:
        path = skills_root / name
        if path.exists():
            found = True
            print(f"  [current] {name}: {_skill_frontmatter_name(path) or 'unverified'}")
    for old, new in LEGACY_SKILLS.items():
        path = skills_root / old
        if path.exists():
            found = True
            print(f"  [legacy] {old} -> {new}: {_skill_frontmatter_name(path) or 'unverified'}")
    for name in AUXILIARY_SKILLS:
        path = skills_root / name
        if path.exists():
            found = True
            print(f"  [retired-public] {name}: will be hidden from the discovery root")
    manifest = skills_root / MANIFEST_NAME
    print(f"  manifest: {'present' if manifest.is_file() else 'absent (legacy/untracked install)'}")
    others = []
    for child in skills_root.iterdir():
        if child.is_dir() and child.name not in set(OWNED_SKILLS) | set(LEGACY_SKILLS):
            if (child / "SKILL.md").is_file():
                others.append(child.name)
    if others:
        print("  [similar/other] untouched: " + ", ".join(sorted(others)))
    if not found:
        print("  no Guiyuan Vibecoding skills found")
    return 0


def _is_reparse_point(path: Path) -> bool:
    """Detect Windows junctions without following them (safe migration/uninstall)."""
    try:
        attrs = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attrs & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT


def _retire_auxiliary(skills_root: Path) -> list[str]:
    """Move old public auxiliary entries outside the scanned skills root.

    Real directories are preserved in a sibling retirement bundle. Windows junctions are
    unlinked only, leaving their target directory untouched. This is intentionally separate
    from uninstall: an update hides old entries but never destroys their contents.
    """
    retired: list[str] = []
    if not skills_root.is_dir():
        return retired
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    retirement_root = skills_root.parent / ".guiyuan-vibecoding-retired" / skills_root.name / stamp
    for name in AUXILIARY_SKILLS:
        src = skills_root / name
        if not src.exists():
            continue
        if _is_reparse_point(src) or src.is_symlink():
            src.unlink()
        else:
            retirement_root.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(retirement_root / name))
        retired.append(name)
    if retired:
        print("retired public auxiliary entries: " + ", ".join(retired))
        print(f"preserved outside skills root: {retirement_root}")
    return retired


def pending_questions(skills_root: Path) -> list[str]:
    """Report post-install decisions without changing preserved user-owned content."""
    if not skills_root.is_dir():
        return []
    legacy = [name for name in LEGACY_SKILLS if (skills_root / name).exists()]
    similar = [
        child.name for child in skills_root.iterdir()
        if child.is_dir() and child.name not in set(OWNED_SKILLS) | set(LEGACY_SKILLS)
        and (child / "SKILL.md").is_file()
    ]
    questions: list[str] = []
    if legacy:
        questions.append(
            "旧版目录暂未删除（" + ", ".join(sorted(legacy)) + "），是否需要我在你确认后处理？"
        )
    if similar:
        questions.append(
            "检测到类似/其他 Skill（" + ", ".join(sorted(similar)) + "），是否保持现状并仅建立映射？"
        )
    if questions:
        print("\npending user decisions:")
        for question in questions:
            print(f"  question: {question}")
    return questions


def uninstall(skills_root: Path) -> int:
    """Remove only Guiyuan-owned skills; never touch other skills or project files."""
    preflight(skills_root)
    removed: list[str] = []
    preserved: list[str] = []
    expected = set(OWNED_SKILLS) | set(LEGACY_SKILLS)
    if skills_root.exists():
        for name in sorted(expected):
            path = skills_root / name
            if not path.is_dir() or _skill_frontmatter_name(path) not in expected:
                continue
            # A user-edited skill is still theirs to keep; ownership is proved by
            # the manifest when available, otherwise only exact VCM frontmatter is used.
            if name in SKILLS:
                manifest = skills_root / MANIFEST_NAME
                if manifest.is_file():
                    try:
                        import json
                        data = json.loads(manifest.read_text(encoding="utf-8"))
                        expected_hash = data.get("skills", {}).get(name, {}).get("sha256")
                        if expected_hash and expected_hash != _tree_hash(path):
                            preserved.append(name)
                            continue
                    except (OSError, ValueError):
                        preserved.append(name)
                        continue
            if _is_reparse_point(path) or path.is_symlink():
                path.unlink()
            else:
                shutil.rmtree(path)
            removed.append(name)
    manifest = skills_root / MANIFEST_NAME
    if manifest.is_file() and not preserved:
        manifest.unlink()
    print("uninstall: " + (", ".join(removed) if removed else "no owned skills removed"))
    if preserved:
        print("preserved user-modified VCM skills: " + ", ".join(preserved))
    remaining = [
        name for name in sorted(expected)
        if (skills_root / name).is_dir() and _skill_frontmatter_name(skills_root / name) in expected
    ]
    if remaining:
        print("post-uninstall: owned paths remaining (preserved or unverified): " + ", ".join(remaining))
    else:
        print("post-uninstall: agent skill root clean of owned Guiyuan paths")
    print("user skills, plugins, project files, and Butler MCP were not touched.")
    return 0


def doctor(skills_root: Path) -> int:
    print(f"Guiyuan Vibecoding v{version()} · doctor")
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
    _retire_auxiliary(dest_root)
    args, rc = _install_transactional(dest_root, ROOT / "skills", SKILLS, force)
    if rc != 0:
        raise SystemExit(rc)
    if backed_up := args["backed_up"]:
        print(f"backup: {args['backup_root']} ({', '.join(backed_up)})")
    _write_manifest(dest_root)
    print(f"Guiyuan Vibecoding v{version()} installed.")
    pending_questions(dest_root)
    print("next: 记得在新对话中 @guiyuan-vibecoding，进行一次初始化，再开始第一个真实任务。")


def _install_transactional(dest_root: Path, src_root: Path, names: tuple[str, ...], force: bool) -> tuple[dict, int]:
    """Back up, atomically swap, validate, and roll back on failure."""
    dest_root.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    # Backups live beside the discovery root. Keeping SKILL.md files out of the root prevents
    # the Agent from indexing historical copies as active Skills.
    backup_root = dest_root.parent / ".guiyuan-vibecoding-backups" / dest_root.name / stamp
    plan: list[tuple[str, Path, Path, bool]] = []
    for name in names:
        src = src_root / name
        dst = dest_root / name
        # Global roots may expose a skill through a Windows junction. Update the target tree
        # in place and keep the junction, rather than replacing the link itself.
        effective_dst = Path(os.path.realpath(dst)) if _is_reparse_point(dst) else dst
        if not src.is_dir():
            print(f"[error] missing source skill: {src}")
            return {"backup_root": backup_root, "backed_up": []}, 1
        if dst.exists() and not force:
            print(f"already installed, skipped: {name} (--force to overwrite)")
            continue
        plan.append((name, src, effective_dst, effective_dst.exists()))

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
                if _is_reparse_point(dst) or dst.is_symlink():
                    # A junction is a link, not a user-owned tree to recursively copy.
                    # Leave it in place until the staged replacement is ready.
                    pass
                else:
                    shutil.copytree(dst, backup)
                backed_up.append(name)
                if _is_reparse_point(dst) or dst.is_symlink():
                    dst.unlink()
                else:
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
            if _is_reparse_point(dst) or dst.is_symlink():
                dst.unlink()
            else:
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
    ap = argparse.ArgumentParser(description="Install Guiyuan Vibecoding skills and self-check the kit")
    ap.add_argument("--force", action="store_true", help="overwrite existing skills")
    ap.add_argument("--doctor", action="store_true", help="verify install + repo health (no writes)")
    ap.add_argument("--preflight", action="store_true", help="read-only inventory of old/current/similar skills")
    ap.add_argument("--uninstall", action="store_true", help="remove only Guiyuan-owned skills; no confirmation")
    ap.add_argument("--skills-dir", default=None, help="explicit global skills root")
    ap.add_argument("--discover", action="store_true", help="list known agent skill roots read-only")
    args = ap.parse_args()
    if args.discover:
        discover()
        return
    dest_root = resolve_skills_root(args.skills_dir)
    print(f"skills root: {dest_root}")
    if args.preflight:
        sys.exit(preflight(dest_root))
    if args.uninstall:
        from tools.vcm_uninstall.uninstall import uninstall as uninstall_route
        sys.exit(uninstall_route(dest_root))
    if args.doctor:
        sys.exit(doctor(dest_root))
    install(args.force, dest_root)


if __name__ == "__main__":
    main()
