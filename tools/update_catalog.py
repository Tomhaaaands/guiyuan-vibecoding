#!/usr/bin/env python3
"""Build the machine-readable release/update catalog from the single version source."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
CATALOG = ROOT / "docs" / "03-reference" / "update-catalog.json"


def _remote_url() -> str:
    try:
        raw = subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""
    match = re.match(r"https?://github\.com/([^/]+/[^/]+?)(?:\.git)?$", raw)
    if not match:
        match = re.match(r"git@github\.com:([^/]+/[^/]+?)(?:\.git)?$", raw)
    return f"https://github.com/{match.group(1)}" if match else raw


def _load() -> dict:
    if not CATALOG.is_file():
        return {"schema_version": 1, "product": "guiyuan-vibecoding", "releases": []}
    try:
        value = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "product": "guiyuan-vibecoding", "releases": []}
    return value if isinstance(value, dict) else {"schema_version": 1, "product": "guiyuan-vibecoding", "releases": []}


def _tag_exists(tag: str) -> bool:
    return subprocess.run(["git", "rev-parse", "--verify", tag], cwd=ROOT,
                          capture_output=True, text=True).returncode == 0


def build(version: str, status: str | None = None) -> dict:
    version = version.lstrip("v")
    tag = f"v{version}"
    base = _remote_url().rstrip("/")
    release_url = f"{base}/releases/tag/{tag}" if "github.com/" in base else ""
    download_base = f"{base}/releases/download/{tag}" if "github.com/" in base else ""
    old = _load()
    entries = [item for item in old.get("releases", []) if isinstance(item, dict) and item.get("version") != version]
    previous = next((item for item in old.get("releases", []) if isinstance(item, dict) and item.get("version") == version), {})
    entry = {
        "version": version,
        "tag": tag,
        "status": status or previous.get("status") or ("published" if _tag_exists(tag) else "pending"),
        "tag_exists": _tag_exists(tag),
        "release_url": release_url,
        "assets": {
            "installer": f"{download_base}/guiyuan-vibecoding-{version}.zip" if download_base else "",
            "sha256": f"{download_base}/guiyuan-vibecoding-{version}.zip.sha256" if download_base else "",
            "manifest": f"{download_base}/guiyuan-vibecoding-{version}.zip.manifest.json" if download_base else "",
        },
        "source": "VERSION + tools/update_catalog.py",
    }
    entries.append(entry)
    entries.sort(key=lambda item: tuple(int(part) if part.isdigit() else part for part in str(item.get("version", "0")).split(".")), reverse=True)
    catalog = {
        "schema_version": 1,
        "product": "guiyuan-vibecoding",
        "current": entry,
        "releases": entries,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    return catalog


def write(catalog: dict) -> bool:
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    if CATALOG.is_file():
        try:
            old = json.loads(CATALOG.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            old = None
        if isinstance(old, dict):
            comparable_old = dict(old)
            comparable_new = dict(catalog)
            comparable_old.pop("generated_at", None)
            comparable_new.pop("generated_at", None)
            if comparable_old == comparable_new:
                catalog["generated_at"] = old.get("generated_at", catalog["generated_at"])
    text = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
    if CATALOG.is_file() and CATALOG.read_text(encoding="utf-8") == text:
        return False
    CATALOG.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Update the Guiyuan Vibecoding release/update catalog")
    ap.add_argument("--version", default=(ROOT / "VERSION").read_text(encoding="utf-8").strip())
    ap.add_argument("--status", choices=["pending", "ready", "published"], default=None)
    args = ap.parse_args()
    catalog = build(args.version, args.status)
    changed = write(catalog)
    print(f"update catalog {'updated' if changed else 'already current'}: {CATALOG.relative_to(ROOT).as_posix()}")
    print(f"  current: {catalog['current']['version']} ({catalog['current']['status']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
