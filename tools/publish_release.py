#!/usr/bin/env python3
"""Publish one GitHub Release containing source archives and the VCM installer assets."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
PUBLIC_SKILL = "guiyuan-vibecoding"
CATALOG = ROOT / "docs" / "03-reference" / "update-catalog.json"
sys.stdout.reconfigure(encoding="utf-8")


def gh(*args: str, capture: bool = False) -> str:
    p = subprocess.run(["gh", *args], cwd=ROOT, check=True, text=True, capture_output=capture,
                       encoding="utf-8", errors="replace")
    return p.stdout if capture else ""


def validate_installer_asset(asset: Path, checksum: Path, manifest: Path) -> str:
    """Validate the exact public installer contract before any GitHub mutation."""
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    sidecar = checksum.read_text(encoding="utf-8", errors="replace").strip().split()
    if not sidecar or sidecar[0] != digest:
        raise ValueError(".sha256 sidecar does not match installer ZIP")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("skills") != [PUBLIC_SKILL]:
        raise ValueError("manifest must declare exactly one public Skill: guiyuan-vibecoding")
    if data.get("sha256") != digest:
        raise ValueError("manifest hash does not match installer ZIP")
    with zipfile.ZipFile(asset) as zf:
        names = [name.rstrip("/") for name in zf.namelist() if name.rstrip("/")]
    tops = {name.split("/", 1)[0] for name in names}
    if tops != {PUBLIC_SKILL}:
        raise ValueError(f"installer ZIP root must contain only {PUBLIC_SKILL}, found {sorted(tops)}")
    nested = [name for name in names if name.endswith("SKILL.md") and name != f"{PUBLIC_SKILL}/SKILL.md"]
    if nested:
        raise ValueError(f"installer ZIP contains nested discoverable SKILL.md files: {nested}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish and remotely verify a GitHub Release")
    ap.add_argument("tag", help="annotated tag, e.g. v0.1.1")
    ap.add_argument("--asset-dir", default=str(ROOT / "dist"))
    ap.add_argument("--publish", action="store_true", help="perform the GitHub mutation; otherwise dry-run")
    args = ap.parse_args()
    tag = args.tag if args.tag.startswith("v") else f"v{args.tag}"
    version = tag[1:]
    asset_dir = Path(args.asset_dir).expanduser()
    if not asset_dir.is_absolute():
        asset_dir = ROOT / asset_dir
    assets = [asset_dir / f"guiyuan-vibecoding-{version}{suffix}" for suffix in (".zip", ".zip.sha256", ".zip.manifest.json")]
    missing = [str(p) for p in assets if not p.is_file()]
    if missing:
        print("missing assets: " + ", ".join(missing))
        return 1
    try:
        local_hash = validate_installer_asset(assets[0], assets[1], assets[2])
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"invalid installer assets: {exc}")
        return 1
    if not CATALOG.is_file():
        print(f"missing update catalog: {CATALOG}")
        return 1
    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid update catalog: {exc}")
        return 1
    current = catalog.get("current", {})
    if current.get("version") != version or current.get("tag") != tag:
        print("update catalog does not match the release tag/version; run release_prepare first")
        return 1
    if not args.publish:
        print("dry-run: would publish " + tag + " with " + ", ".join(p.name for p in assets))
        return 0
    gh("release", "create", tag, *[str(p) for p in assets], "--verify-tag", "--title", f"Guiyuan Vibecoding {tag}",
       "--generate-notes")
    payload = json.loads(gh("release", "view", tag, "--json", "tagName,isDraft,assets", capture=True))
    if payload.get("tagName") != tag or payload.get("isDraft"):
        raise SystemExit("remote release verification failed: tag or draft state")
    remote_names = {a.get("name") for a in payload.get("assets", [])}
    if not {p.name for p in assets}.issubset(remote_names):
        raise SystemExit("remote release verification failed: installer assets missing")
    with tempfile.TemporaryDirectory() as tmp:
        gh("release", "download", tag, "--pattern", assets[0].name, "--dir", tmp)
        remote_hash = hashlib.sha256((Path(tmp) / assets[0].name).read_bytes()).hexdigest()
    if remote_hash != local_hash:
        raise SystemExit("remote release verification failed: installer hash mismatch")
    print(f"release {tag} published and verified ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
