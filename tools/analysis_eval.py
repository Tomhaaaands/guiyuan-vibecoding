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
import os
import sys
from pathlib import Path

from analysis_labels import score_labels
from analysis_provider import (
    SiliconFlowProvider,
    embed_statements,
    load_provider,
    resolve_provider,
)

sys.stdout.reconfigure(encoding="utf-8")


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
        help="aggregate F1 promotion threshold (default 0.25; semantic local-fallback ~0.169 vs a real backend ~0.299)",
    )
    parser.add_argument("--mode", choices=("id", "similarity", "semantic"), default="semantic")
    parser.add_argument("--threshold", type=float, default=0.7, help="similarity/semantic match cutoff")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cases = _load_cases(args.gold, args.suite, args.intent)
    provider = load_provider(resolve_provider(args.root, args.provider))
    embedder = None
    if args.mode == "semantic":
        api_key = os.environ.get("VCM_SILICONFLOW_API_KEY") or os.environ.get("SILICONFLOW_API_KEY")
        if not api_key:
            parser.error("semantic mode requires VCM_SILICONFLOW_API_KEY")
        base_url = os.environ.get("VCM_SILICONFLOW_BASE_URL") or SiliconFlowProvider.default_base
        cache: dict[str, list[float]] = {}

        def embedder(texts: list[str]) -> list[list[float]]:
            missing = [t for t in texts if t not in cache]
            if missing:
                vecs = embed_statements(
                    missing, api_key=api_key, base_url=base_url, model=args.embedding_model
                )
                cache.update(dict(zip(missing, vecs)))
            return [cache[t] for t in texts]

    results: list[dict] = []
    for case in cases:
        if not case["intent"]:
            results.append({"name": case["name"], "skipped": True})
            continue
        result = provider.analyze(case["intent"])
        scores = score_labels(
            result, case["gold"], mode=args.mode, embedder=embedder, threshold=args.threshold
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
            "min_f1": args.min_f1,
            "aggregate_f1": round(aggregate_f1, 4),
            "passed": passed,
            "cases": results,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"provider={provider.name} model={provider.model} mode={args.mode}")
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
