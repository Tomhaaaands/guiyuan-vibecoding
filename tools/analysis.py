#!/usr/bin/env python3
"""P2 semantic-analysis orchestrator: intent -> labeled authority artifact (stdlib only).

This is the only place a provider is invoked. It picks the configured backend (default
local-fallback), calls it, validates the five labeled buckets, and persists the result as
an `analysis/<slug>` authority artifact at status draft. Provider failures degrade to the
local heuristic and are never presented as accepted. The deterministic core never imports
a provider; only this module does.

Usage:
  python tools/analysis.py --root <project> --intent "build an email login" --json
  python tools/analysis.py --root <project> --intent "ship an admin dashboard" --provider local-fallback
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

from artifact_store import ArtifactStore, content_hash
from analysis_labels import LABEL_BUCKETS, validate_labels
from analysis_provider import LocalFallbackProvider, load_provider, resolve_provider

sys.stdout.reconfigure(encoding="utf-8")

_ENTRY_RE = re.compile(r"^-\s*\*\*([^*]+)\*\*\s+(.+?)(?:\s*\(([^)]*)\))?$")


def _slug(intent: str, limit: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", intent.lower()).strip("-")
    return slug[:limit].strip("-") or "intent"


def _load_red_lines(root: Path) -> list[str]:
    """Load project red lines from the new root file or the legacy constitution path."""
    for path in (
        Path(root) / "red-lines.md",
        Path(root) / "docs" / "00-system" / "constitution" / "red-lines.md",
    ):
        if path.is_file():
            return _parse_red_lines(path.read_text(encoding="utf-8"))
    return []


def _parse_red_lines(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("-", "*")):
            stripped = stripped.lstrip("-* ").strip()
        if stripped and stripped != "---":
            out.append(stripped)
    return out


def _red_dice(a: str, b: str) -> float:
    def ngrams(text: str) -> set[str]:
        text = " " + str(text).lower() + " "
        text = re.sub(r"[^a-z0-9\u4e00-\u9fff ]", "", text)
        return {text[i : i + 2] for i in range(len(text) - 1)}

    ga, gb = ngrams(a), ngrams(b)
    if not ga or not gb:
        return 0.0
    return 2 * len(ga & gb) / (len(ga) + len(gb))


def _apply_red_lines(
    result: dict,
    red_lines: list[str],
    judge=None,
    threshold: float = 0.25,
) -> tuple[dict, bool]:
    """Route red-line-adjacent decisions/options to a judge before accepting them.

    Lexical overlap only shortlists candidates (topic detection). A `judge(statement,
    red_line) -> dict` decides respects/violates/unknown; 'respects' keeps the item (marked
    red_line_reviewed), while 'violates' or 'unknown' surfaces it as an open question and is
    never silently accepted. Without a judge, the default is conservative ('unknown').
    """
    touched = False
    for bucket in ("decisions", "options"):
        kept: list[dict] = []
        for item in result.get(bucket, []):
            statement = item.get("statement", "")
            best, red = 0.0, None
            for line in red_lines:
                sim = _red_dice(statement, line)
                if sim > best:
                    best, red = sim, line
            if best >= threshold and red:
                verdict = "unknown"
                if judge is not None:
                    try:
                        judged = judge(statement, red)
                        if isinstance(judged, dict):
                            verdict = str(judged.get("verdict", "unknown")).lower()
                    except Exception:  # noqa: BLE001 - a failed judge degrades to 'unknown'
                        verdict = "unknown"
                if verdict == "respects":
                    item["red_line_reviewed"] = True
                    kept.append(item)
                else:
                    touched = True
                    result.setdefault("open_questions", []).append(
                        {
                            "id": f"redline-{len(result.get('open_questions', [])) + 1}",
                            "statement": (
                                f"Confirm this does not violate the red line '{red}': {statement}"
                            ),
                            "source": "red-line",
                            "confidence": 0.9,
                        }
                    )
            else:
                kept.append(item)
        result[bucket] = kept
    return result, touched


def _render(result: dict, provenance: dict) -> str:
    lines = ["# Analysis", "", "## intent", str(result.get("intent", "")), ""]
    for bucket in LABEL_BUCKETS:
        lines.append(f"## {bucket}")
        items = result.get(bucket, [])
        if not items:
            lines.append("(none)")
        for item in items:
            meta = ", ".join(
                str(x)
                for x in (item.get("source", ""), item.get("confidence", ""))
                if x not in (None, "")
            )
            suffix = f" ({meta})" if meta else ""
            lines.append(f"- **{item['id']}** {item['statement']}{suffix}")
        lines.append("")
    lines.append("## provenance")
    for key in (
        "provider",
        "model",
        "idempotency_key",
        "created_at",
        "status",
        "degraded",
        "red_line_touch",
    ):
        lines.append(f"{key}: {provenance.get(key, '')}")
    return "\n".join(lines).rstrip() + "\n"


def _parse_section(section: list[str]) -> list[dict]:
    items: list[dict] = []
    for line in section:
        match = _ENTRY_RE.match(line.strip())
        if match:
            item_id, statement, meta = match.groups()
            entry: dict = {"id": item_id.strip(), "statement": statement.strip()}
            if meta:
                parts = [p.strip() for p in meta.split(",") if p.strip()]
                if parts:
                    entry["source"] = parts[0]
                if len(parts) > 1:
                    try:
                        entry["confidence"] = float(parts[1])
                    except ValueError:
                        entry["confidence"] = parts[1]
            items.append(entry)
    return items


def _parse(content: str) -> dict:
    sections: list[tuple[str, list[dict]]] = []
    current: tuple[str, list[dict]] = ("", [])
    for line in content.splitlines():
        if line.startswith("## "):
            if current[0]:
                sections.append(current)
            current = (line[3:].strip(), [])
        else:
            current[1].append(line)
    if current[0]:
        sections.append(current)

    result: dict = {"intent": "", **{b: [] for b in LABEL_BUCKETS}}
    provenance: dict = {}
    for heading, lines in sections:
        if heading in LABEL_BUCKETS:
            result[heading] = _parse_section(lines)
        elif heading == "intent":
            result["intent"] = "\n".join(lines).strip()
        elif heading == "provenance":
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    provenance[key.strip()] = value.strip()
    result["_provenance"] = provenance
    return result


def parse_analysis(content: str) -> dict:
    """Parse a persisted analysis artifact back into its labeled buckets (public API)."""
    return _parse(content)


def analyze(
    intent: str,
    *,
    root: Path,
    context: dict | None = None,
    provider: str | None = None,
    status: str = "draft",
    context_id: str | None = None,
    updated_at: str | None = None,
    force: bool = False,
) -> dict:
    intent = (intent or "").strip()
    if not intent:
        raise ValueError("intent is required")

    store = ArtifactStore(root)
    store.init()
    artifact_id = f"analysis/{_slug(intent)}"
    provider_name = resolve_provider(root, provider)
    red_lines = _load_red_lines(root)
    context_hash = content_hash(
        json.dumps(context, sort_keys=True) if context is not None else intent
    )[len("sha256:"):]
    red_hash = hashlib.sha256("\n".join(red_lines).encode("utf-8")).hexdigest()[:8]
    idempotency_key = hashlib.sha256(
        f"{provider_name}|{red_hash}|{intent}|{context_hash}".encode("utf-8")
    ).hexdigest()[:16]

    # Idempotent reuse: same provider + intent + context -> return the stored result.
    if store.exists(artifact_id) and not force:
        existing = _parse(store.get(artifact_id).content)
        provenance = existing.get("_provenance", {})
        if provenance.get("idempotency_key") == idempotency_key:
            existing.pop("_provenance", None)
            return {
                "artifact_id": artifact_id,
                "idempotency_key": idempotency_key,
                "reused": True,
                "provider": provenance.get("provider", provider_name),
                "model": provenance.get("model", ""),
                "status": provenance.get("status", status),
                "degraded": provenance.get("degraded", "false") == "true",
                "red_line_touch": provenance.get("red_line_touch", "false") == "true",
                "context_id": provenance.get("context_id", context_id),
                "result": existing,
                "provenance": provenance,
            }

    degraded = False
    selected_provider = load_provider(provider_name)
    try:
        result = selected_provider.analyze(intent, context)
    except Exception:  # noqa: BLE001 - any provider failure degrades to local heuristic
        degraded = True
        selected_provider = LocalFallbackProvider()
        result = selected_provider.analyze(intent, context)

    errors = validate_labels(result)
    if errors:
        raise ValueError(f"provider returned invalid labeled analysis: {errors}")

    result, red_line_touch = _apply_red_lines(
        result, red_lines, judge=selected_provider.judge_red_line
    )
    errors = validate_labels(result)
    if errors:
        raise ValueError(f"red-line handling produced invalid labeled analysis: {errors}")

    provenance = {
        "provider": selected_provider.name,
        "model": selected_provider.model,
        "idempotency_key": idempotency_key,
        "created_at": updated_at or datetime.date.today().isoformat(),
        "status": status,
        "context_id": context_id or "",
        "degraded": str(degraded).lower(),
        "red_line_touch": str(red_line_touch).lower(),
    }
    content = _render(result, provenance)
    meta = store.write(
        artifact_id,
        "analysis",
        content,
        status=status,
        depends_on=_extract_deps(result),
        updated_at=updated_at,
    )
    return {
        "artifact_id": artifact_id,
        "idempotency_key": idempotency_key,
        "reused": False,
        "provider": selected_provider.name,
        "model": selected_provider.model,
        "status": meta.status,
        "degraded": degraded,
        "red_line_touch": red_line_touch,
        "context_id": context_id,
        "result": result,
        "provenance": provenance,
    }


def _extract_deps(result: dict) -> list[str]:
    # Facts often point at existing artifacts by a `product/...`-style source; keep it
    # conservative and only link when the source string looks like an artifact ref.
    deps: list[str] = []
    for bucket in LABEL_BUCKETS:
        for item in result.get(bucket, []):
            source = item.get("source", "")
            if isinstance(source, str) and "artifact" in source and ":" not in source:
                deps.append(source)
    return deps


def main() -> None:
    parser = argparse.ArgumentParser(description="P2 semantic-analysis orchestrator")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--context-id", default=None)
    parser.add_argument("--status", default="draft")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out = analyze(
        args.intent,
        root=args.root,
        provider=args.provider,
        context_id=args.context_id,
        status=args.status,
        force=args.force,
    )
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(f"analysis {out['artifact_id']}@{'reused' if out['reused'] else 'new'}")
    print(f"  provider={out['provider']} model={out['model']} status={out['status']} degraded={out['degraded']}")
    for bucket in LABEL_BUCKETS:
        for item in out["result"][bucket]:
            print(f"  {bucket}: {item['id']} {item['statement']}")


if __name__ == "__main__":
    main()
