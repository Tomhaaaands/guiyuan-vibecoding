#!/usr/bin/env python3
"""Build and validate the machine registry from human-facing project documents."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from project_manifest import artifact_path, root_path

KINDS = {
    "prd.md": "product-spec",
    "technical-spec.md": "technical-spec",
    "iteration.md": "technical-iteration",
    "acceptance.md": "product-acceptance",
}

# These names are semantic, not layout requirements.  ``project_manifest`` supplies the
# physical path for projects that choose a different documentation tree.
PROJECT_ARTIFACTS = (
    ("project_state", "project-state"),
    ("changelog", "changelog"),
    ("roadmap", "roadmap"),
    ("red_lines", "red-lines"),
)


def _hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def scan(root: Path) -> tuple[list[dict], list[dict], list[str]]:
    docs = root_path(root, "human_docs", "docs")
    records: list[dict] = []
    by_module: dict[str, dict] = {}
    if docs.is_dir():
        for path in sorted(docs.rglob("*.md")):
            if "archive" in path.parts or "_archive" in path.parts:
                continue
            name = path.name
            kind = KINDS.get(name)
            rel = path.relative_to(root).as_posix()
            if kind:
                module = path.parent.name if path.parent != docs else "project"
                prefix = "product" if kind.startswith("product") else "technical"
                artifact_id = f"{prefix}/{module}/{name[:-3]}"
                records.append({
                    "id": artifact_id, "kind": kind, "module": module, "path": rel,
                    "status": "draft", "revision": 1, "content_hash": _hash(path),
                    "depends_on": [],
                })
                by_module.setdefault(module, {})[kind] = artifact_id
    for key, kind in PROJECT_ARTIFACTS:
        default = {"project_state": "NOW.md", "changelog": "CHANGELOG.md",
                   "roadmap": "docs/01-product/roadmap.md",
                   "red_lines": "docs/00-system/constitution/red-lines.md"}[key]
        path = artifact_path(root, key, must_exist=False)
        # ``artifact_path`` knows manifest mappings and legacy fallbacks; when no mapping is
        # present its default for roadmap/red-lines is intentionally canonical here.
        if not path.exists() and not (root / ".guiyuan-vibecoding/project-manifest.toml").is_file():
            path = root / default
        artifact_id = {"project_state": "project-state", "changelog": "workflow/changelog",
                       "roadmap": "roadmap", "red_lines": "red-lines"}[key]
        if path.is_file():
            records.append({"id": artifact_id, "kind": kind, "module": "project",
                            "path": path.relative_to(root).as_posix(), "status": "active",
                            "revision": 1, "content_hash": _hash(path), "depends_on": []})
    modules = []
    issues: list[str] = []
    for module, entries in sorted(by_module.items()):
        product = entries.get("product-spec")
        acceptance = entries.get("product-acceptance")
        technical = entries.get("technical-spec")
        if product and not acceptance:
            issues.append(f"module {module}: product PRD is missing acceptance.md")
        modules.append({
            "id": module, "product_doc": product or "", "acceptance_doc": acceptance or "",
            "technical_docs": [technical] if technical else [], "status": "active",
        })
    # Keep machine state visible to derived views without treating it as human authority.
    machine = root / ".guiyuan-vibecoding"
    for rel, kind in (("anchors", "confirmation-anchor"), ("receipts", "receipt")):
        directory = machine / rel
        if directory.is_dir():
            for path in sorted(directory.glob("*.json")):
                records.append({
                    "id": f"machine/{rel}/{path.stem}", "kind": kind, "module": "machine",
                    "path": path.relative_to(root).as_posix(), "status": "recorded", "revision": 1,
                    "content_hash": _hash(path), "depends_on": [],
                })
    return records, modules, issues


def _toml(value: object) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(str(v), ensure_ascii=False) for v in value) + "]"
    return json.dumps(value, ensure_ascii=False)


def write_registry(root: Path) -> dict:
    records, modules, issues = scan(root)
    reg = root / ".guiyuan-vibecoding" / "registry"
    indexes = root / ".guiyuan-vibecoding" / "indexes"
    reg.mkdir(parents=True, exist_ok=True)
    indexes.mkdir(parents=True, exist_ok=True)
    artifact_lines = ["# Generated registry; source content remains under docs/.", ""]
    for record in records:
        artifact_lines.append("[[artifacts]]")
        for key in ("id", "kind", "module", "path", "status", "revision", "content_hash"):
            artifact_lines.append(f"{key} = {_toml(record[key])}")
        artifact_lines.append(f"depends_on = {_toml(record['depends_on'])}")
        artifact_lines.append("")
    (reg / "artifacts.toml").write_text("\n".join(artifact_lines), encoding="utf-8")
    module_lines = ["# Generated module registry.", ""]
    for module in modules:
        module_lines.append("[[modules]]")
        for key in ("id", "product_doc", "acceptance_doc", "technical_docs", "status"):
            module_lines.append(f"{key} = {_toml(module[key])}")
        module_lines.append("")
    (reg / "modules.toml").write_text("\n".join(module_lines), encoding="utf-8")
    doc_tree = [{"id": r["id"], "kind": r["kind"], "path": r["path"], "status": r["status"]} for r in records]
    (indexes / "doc-tree.json").write_text(json.dumps(doc_tree, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"artifacts": len(records), "modules": len(modules), "issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Guiyuan machine registry")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true", help="write registry and indexes")
    args = parser.parse_args()
    result = write_registry(args.root.resolve()) if args.write else {"issues": scan(args.root.resolve())[2]}
    for issue in result.get("issues", []):
        print(f"  [registry] {issue}")
    print(json.dumps(result, ensure_ascii=False))
    # Writing a derived index is always safe; validation-only mode keeps a non-zero status so CI
    # can enforce that every product PRD has an acceptance document.
    raise SystemExit(1 if result.get("issues") and not args.write else 0)


if __name__ == "__main__":
    main()
