#!/usr/bin/env python3
"""Load the project layout contract used by Guiyuan tools.

The manifest separates semantic authority artifacts from their physical paths.  Older projects
without a manifest continue to use the canonical five-layer layout as a compatibility fallback.
"""

from __future__ import annotations

from pathlib import Path
import tomllib


MANIFEST_REL = Path(".guiyuan-vibecoding/project-manifest.toml")
DEFAULT_ARTIFACTS = {
    "agent_rules": "AGENTS.md",
    "project_state": "NOW.md",
    "product_state": "NOW.md",
    "changelog": "CHANGELOG.md",
    "red_lines": "docs/00-system/constitution/red-lines.md",
    "roadmap": "docs/01-product/roadmap.md",
    "archive": "docs/04-workflow/archive",
}


def load_manifest(root: Path) -> dict:
    """Return a parsed project manifest, or an empty mapping for legacy projects."""
    path = root / MANIFEST_REL
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as fh:
            value = tomllib.load(fh)
        return value if isinstance(value, dict) else {}
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def artifact_path(root: Path, artifact: str, *, must_exist: bool = False) -> Path:
    """Resolve a semantic artifact to a path, preserving legacy path fallbacks."""
    manifest = load_manifest(root)
    configured = (manifest.get("artifacts") or {}).get(artifact)
    candidates = [root / configured] if isinstance(configured, str) else []
    fallback = DEFAULT_ARTIFACTS.get(artifact)
    if fallback:
        candidates.append(root / fallback)
    # Existing template projects keep state/ledger under docs/04-workflow.
    if artifact == "project_state":
        candidates.append(root / "docs" / "04-workflow" / "NOW.md")
    elif artifact == "changelog":
        candidates.append(root / "docs" / "04-workflow" / "changelog.md")
    for candidate in candidates:
        if candidate.is_file() or candidate.is_dir() or not must_exist:
            return candidate
    return candidates[0] if candidates else root / artifact


def manifest_path(root: Path) -> Path:
    return root / MANIFEST_REL


def root_path(root: Path, key: str, default: str) -> Path:
    """Resolve a declared directory root (for example ``human_docs`` or ``code``)."""
    value = (load_manifest(root).get("roots") or {}).get(key, default)
    if isinstance(value, list):
        value = value[0] if value else default
    return root / str(value)
