#!/usr/bin/env python3
"""P6 experience loop: receipts -> evidence-backed candidates + shadow evaluation.

Reads `receipts` artifacts with verdict fail/blocked, groups them by task, and emits `[AI-DRAFT]`
`experience` candidates (never auto-promoted to accepted). A separate shadow evaluation recommends
which could become a project red line, but it never edits the authoritative `red-lines.md`; the
optional --draft action writes a `red-lines.draft.md` review file only, matching the distill pattern.

Usage:
  python tools/experience_loop.py --root <project> --action list
  python tools/experience_loop.py --root <project> --action write --slug auth-01
  python tools/experience_loop.py --root <project> --action draft --min-frequency 1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from artifact_store import ArtifactStore

sys.stdout.reconfigure(encoding="utf-8")

_SECTION_RE = re.compile(r"^##\s+([^\n]+)$")


def _field(content: str, name: str) -> str:
    active = False
    for line in content.splitlines():
        match = _SECTION_RE.match(line)
        if match:
            active = match.group(1).strip().lower() == name.lower()
            continue
        if active and line.strip():
            return line.strip().lstrip("* ").strip()
    return ""


def _bullet_lines(content: str, name: str) -> list[str]:
    out: list[str] = []
    active = False
    for line in content.splitlines():
        match = _SECTION_RE.match(line)
        if match:
            active = match.group(1).strip().lower() == name.lower()
            continue
        if active and line.strip():
            out.append(line.strip().lstrip("-* ").strip())
    return out


def _slug(artifact_id: str) -> str:
    return artifact_id.rsplit("/", 1)[-1] if "/" in artifact_id else artifact_id


def collect_experience(store: ArtifactStore) -> list[dict]:
    groups: dict[str, dict] = {}
    for meta in store.list():
        if meta.kind != "receipts":
            continue
        artifact = store.get(meta.artifact_id)
        verdict = _field(artifact.content, "verdict")
        if verdict not in ("fail", "blocked"):
            continue
        task = _field(artifact.content, "task")
        error = _field(artifact.content, "error")
        slug = _slug(meta.artifact_id)
        failed = [c for c in _bullet_lines(artifact.content, "checks") if c.lower().endswith("fail")]
        lesson = error if error and error != "-" else ("; ".join(failed) or "checks failed")
        entry = groups.setdefault(
            slug, {"slug": slug, "task": task, "lesson": lesson, "evidence": [], "frequency": 0, "verdicts": set()}
        )
        entry["evidence"].append(meta.artifact_id)
        entry["frequency"] += 1
        entry["verdicts"].add(verdict)
    return [
        {**e, "verdicts": sorted(e["verdicts"])}
        for e in groups.values()
    ]


def write_experience(store: ArtifactStore, slug: str, candidate: dict) -> str:
    content = (
        "# Experience candidate\n\n> [AI-DRAFT] unconfirmed; never auto-promoted to accepted\n\n"
        f"## lesson\n{candidate.get('lesson', '')}\n"
        f"## task\n{candidate.get('task', '')}\n"
        f"## frequency\n{candidate.get('frequency', 1)}\n"
        "## evidence\n" + "\n".join(f"- {e}" for e in candidate.get("evidence", [])) + "\n"
    )
    target = f"experience/{slug}"
    store.write(
        target,
        "experience",
        content,
        status="draft",
        depends_on=candidate.get("evidence", []),
    )
    return target


def shadow_evaluate(store: ArtifactStore, *, min_frequency: int = 1) -> list[dict]:
    """Return candidates that qualify for red-line consideration (never writes them)."""
    return [c for c in collect_experience(store) if c["frequency"] >= min_frequency]


def write_draft_red_lines(root: Path, candidates: list[dict]) -> Path:
    path = Path(root) / "docs" / "00-system" / "constitution" / "red-lines.draft.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Red lines draft (shadow, unconfirmed)", ""]
    for c in candidates:
        lines.append(f"- [{c['frequency']}x] {c['lesson']}  (evidence: {', '.join(c['evidence'])})")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="P6 experience loop + shadow evaluation")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--action", choices=("list", "write", "draft"), default="list")
    parser.add_argument("--slug", default=None)
    parser.add_argument("--min-frequency", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    store = ArtifactStore(args.root)
    candidates = collect_experience(store)
    if args.action == "list":
        if args.json:
            print(json.dumps(candidates, ensure_ascii=False, indent=2))
        else:
            for c in candidates:
                print(f"  {c['slug']} [{c['frequency']}x {','.join(c['verdicts'])}] {c['lesson'][:70]}")
        return
    if args.action == "draft":
        qualifying = shadow_evaluate(store, min_frequency=args.min_frequency)
        path = write_draft_red_lines(args.root, qualifying)
        print(f"shadow draft written (not authoritative): {path}")
        return
    if args.action == "write":
        if not args.slug:
            parser.error("--action write requires --slug")
        found = next((c for c in candidates if c["slug"] == args.slug), None)
        if found is None:
            parser.error(f"no failed/blocked receipt group for slug {args.slug!r}")
        target = write_experience(store, args.slug, found)
        print(f"wrote experience candidate: {target} (draft, [AI-DRAFT])")


if __name__ == "__main__":
    main()
