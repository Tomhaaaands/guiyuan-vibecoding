#!/usr/bin/env python3
"""Cross-artifact consistency check for the authority artifact store (stdlib only).

Enforces the machine-checkable half of docs/02-technical/artifact-context-contract.md section 6: missing
acceptance on accepted product/task/roadmap artifacts, state claims without receipts, broken
supersession references, and accepted-but-superseded status. Reference existence and content
hash integrity are already covered by artifact_store.validate; this adds the semantic rules.

Usage:
  python tools/artifact_consistency.py --root <project>
  python tools/artifact_consistency.py --root <project> --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from artifact_store import ArtifactStore, split_ref

sys.stdout.reconfigure(encoding="utf-8")

ACCEPTANCE_KINDS = {"product-spec", "tasks", "roadmap"}
POST_WORK_STAGES = {"VERIFICATION", "DELIVERY", "DELIVERED"}
_SECTION_RE = re.compile(r"^##\s+([^\n]+)$")


def _has_acceptance(content: str) -> bool:
    return any(line.strip().lower().lstrip("#").strip() == "acceptance" for line in content.splitlines())


def _field(content: str, name: str) -> str | None:
    """Return the first non-empty line under a `## name` section, if any."""
    active = False
    for line in content.splitlines():
        match = _SECTION_RE.match(line)
        if match:
            active = match.group(1).strip().lower() == name.lower()
            continue
        if active:
            value = line.strip()
            if value:
                return value
    return None


def check(store: ArtifactStore) -> list[dict]:
    """Return a list of consistency findings (empty means the artifact graph is consistent)."""
    issues: list[dict] = []
    metas = store.list()
    heads: dict[str, int] = {}
    for meta in metas:
        heads[meta.artifact_id] = max(heads.get(meta.artifact_id, 0), meta.revision)
    has_receipts = any(meta.kind == "receipts" for meta in metas)

    # Rule 1: accepted product/task/roadmap artifacts must carry an acceptance clause.
    for meta in metas:
        if meta.kind in ACCEPTANCE_KINDS and meta.status == "accepted":
            artifact = store.get(meta.artifact_id)
            if not _has_acceptance(artifact.content):
                issues.append(
                    {
                        "severity": "error",
                        "rule": "missing_acceptance",
                        "artifact": f"{meta.artifact_id}@{meta.revision}",
                        "detail": f"accepted {meta.kind} has no '## acceptance' clause",
                    }
                )

    # Rule 2: a project-state in a post-work stage claims progress without a receipt.
    for meta in metas:
        if meta.kind == "project-state" and not has_receipts:
            artifact = store.get(meta.artifact_id)
            stage = _field(artifact.content, "stage")
            if stage and stage in POST_WORK_STAGES:
                issues.append(
                    {
                        "severity": "error",
                        "rule": "state_without_receipt",
                        "artifact": f"{meta.artifact_id}@{meta.revision}",
                        "detail": f"stage {stage!r} claimed but no receipts artifact exists",
                    }
                )

    # Rule 3: a supersedes reference must not point past the head revision of its target.
    for meta in metas:
        if not meta.supersedes:
            continue
        target_id, rev = split_ref(meta.supersedes)
        if rev is not None and target_id in heads and rev > heads[target_id]:
            issues.append(
                {
                    "severity": "error",
                    "rule": "supersedes_revision_gap",
                    "artifact": f"{meta.artifact_id}@{meta.revision}",
                    "detail": f"supersedes {meta.supersedes} but head of {target_id} is @{heads[target_id]}",
                }
            )

    # Rule 4: an artifact that is superseded by a newer revision should not stay accepted.
    superseded_targets = {split_ref(m.supersedes)[0] for m in metas if m.supersedes}
    for meta in metas:
        if meta.artifact_id in superseded_targets and meta.status in ("accepted", "review"):
            issues.append(
                {
                    "severity": "warn",
                    "rule": "accepted_superseded",
                    "artifact": f"{meta.artifact_id}@{meta.revision}",
                    "detail": "artifact is superseded by a newer revision but is still accepted/review",
                }
            )
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-artifact consistency check")
    parser.add_argument("--root", type=Path, required=True, help="project root with artifacts/")
    parser.add_argument("--json", action="store_true", help="emit machine-readable findings")
    args = parser.parse_args()

    store = ArtifactStore(args.root)
    issues = check(store)
    if args.json:
        print(json.dumps(issues, ensure_ascii=False, indent=2))
    else:
        if not issues:
            print("artifact graph consistent ✓")
        for issue in issues:
            print(f"  [{issue['severity']}] {issue['rule']} {issue['artifact']}: {issue['detail']}")
    errors = [i for i in issues if i["severity"] == "error"]
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
