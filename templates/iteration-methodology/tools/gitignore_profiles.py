#!/usr/bin/env python3
"""Deterministic .gitignore generation for managed projects.

The generated file is intentionally plain text so it remains useful outside VCM.  Rules are
the union of a safe common baseline and overlays selected by topology, scale, and capability.
"""
from __future__ import annotations

from pathlib import Path

COMMON_RULES = [
    "# Guiyuan Vibecoding managed-project defaults",
    "__pycache__/", "*.py[cod]", "*.egg-info/", ".pytest_cache/", ".coverage", "htmlcov/",
    ".venv/", "venv/", ".env", ".env.*", "!.env.example",
    "build/", "dist/", "out/", ".tmp/", ".cache/", ".qa/", ".preview/",
    ".vscode/", ".idea/", ".DS_Store", "Thumbs.db", "status.html",
]

TOPOLOGY_RULES = {
    "web": ["node_modules/", ".next/", ".nuxt/", ".svelte-kit/", ".vercel/", "*.log", "npm-debug.log*", "yarn-debug.log*", "pnpm-debug.log*"],
    "service": [".mypy_cache/", ".ruff_cache/", ".pytest_cache/"],
    "cli": [".mypy_cache/", ".ruff_cache/"],
    "monorepo": ["**/node_modules/", "**/.next/", "**/dist/", "**/.turbo/", "**/.nx/"],
}

CAPABILITY_RULES = {
    "auth": ["credentials/", "secrets/", "*.pem", "*.key", "*.p12", "*.pfx"],
    "vector-db": ["data/", "vectors/", "qdrant_storage/", "chroma/", "*.sqlite", "*.sqlite3", "*.db"],
    "rag": ["embeddings/", "indexes/", "retrieval-cache/"],
    "content-pipeline": ["raw-media/", "generated-media/", "pipeline-cache/"],
    "worker": ["worker-state/", "*.pid"],
}

SCALE_RULES = {
    "large": ["**/.pytest_cache/", "**/__pycache__/", "**/coverage/"],
    "medium": [],
    "small": [],
}


def rules_for(*, topology: str | None = None, scale: str | None = None,
              capabilities: list[str] | tuple[str, ...] = (), extra: list[str] | tuple[str, ...] = ()) -> list[str]:
    """Return de-duplicated rules in stable order."""
    out: list[str] = []
    for group in (COMMON_RULES, TOPOLOGY_RULES.get(topology or "", []),
                  SCALE_RULES.get(scale or "", [])):
        for rule in group:
            if rule not in out:
                out.append(rule)
    for capability in capabilities:
        for rule in CAPABILITY_RULES.get(capability, []):
            if rule not in out:
                out.append(rule)
    for rule in extra:
        if rule and rule not in out:
            out.append(rule)
    return out


def render(*, topology: str | None = None, scale: str | None = None,
           capabilities: list[str] | tuple[str, ...] = (), extra: list[str] | tuple[str, ...] = ()) -> str:
    return "\n".join(rules_for(topology=topology, scale=scale, capabilities=capabilities, extra=extra)) + "\n"


def ensure(path: Path, *, topology: str | None = None, scale: str | None = None,
           capabilities: list[str] | tuple[str, ...] = (), extra: list[str] | tuple[str, ...] = (),
           replace: bool = False) -> bool:
    """Create defaults, or append missing rules when adopting an existing project."""
    generated = render(topology=topology, scale=scale, capabilities=capabilities, extra=extra)
    if replace or not path.exists():
        path.write_text(generated, encoding="utf-8")
        return True
    existing = path.read_text(encoding="utf-8")
    missing = [rule for rule in rules_for(topology=topology, scale=scale, capabilities=capabilities, extra=extra)
               if rule not in existing.splitlines()]
    if not missing:
        return False
    path.write_text(existing.rstrip() + "\n\n# Guiyuan profile overlay\n" + "\n".join(missing) + "\n", encoding="utf-8")
    return True


