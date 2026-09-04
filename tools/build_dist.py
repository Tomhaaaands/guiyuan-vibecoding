#!/usr/bin/env python3
"""Build the distributable skill zip for install-by-message (Quark-style).

The primary install path for the kit is a one-line message to an agent with a "技能地址"
zip URL (see skills/guiyuan-vibecoding-install/SKILL.md). This tool produces that zip: three
self-contained skills at the zip root, so unzipping into an agent's global skills root
installs the kit (no wrapper dir).

Usage:
  python tools/build_dist.py            # build dist/guiyuan-vibecoding-<version>.zip
  python tools/build_dist.py --verify   # build + extract to temp and validate installability
  python tools/build_dist.py --out DIR  # write the zip into DIR (default: <repo>/dist)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
SKILLS = ("guiyuan-iteration-close-loop", "guiyuan-vibecoding", "guiyuan-vibecoding-install")
EXCLUDE_PARTS = {"__pycache__", ".git"}
EXCLUDE_SUFFIXES = {".pyc"}


def version() -> str:
    v = ROOT / "VERSION"
    return v.read_text(encoding="utf-8").strip() if v.is_file() else "0.0.0"


def source_commit() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def _walk_files(skill_dir: Path):
    for p in skill_dir.rglob("*"):
        if p.is_file() and not any(part in EXCLUDE_PARTS for part in p.parts) and p.suffix not in EXCLUDE_SUFFIXES:
            yield p


def build(out_dir: Path, verify: bool) -> Path:
    ver = version()
    zip_path = out_dir / f"guiyuan-vibecoding-{ver}.zip"
    out_dir.mkdir(parents=True, exist_ok=True)

    n_files = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in SKILLS:
            skill_dir = ROOT / "skills" / name
            if not skill_dir.is_dir():
                print(f"[error] missing skill dir: {skill_dir}")
                sys.exit(1)
            for p in _walk_files(skill_dir):
                arc = Path(name) / p.relative_to(skill_dir)
                zf.write(p, arc.as_posix())
                n_files += 1

    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    size = zip_path.stat().st_size
    checksum_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    manifest_path = zip_path.with_suffix(zip_path.suffix + ".manifest.json")
    checksum_path.write_text(f"{sha} *{zip_path.name}\n", encoding="utf-8")
    manifest_path.write_text(json.dumps({
        "name": "Guiyuan Vibecoding",
        "version": ver,
        "asset": zip_path.name,
        "sha256": sha,
        "size": size,
        "source_commit": source_commit(),
        "skills": list(SKILLS),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"built  : {zip_path}")
    print(f"version: {ver}")
    print(f"skills : {', '.join(SKILLS)}")
    print(f"files  : {n_files}")
    print(f"size   : {size:,} bytes")
    print(f"sha256 : {sha}")
    print(f"checksum: {checksum_path.name}")
    print(f"manifest: {manifest_path.name}")

    if verify:
        verify_zip(zip_path)
    return zip_path


def verify_zip(zip_path: Path) -> None:
    """Extract to a temp dir and validate the installability contract."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(root)
        print("\n== verify ==")
        ok = True
        for name in SKILLS:
            sk = root / name / "SKILL.md"
            ag = root / name / "agents" / "openai.yaml"
            if sk.is_file():
                adapter = "agents/openai.yaml (Codex adapter)" if ag.is_file() else "no Codex adapter (optional)"
                print(f"  [ok] {name}: SKILL.md + {adapter}")
            else:
                print(f"  [bad] {name}: missing SKILL.md")
                ok = False
        bundled = root / "guiyuan-vibecoding-install" / "VERSION"
        if bundled.is_file() and bundled.read_text(encoding="utf-8").strip() == version():
            print(f"  [ok] bundled VERSION == {version()}")
        else:
            print(f"  [bad] bundled VERSION mismatch")
            ok = False
        project_payload = root / "guiyuan-vibecoding" / "assets" / "project"
        for required in (
            project_payload / "tools" / "render_project_home.py",
            project_payload / "templates" / "guiyuan-vibecoding-home.html",
        ):
            if required.is_file():
                print(f"  [ok] static project-home asset: {required.relative_to(root)}")
            else:
                print(f"  [bad] missing static project-home asset: {required.relative_to(root)}")
                ok = False
        legacy = [p.relative_to(root).as_posix() for p in root.rglob("*") if "serve_project" in p.name or "serve_status" in p.name]
        if legacy:
            print(f"  [bad] legacy status server files remain: {legacy}")
            ok = False
        else:
            print("  [ok] no legacy 8010 status server in payload")
        # every top-level entry must be one of the three skills
        tops = {p for p in root.iterdir() if p.is_dir()}
        if tops == {root / n for n in SKILLS}:
            print(f"  [ok] zip root contains exactly the 3 skill dirs")
        else:
            print(f"  [bad] unexpected zip root entries: {sorted(p.name for p in tops)}")
            ok = False
        print("verify " + ("passed ✓" if ok else "found issues ✗"))
        sys.exit(0 if ok else 1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the distributable Guiyuan Vibecoding skill zip")
    ap.add_argument("--out", default=str(ROOT / "dist"), help="output directory (default: <repo>/dist)")
    ap.add_argument("--verify", action="store_true", help="build then extract to temp and validate installability")
    args = ap.parse_args()
    build(Path(args.out), args.verify)


if __name__ == "__main__":
    main()
