#!/usr/bin/env python3
"""Prepare and verify a release payload without publishing it."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())


def run(args: list[str]) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a release payload and validate release preconditions")
    ap.add_argument("--version", default=(ROOT / "VERSION").read_text(encoding="utf-8").strip())
    ap.add_argument("--out", default=str(ROOT / "dist"))
    args = ap.parse_args()
    version = args.version.lstrip("v")
    tag = f"v{version}"
    if (ROOT / "VERSION").read_text(encoding="utf-8").strip() != version:
        print("[release] VERSION does not match requested version")
        return 1
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    if status:
        print("[release] worktree is not clean; commit changes before preparing a release")
        return 1
    subprocess.run([sys.executable, str(ROOT / "tools" / "git_safety_gate.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "check_package.py")], cwd=ROOT, check=True)
    out = Path(args.out)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_dist.py"), "--verify", "--out", str(out)], cwd=ROOT, check=True)
    asset = out / f"guiyuan-vibecoding-{version}.zip"
    checksum = asset.with_suffix(asset.suffix + ".sha256")
    manifest = asset.with_suffix(asset.suffix + ".manifest.json")
    if not asset.is_file() or not checksum.is_file() or not manifest.is_file():
        print("[release] expected release assets are missing")
        return 1
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    recorded = json.loads(manifest.read_text(encoding="utf-8"))
    if recorded.get("sha256") != digest or recorded.get("version") != version:
        print("[release] manifest/hash mismatch")
        return 1
    print(json.dumps({"version": version, "tag": tag, "asset": str(asset), "sha256": digest,
                      "checksum": str(checksum), "manifest": str(manifest)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
