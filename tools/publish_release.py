#!/usr/bin/env python3
"""Publish one GitHub Release containing source archives and the VCM installer assets."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())


def gh(*args: str, capture: bool = False) -> str:
    p = subprocess.run(["gh", *args], cwd=ROOT, check=True, text=True, capture_output=capture,
                       encoding="utf-8", errors="replace")
    return p.stdout if capture else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish and remotely verify a GitHub Release")
    ap.add_argument("tag", help="annotated tag, e.g. v0.1.1")
    ap.add_argument("--asset-dir", default=str(ROOT / "dist"))
    ap.add_argument("--publish", action="store_true", help="perform the GitHub mutation; otherwise dry-run")
    args = ap.parse_args()
    tag = args.tag if args.tag.startswith("v") else f"v{args.tag}"
    version = tag[1:]
    asset_dir = Path(args.asset_dir)
    assets = [asset_dir / f"guiyuan-vibecoding-{version}{suffix}" for suffix in (".zip", ".zip.sha256", ".zip.manifest.json")]
    missing = [str(p) for p in assets if not p.is_file()]
    if missing:
        print("missing assets: " + ", ".join(missing))
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
    local_hash = hashlib.sha256(assets[0].read_bytes()).hexdigest()
    if remote_hash != local_hash:
        raise SystemExit("remote release verification failed: installer hash mismatch")
    print(f"release {tag} published and verified ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
