#!/usr/bin/env python3
"""Deterministic context compiler (P2 runtime, stdlib only).

Turns authority artifacts into the minimum bounded view for one decision, per
docs/02-technical/artifact-context-contract.md sections 3-7: L0 pointer cards and L1 field/span
slices, ordered by phase policy, enforced under a hard token ceiling, with delta-only
continuation. It never connects a provider and never silently drops required safety,
permission, acceptance, or destructive-operation evidence.

Usage:
  python tools/context_compiler.py --root <project> --phase EXECUTION
  python tools/context_compiler.py --root <project> --phase EXECUTION --task task-auth-07
      --ref product/auth --ref technical/auth@7 --ref decisions/auth-provider@2
  python tools/context_compiler.py --root <project> --phase EXECUTION --prev-context-id ctx-1
      --changed product/auth --changed technical/auth
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from context_budget import DEFAULT_BUDGET, DEFAULT_TARGET, estimate_tokens
from artifact_store import Artifact, ArtifactStore, content_hash, split_ref

sys.stdout.reconfigure(encoding="utf-8")

PHASES = (
    "ANALYSIS",
    "SPECIFICATION",
    "PLANNING",
    "EXECUTION",
    "VERIFICATION",
    "DELIVERY",
    "REFLECTION",
)

# Phase policy (contract section 5): which artifact kinds are required safety/acceptance
# sources, which are optional authority, and which are excluded by default.
PHASE_POLICY: dict[str, dict] = {
    "ANALYSIS": {
        "required": ["product-spec", "decisions"],
        "optional": ["design-brief"],
        "prohibited": ["archive"],
    },
    "SPECIFICATION": {
        "required": ["analysis", "product-spec", "decisions"],
        "optional": ["technical-spec", "design-brief"],
        "prohibited": ["archive"],
    },
    "PLANNING": {
        "required": ["roadmap", "project-state", "decisions"],
        "optional": ["technical-spec", "tasks"],
        "prohibited": ["archive"],
    },
    "EXECUTION": {
        "required": ["tasks", "project-state", "technical-spec", "product-spec", "decisions"],
        "optional": [],
        "prohibited": ["archive", "roadmap"],
    },
    "VERIFICATION": {
        "required": ["tasks", "receipts", "technical-spec"],
        "optional": ["product-spec"],
        "prohibited": ["archive"],
    },
    "DELIVERY": {
        "required": ["receipts", "roadmap", "project-state"],
        "optional": [],
        "prohibited": ["archive"],
    },
    "REFLECTION": {
        "required": ["receipts", "experience"],
        "optional": ["decisions"],
        "prohibited": ["archive"],
    },
}


class BudgetConflictError(ValueError):
    """Raised when required safety/acceptance evidence cannot fit the hard ceiling."""


@dataclasses.dataclass
class CompiledSection:
    ref: str
    level: str  # L0 | L1
    title: str
    text: str
    reason: str
    required: bool
    tokens: int
    unchanged: bool = False
    l0_text: str = ""  # compact pointer text used when an L1 slice is downgraded


def _first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            return stripped
    return "(no content)"


def _l0(artifact: Artifact, reason: str, required: bool) -> CompiledSection:
    meta = artifact.metadata
    pointer = (
        f"{meta.artifact_id}@{meta.revision} [{meta.status}]: {_first_line(artifact.content)} "
        f"| depends_on={','.join(meta.depends_on) or '-'}"
    )
    return CompiledSection(
        ref=f"{meta.artifact_id}@{meta.revision}",
        level="L0",
        title=f"pointer:{meta.artifact_id}",
        text=pointer,
        reason=reason,
        required=required,
        tokens=estimate_tokens(pointer),
    )


def _l1(artifact: Artifact, reason: str, required: bool) -> CompiledSection:
    """Extract the named field slice from `## ` sections. Falls back to L0 for empty."""
    meta = artifact.metadata
    sections = _parse_fields(artifact.content)
    joined = "\n\n".join(f"## {name}: {body}" for name, body in sections)
    return CompiledSection(
        ref=f"{meta.artifact_id}@{meta.revision}",
        level="L1",
        title=f"fields:{meta.artifact_id}",
        text=joined if joined else f"## {_first_line(artifact.content)}",
        reason=reason,
        required=required,
        tokens=estimate_tokens(joined if joined else _first_line(artifact.content)),
    )


def _parse_fields(content: str) -> list[tuple[str, str]]:
    """Return [(heading, body)] for top-level `## ` sections, preserving order."""
    out: list[tuple[str, str]] = []
    current: list[str] = []
    heading: str | None = None
    for line in content.splitlines():
        if line.startswith("## "):
            if heading is not None:
                out.append((heading, "\n".join(current).strip()))
            heading = line[3:].strip()
            current = []
        elif heading is not None:
            current.append(line)
    if heading is not None:
        out.append((heading, "\n".join(current).strip()))
    return [(name, body) for name, body in out if body]


def _select_refs(store: ArtifactStore, phase: str, refs: list[str]) -> tuple[list[str], dict]:
    """Resolve requested refs, or auto-select artifacts by the phase policy."""
    policy = PHASE_POLICY[phase]
    if refs:
        # Keep the caller's order; validate existence.
        return refs, policy
    selected: list[str] = []
    for meta in store.list():
        if meta.kind in policy["prohibited"]:
            continue
        if meta.kind in policy["required"] or meta.kind in policy["optional"]:
            selected.append(f"{meta.artifact_id}@{meta.revision}")
    return selected, policy


def _resolve(store: ArtifactStore, ref: str) -> Artifact:
    artifact_id, rev = split_ref(ref)
    artifact = store.get(artifact_id)
    if rev is not None and rev != artifact.metadata.revision:
        raise ValueError(
            f"{ref} requests revision {rev}, but current is {artifact.metadata.revision}"
        )
    return artifact


def compile_context(
    store: ArtifactStore,
    *,
    phase: str,
    task_id: str = "",
    refs: list[str] | None = None,
    target_budget: int = DEFAULT_TARGET,
    hard_ceiling: int = DEFAULT_BUDGET,
    prev_context_id: str | None = None,
    changed: list[str] | None = None,
) -> dict:
    if phase not in PHASES:
        raise ValueError(f"invalid phase {phase!r}; expected one of {PHASES}")
    if target_budget <= 0 or hard_ceiling <= 0 or target_budget > hard_ceiling:
        raise ValueError("require 0 < target <= ceiling")

    selected, policy = _select_refs(store, phase, refs or [])
    resolved: list[Artifact] = [_resolve(store, ref) for ref in selected]

    # Put required kinds first, then optional, preserving ref order within each group.
    def key(artifact: Artifact) -> int:
        return 0 if artifact.metadata.kind in policy["required"] else 1

    resolved.sort(key=key)
    changed_ids = set(changed or [])
    deltas = prev_context_id is not None

    sections: list[CompiledSection] = []
    for artifact in resolved:
        meta = artifact.metadata
        is_required = meta.kind in policy["required"]
        reason = "required-safety/acceptance" if is_required else "authority"
        if deltas and meta.artifact_id not in changed_ids:
            # Delta continuation: unchanged context is referenced, not replayed.
            sections.append(
                CompiledSection(
                    ref=f"{meta.artifact_id}@{meta.revision}",
                    level="L0",
                    title=f"unchanged:{meta.artifact_id}",
                    text="",
                    reason=reason,
                    required=is_required,
                    tokens=0,
                    unchanged=True,
                )
            )
            continue
        section = _l1(artifact, reason, is_required)
        section.l0_text = _l0(artifact, reason, is_required).text
        sections.append(section)

    # Budget enforcement: exact field slices first, downgrade to L0, then drop optional.
    sections = _fit_budget(sections, target_budget, hard_ceiling)

    included = [
        {
            "ref": s.ref,
            "level": s.level,
            "reason": s.reason,
            "required": s.required,
            "unchanged": s.unchanged,
        }
        for s in sections
    ]
    excluded = [
        {"ref": f"archive/{meta.artifact_id}", "reason": "archaeology-not-required"}
        for meta in store.list()
        if meta.kind == "archive"
    ]
    context_id = _context_id(phase, task_id, resolved, changed_ids)
    total_tokens = sum(s.tokens for s in sections)
    return {
        "context_id": context_id,
        "phase": phase,
        "task_id": task_id,
        "target_budget": target_budget,
        "hard_ceiling": hard_ceiling,
        "estimated_tokens": total_tokens,
        "delta": deltas,
        "prev_context_id": prev_context_id,
        "included": included,
        "excluded": excluded,
        "sections": [dataclasses.asdict(s) for s in sections],
    }


def _fit_budget(
    sections: list[CompiledSection],
    target: int,
    ceiling: int,
) -> list[CompiledSection]:
    total = sum(s.tokens for s in sections)
    if total <= ceiling:
        return sections

    # Pass 1: downgrade optional L1 slices to L0 pointer cards.
    downgraded: list[CompiledSection] = []
    for s in sections:
        if s.level == "L1" and not s.required:
            pointer = s.l0_text or s.text
            card = CompiledSection(
                ref=s.ref,
                level="L0",
                title=f"pointer:{s.ref}",
                text=pointer,
                reason=s.reason,
                required=False,
                tokens=estimate_tokens(pointer),
                unchanged=s.unchanged,
                l0_text=s.l0_text,
            )
            downgraded.append(card)
        else:
            downgraded.append(s)
    if sum(s.tokens for s in downgraded) <= ceiling:
        return downgraded

    # Pass 2: drop optional sections entirely.
    trimmed = [s for s in downgraded if s.required]
    if sum(s.tokens for s in trimmed) <= ceiling:
        return trimmed

    # Required safety/acceptance cannot fit -> hard stop, never silently truncate.
    raise BudgetConflictError(
        f"required safety/acceptance evidence cannot fit the hard ceiling ({sum(s.tokens for s in trimmed)}>{ceiling})"
    )


def _context_id(phase: str, task_id: str, resolved: list[Artifact], changed: set[str]) -> str:
    ids = [f"{a.metadata.artifact_id}@{a.metadata.revision}" for a in resolved]
    basis = "|".join(ids) + "|" + "|".join(sorted(changed))
    return f"{phase.lower()}-{(task_id or 'ctx')}-{content_hash(basis)[len('sha256:'):8]}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic context compiler")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--phase", required=True, choices=PHASES)
    parser.add_argument("--task", default="")
    parser.add_argument("--ref", action="append", default=[])
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET)
    parser.add_argument("--ceiling", type=int, default=DEFAULT_BUDGET)
    parser.add_argument("--prev-context-id")
    parser.add_argument("--changed", action="append", default=[])
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    store = ArtifactStore(args.root)
    result = compile_context(
        store,
        phase=args.phase,
        task_id=args.task,
        refs=args.ref,
        target_budget=args.target,
        hard_ceiling=args.ceiling,
        prev_context_id=args.prev_context_id,
        changed=args.changed,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"== context {result['context_id']} [{result['phase']}] ==")
    print(f"  tokens {result['estimated_tokens']} / target {args.target} / ceiling {args.ceiling}")
    for s in result["sections"]:
        marker = "unchanged" if s["unchanged"] else f"{s['level']}"
        print(
            f"  [{marker}] {s['ref']} ({s['reason']}) ~{s['tokens']} tokens"
            + (" [required]" if s["required"] else "")
        )
        if s["text"]:
            print(f"      {s['text'][:120].replace(chr(10), ' ')}")
    if result["excluded"]:
        print("  excluded:")
        for e in result["excluded"]:
            print(f"    - {e['ref']} ({e['reason']})")


if __name__ == "__main__":
    main()
