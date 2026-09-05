#!/usr/bin/env python3
"""P2 analysis scoring loop: run a provider against ground-truth fixtures (stdlib only).

This is the gate you run before wiring a real model backend. It calls the selected provider
directly (without persisting), scores its labeled output against gold fixtures, and fails when
the aggregate F1 is below --min-f1. Statement-similarity scoring is the default so a real model
with its own ids is judged on meaning, not on reproducing fixture ids.

Usage:
  python tools/analysis_eval.py --gold fixtures/login.json
  python tools/analysis_eval.py --suite fixtures --min-f1 0.6 --json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from analysis_labels import score_labels
from analysis_provider import load_provider, resolve_provider
from pb_bridge import (
    SIMILARITY_MAX_BYTES,
    SIMILARITY_MAX_TEXT_BYTES,
    SIMILARITY_MAX_TEXTS,
    TOOL_SIMILARITY,
    config as pb_config,
    pb_capabilities,
    pb_similarity,
)

sys.stdout.reconfigure(encoding="utf-8")


def _parse_pb_similarity_scores(response: object, expected: int) -> list[float]:
    """Validate and normalize one PB similarity response.

    Semantic evaluation is a quality gate, so a malformed or partial response must fail closed
    instead of silently turning missing candidates into zero scores.
    """
    if not isinstance(response, dict):
        raise RuntimeError("PB similarity returned a malformed response")
    if response.get("unavailable"):
        raise RuntimeError(str(response.get("reason") or "PB embedding unavailable"))
    if response.get("error"):
        raise RuntimeError(str(response["error"]))
    rows = response.get("results")
    if not isinstance(rows, list) or len(rows) != expected:
        raise RuntimeError("PB similarity returned an incomplete results array")
    scores: list[float | None] = [None] * expected
    for row in rows:
        if not isinstance(row, dict) or isinstance(row.get("index"), bool):
            raise RuntimeError("PB similarity returned an invalid result row")
        index = row.get("index")
        if not isinstance(index, int) or index < 0 or index >= expected or scores[index] is not None:
            raise RuntimeError("PB similarity returned invalid or duplicate indexes")
        try:
            score = float(row.get("score"))
        except (TypeError, ValueError) as exc:
            raise RuntimeError("PB similarity returned a non-numeric score") from exc
        if not math.isfinite(score):
            raise RuntimeError("PB similarity returned a non-finite score")
        scores[index] = score
    if any(score is None for score in scores):
        raise RuntimeError("PB similarity omitted a candidate index")
    return [float(score) for score in scores]


def _load_cases(gold: Path | None, suite: Path | None, intent: str | None) -> list[dict]:
    if gold and suite:
        raise SystemExit("use either --gold or --suite, not both")
    if suite:
        cases = []
        for path in sorted(suite.glob("*.json")):
            fixture = json.loads(path.read_text(encoding="utf-8"))
            cases.append(
                {
                    "name": path.stem,
                    "intent": fixture.get("intent", ""),
                    "gold": fixture.get("gold", fixture),
                }
            )
        return cases
    if not gold:
        raise SystemExit("provide --gold <file> or --suite <dir>")
    fixture = json.loads(gold.read_text(encoding="utf-8"))
    return [
        {
            "name": gold.stem,
            "intent": intent or fixture.get("intent", ""),
            "gold": fixture.get("gold", fixture),
        }
    ]


def _build_pb_similarity_scorer(root: Path, timeout: int):
    """Build a scorer that delegates every semantic comparison to PB.

    VCM receives only cosine scores, never vectors or model credentials.  Calls are
    chunked to PB's v1 limits so a large sentence-level fixture cannot accidentally
    trigger a request-size failure.
    """
    cfg = pb_config(root)
    if not cfg["pb_enabled"]:
        raise RuntimeError(
            "semantic mode requires PB: enable pb_enabled in .guiyuan-vibecoding/config.json"
        )
    discovered = pb_capabilities(root, timeout)
    if not discovered:
        raise RuntimeError("semantic mode could not complete the PB initialize/tools/list/capabilities handshake")
    if TOOL_SIMILARITY not in set(discovered.get("tools", [])):
        raise RuntimeError(f"PB does not expose required tool {TOOL_SIMILARITY}")

    def score(query: str, texts: list[str]) -> list[float]:
        query_bytes = len(str(query).encode("utf-8"))
        if query_bytes > SIMILARITY_MAX_TEXT_BYTES:
            raise RuntimeError("semantic query exceeds PB per-text byte limit")
        scores: list[float] = []
        chunk: list[str] = []
        used = query_bytes

        def flush() -> None:
            if not chunk:
                return
            response = pb_similarity(query, chunk, root=root, timeout=timeout)
            if response is None:
                raise RuntimeError("PB similarity request failed or became unreachable")
            scores.extend(_parse_pb_similarity_scores(response, len(chunk)))
            chunk.clear()

        for text in texts:
            value = str(text)
            size = len(value.encode("utf-8"))
            if size > SIMILARITY_MAX_TEXT_BYTES:
                raise RuntimeError("semantic candidate exceeds PB per-text byte limit")
            if chunk and (len(chunk) >= SIMILARITY_MAX_TEXTS or used + size > SIMILARITY_MAX_BYTES):
                flush()
                used = query_bytes
            chunk.append(value)
            used += size
        flush()
        return scores

    return score


def main() -> None:
    parser = argparse.ArgumentParser(description="Score an analysis provider against gold")
    parser.add_argument("--intent", help="intent text; defaults to the fixture's intent")
    parser.add_argument("--gold", type=Path, help="single gold fixture JSON")
    parser.add_argument("--suite", type=Path, help="directory of gold fixture JSONs")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--min-f1",
        type=float,
        default=0.25,
        help="aggregate F1 promotion threshold (default 0.25)",
    )
    parser.add_argument("--mode", choices=("id", "similarity", "semantic"), default="semantic")
    parser.add_argument("--threshold", type=float, default=0.7, help="similarity/semantic match cutoff")
    parser.add_argument("--pb-timeout", type=int, default=8, help="PB request timeout in seconds (semantic mode)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cases = _load_cases(args.gold, args.suite, args.intent)
    provider = load_provider(resolve_provider(args.root, args.provider))
    embedder = None
    similarity_scorer = None
    if args.mode == "semantic":
        try:
            similarity_scorer = _build_pb_similarity_scorer(args.root, args.pb_timeout)
        except RuntimeError as exc:
            parser.error(str(exc))

    results: list[dict] = []
    for case in cases:
        if not case["intent"]:
            results.append({"name": case["name"], "skipped": True})
            continue
        result = provider.analyze(case["intent"])
        scores = score_labels(
            result,
            case["gold"],
            mode=args.mode,
            embedder=embedder,
            similarity_scorer=similarity_scorer,
            threshold=args.threshold,
        )
        results.append(
            {
                "name": case["name"],
                "intent": case["intent"],
                "scores": scores,
                "f1": scores["overall"]["f1"],
            }
        )

    ran = [r for r in results if not r.get("skipped")]
    aggregate_f1 = sum(r["f1"] for r in ran) / len(ran) if ran else 0.0
    passed = aggregate_f1 >= args.min_f1

    if args.json:
        payload = {
            "provider": provider.name,
            "model": provider.model,
            "mode": args.mode,
            "semantic_backend": "pb" if args.mode == "semantic" else None,
            "min_f1": args.min_f1,
            "aggregate_f1": round(aggregate_f1, 4),
            "passed": passed,
            "cases": results,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        backend = "pb" if args.mode == "semantic" else "local"
        print(f"provider={provider.name} model={provider.model} mode={args.mode} scorer={backend}")
        for r in ran:
            o = r["scores"]["overall"]
            print(
                f"  {r['name']}: intent={r['intent']!r} f1={o['f1']} "
                f"(precision={o['precision']} recall={o['recall']})"
            )
            for bucket in (b for b in r["scores"] if b != "overall"):
                s = r["scores"][bucket]
                if s["fn"] or s["fp"]:
                    print(
                        f"      {bucket}: precision={s['precision']} recall={s['recall']} "
                        f"f1={s['f1']} (tp={s['tp']} fp={s['fp']} fn={s['fn']})"
                    )
        print(
            f"  aggregate f1={round(aggregate_f1, 4)} [required >= {args.min_f1}] "
            f"{'PASS' if passed else 'FAIL'}"
        )

    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
