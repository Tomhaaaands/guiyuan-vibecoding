#!/usr/bin/env python3
"""Validation and ground-truth scoring for P2 labeled analysis (stdlib only).

This is the provider-agnostic contract for ANALYSIS output: a candidate analysis carries
five labeled buckets, each item has an id and a statement. Score it against a gold fixture
either by exact id (deterministic, for fixture regression) or by statement-similarity
(character-bigram Dice similarity, so a real provider with different ids and paraphrases can be
judged without reproducing fixture ids).

Usage:
  python tools/analysis_labels.py validate --file candidate.json
  python tools/analysis_labels.py score --candidate c.json --gold g.json
  python tools/analysis_labels.py score --candidate c.json --gold g.json --mode similarity
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable

sys.stdout.reconfigure(encoding="utf-8")

LABEL_BUCKETS = ("known_facts", "assumptions", "options", "decisions", "open_questions")
_NORM_RE = re.compile(r"[a-z0-9\u4e00-\u9fff ]")


def validate_labels(candidate: dict) -> list[str]:
    """Check a candidate analysis has the five labeled buckets with valid items."""
    errors: list[str] = []
    for bucket in LABEL_BUCKETS:
        items = candidate.get(bucket)
        if not isinstance(items, list):
            errors.append(f"{bucket}: expected a list")
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{bucket}[{i}]: expected an object")
                continue
            label = f"{bucket}[{i}]"
            if not str(item.get("id", "")).strip():
                errors.append(f"{label}: missing non-empty id")
            if not str(item.get("statement", "")).strip():
                errors.append(f"{label}: missing non-empty statement")
    return errors


def _ngrams(text: str, n: int = 2) -> set[str]:
    text = " " + str(text).lower() + " "
    text = "".join(_NORM_RE.findall(text))
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def _dice(a: str, b: str) -> float:
    ga, gb = _ngrams(a), _ngrams(b)
    if not ga or not gb:
        return 0.0
    return 2 * len(ga & gb) / (len(ga) + len(gb))


def _match_similarity(cand: list[dict], want: list[dict], threshold: float = 0.40) -> tuple[int, int, int]:
    """Greedy bipartite match by statement character-bigram Dice; returns tp, fp, fn."""
    remaining = list(want)
    tp = 0
    for c in cand:
        best = -1.0
        best_i = -1
        for g_i, g in enumerate(remaining):
            sim = _dice(c.get("statement", ""), g.get("statement", ""))
            if sim > best:
                best, best_i = sim, g_i
        if best_i >= 0 and best >= threshold:
            tp += 1
            remaining.pop(best_i)
    fp = len(cand) - tp
    fn = len(remaining)
    return tp, fp, fn


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def _match_embedding(
    cand_items: list[dict],
    want_items: list[dict],
    vec_map: dict,
    threshold: float,
) -> tuple[int, int, int]:
    remaining = list(want_items)
    tp = 0
    for c in cand_items:
        cv = vec_map.get(c.get("statement", ""))
        if cv is None:
            continue
        best, best_i = -1.0, -1
        for i, g in enumerate(remaining):
            gv = vec_map.get(g.get("statement", ""))
            if gv is None:
                continue
            sim = _cosine(cv, gv)
            if sim > best:
                best, best_i = sim, i
        if best_i >= 0 and best >= threshold:
            tp += 1
            remaining.pop(best_i)
    return tp, len(cand_items) - tp, len(remaining)


def score_labels(
    candidate: dict,
    gold: dict,
    mode: str = "id",
    embedder: Callable[[list[str]], list[list[float]]] | None = None,
    threshold: float = 0.7,
) -> dict:
    """Score a candidate against a gold fixture, per bucket.

    mode="id" requires the exact expected item ids (deterministic fixtures); mode="similarity"
    matches statements by character-bigram Dice; mode="semantic" matches by embedding cosine
    (embedder must be a callable list[str] -> list[list[float]]) so meaning, not wording, is
    measured.
    """
    if mode not in ("id", "similarity", "semantic"):
        raise ValueError("mode must be 'id', 'similarity', or 'semantic'")

    vec_map: dict = {}
    if mode == "semantic":
        if embedder is None:
            raise ValueError("semantic mode requires an embedder callable")
        all_texts: list[str] = []
        for bucket in LABEL_BUCKETS:
            all_texts.extend(
                i.get("statement", "")
                for i in candidate.get(bucket, []) + gold.get(bucket, [])
                if isinstance(i, dict) and i.get("statement")
            )
        vectors = embedder(all_texts)
        vec_map = {t: v for t, v in zip(all_texts, vectors)}

    result: dict[str, dict] = {"overall": {"tp": 0, "fp": 0, "fn": 0}}
    for bucket in LABEL_BUCKETS:
        cand_items = [i for i in candidate.get(bucket, []) if isinstance(i, dict)]
        want_items = [i for i in gold.get(bucket, []) if isinstance(i, dict)]
        if mode == "id":
            cand = {str(i.get("id", "")) for i in cand_items}
            want = {str(i.get("id", "")) for i in want_items}
            tp = len(cand & want)
            fp = len(cand - want)
            fn = len(want - cand)
        elif mode == "similarity":
            tp, fp, fn = _match_similarity(cand_items, want_items)
        else:
            tp, fp, fn = _match_embedding(cand_items, want_items, vec_map, threshold)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        result[bucket] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
        result["overall"]["tp"] += tp
        result["overall"]["fp"] += fp
        result["overall"]["fn"] += fn
    t = result["overall"]
    p = t["tp"] / (t["tp"] + t["fp"]) if (t["tp"] + t["fp"]) else 0.0
    r = t["tp"] / (t["tp"] + t["fn"]) if (t["tp"] + t["fn"]) else 0.0
    result["overall"]["precision"] = round(p, 4)
    result["overall"]["recall"] = round(r, 4)
    result["overall"]["f1"] = round(2 * p * r / (p + r) if (p + r) else 0.0, 4)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and score labeled analysis")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validate")
    p.add_argument("--file", type=Path, required=True)
    p = sub.add_parser("score")
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--gold", type=Path, required=True)
    p.add_argument("--mode", choices=("id", "similarity"), default="id")
    args = parser.parse_args()

    def load(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    if args.cmd == "validate":
        errors = validate_labels(load(args.file))
        if errors:
            for e in errors:
                print(f"  [error] {e}")
            raise SystemExit(1)
        print("labeled analysis valid ✓")
    else:
        scores = score_labels(load(args.candidate), load(args.gold), mode=args.mode)
        print(json.dumps(scores, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
