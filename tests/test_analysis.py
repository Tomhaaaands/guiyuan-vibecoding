"""Tests for analysis, analysis_labels, and analysis_provider (local, no network)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from analysis import (
    _parse_red_lines,
    _red_dice,
    analyze,
    parse_analysis,
)
from analysis_eval import _parse_pb_similarity_scores
from analysis_labels import (
    LABEL_BUCKETS,
    score_labels,
    validate_labels,
)
from analysis_provider import (
    LocalFallbackProvider,
    ProviderError,
    SiliconFlowProvider,
    _parse_judge,
    _parse_model_json,
    load_provider,
    parse_config,
    resolve_provider,
)


class RedLineParsingTest(unittest.TestCase):
    def test_parse_bullets_and_heading_skipped(self):
        text = "# Red lines\n- never expose a secret\n* no destructive ops\n\n---\nDo not delete user data"
        lines = _parse_red_lines(text)
        self.assertEqual(len(lines), 3)
        self.assertIn("never expose a secret", lines)

    def test_parse_dedups_empty(self):
        self.assertEqual(_parse_red_lines("\n# x\n"), [])


class RedDiceTest(unittest.TestCase):
    def test_exact_match_high(self):
        self.assertAlmostEqual(_red_dice("never expose secrets", "never expose secrets"), 1.0)

    def test_unrelated_low(self):
        self.assertLess(_red_dice("ship a red button", "no third-party identity"), 0.2)


class AnalysisLabelsTest(unittest.TestCase):
    def _candidate(self):
        return {
            "known_facts": [{"id": "f1", "statement": "A"}],
            "assumptions": [{"id": "a1", "statement": "B"}],
            "options": [{"id": "o1", "statement": "C"}],
            "decisions": [{"id": "d1", "statement": "D"}],
            "open_questions": [{"id": "q1", "statement": "E"}],
        }

    def test_validate_valid(self):
        self.assertEqual(validate_labels(self._candidate()), [])

    def test_validate_missing_id(self):
        bad = self._candidate()
        bad["known_facts"][0]["id"] = ""
        errors = validate_labels(bad)
        self.assertTrue(any("id" in e for e in errors))

    def test_validate_missing_bucket(self):
        bad = self._candidate()
        del bad["decisions"]
        errors = validate_labels(bad)
        self.assertTrue(any("decisions" in e for e in errors))

    def test_validate_wrong_type(self):
        bad = self._candidate()
        bad["options"] = "nope"
        errors = validate_labels(bad)
        self.assertTrue(any("expected a list" in e for e in errors))

    def test_score_id_mode(self):
        cand = self._candidate()
        gold = self._candidate()
        score = score_labels(cand, gold, mode="id")
        self.assertEqual(score["overall"]["f1"], 1.0)

    def test_score_similarity_perfect_paraphrase(self):
        cand = {
            "known_facts": [{"id": "x1", "statement": "user wants email login"}],
            "assumptions": [], "options": [], "decisions": [], "open_questions": [],
        }
        gold = {
            "known_facts": [{"id": "g1", "statement": "user wants email login"}],
            "assumptions": [], "options": [], "decisions": [], "open_questions": [],
        }
        score = score_labels(cand, gold, mode="similarity")
        self.assertEqual(score["known_facts"]["f1"], 1.0)

    def test_score_semantic_with_remote_scorer(self):
        cand = {
            "known_facts": [{"id": "x1", "statement": "candidate fact"}],
            "assumptions": [], "options": [], "decisions": [], "open_questions": [],
        }
        gold = {
            "known_facts": [{"id": "g1", "statement": "gold fact"}],
            "assumptions": [], "options": [], "decisions": [], "open_questions": [],
        }

        def scorer(query, texts):
            self.assertEqual(query, "candidate fact")
            self.assertEqual(texts, ["gold fact"])
            return [0.91]

        score = score_labels(cand, gold, mode="semantic", similarity_scorer=scorer)
        self.assertEqual(score["known_facts"]["f1"], 1.0)

    def test_score_semantic_rejects_two_scorers(self):
        with self.assertRaises(ValueError):
            score_labels({}, {}, mode="semantic", embedder=lambda _: [], similarity_scorer=lambda _q, _t: [])

    def test_score_invalid_mode(self):
        with self.assertRaises(ValueError):
            score_labels({}, {}, mode="bad")


class PbSimilarityResponseTest(unittest.TestCase):
    def test_validates_complete_indexed_scores(self):
        response = {"results": [{"index": 1, "score": 0.2}, {"index": 0, "score": 0.9}]}
        self.assertEqual(_parse_pb_similarity_scores(response, 2), [0.9, 0.2])

    def test_rejects_partial_or_malformed_scores(self):
        with self.assertRaises(RuntimeError):
            _parse_pb_similarity_scores({"results": [{"index": 0, "score": 0.9}]}, 2)
        with self.assertRaises(RuntimeError):
            _parse_pb_similarity_scores({"results": [{"index": 0, "score": "nan"}]}, 1)


class LocalProviderTest(unittest.TestCase):
    def test_produces_valid_buckets(self):
        result = LocalFallbackProvider().analyze("build an email login")
        self.assertEqual(validate_labels(result), [])
        self.assertIn("intent", result)

    def test_empty_intent_raises(self):
        with self.assertRaises(ProviderError):
            LocalFallbackProvider().analyze("  ")

    def test_default_judge_is_unknown(self):
        judge = LocalFallbackProvider().judge_red_line("x", "y")
        self.assertEqual(judge["verdict"], "unknown")


class ProviderRegistryTest(unittest.TestCase):
    def test_resolve_explicit(self):
        self.assertEqual(resolve_provider(Path("."), "local-fallback"), "local-fallback")

    def test_resolve_fallback(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            try:
                os.environ.pop("VCM_ANALYSIS_PROVIDER", None)
            except KeyError:
                pass
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(resolve_provider(Path(tmp)), "local-fallback")

    def test_load_provider_unknown_falls_back(self):
        provider = load_provider("does-not-exist")
        self.assertIsInstance(provider, LocalFallbackProvider)

    def test_config_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = root / ".vibecoding"
            cfg.mkdir()
            (cfg / "provider.toml").write_text("[analysis]\nprovider = 'local-fallback'\n", encoding="utf-8")
            self.assertEqual(parse_config(root).get("analysis", {}).get("provider"), "local-fallback")


class SiliconFlowHelpersTest(unittest.TestCase):
    def test_parse_model_json_strips_fence(self):
        content = '```json\n{"known_facts": [], "intent": "x"}\n```'
        parsed = _parse_model_json(content, "x")
        self.assertEqual(parsed["intent"], "x")

    def test_parse_model_json_non_json_raises(self):
        with self.assertRaises(ProviderError):
            _parse_model_json("not json", "x")

    def test_parse_judge_valid(self):
        self.assertEqual(_parse_judge('{"verdict": "violates", "confidence": 0.9}')["verdict"], "violates")

    def test_parse_judge_unparseable_is_unknown(self):
        self.assertEqual(_parse_judge("nope")["verdict"], "unknown")

    def test_parse_judge_invalid_verdict(self):
        self.assertEqual(_parse_judge('{"verdict": "maybe"}')["verdict"], "unknown")

    def test_siliconflow_without_key_raises(self):
        provider = SiliconFlowProvider()
        with mock.patch.dict(os.environ, {}, clear=True):
            provider.api_key = ""
            with self.assertRaises(ProviderError):
                provider.analyze("x")


class AnalyzeOrchestratorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_analyze_local_persists_and_returns(self):
        out = analyze("ship an admin dashboard", root=self.root, provider="local-fallback")
        self.assertEqual(out["provider"], "local-fallback")
        self.assertFalse(out["degraded"])
        for bucket in LABEL_BUCKETS:
            self.assertIsInstance(out["result"][bucket], list)

    def test_empty_intent_raises(self):
        with self.assertRaises(ValueError):
            analyze("   ", root=self.root, provider="local-fallback")

    def test_red_line_shortlist_flags(self):
        (self.root / "red-lines.md").write_text("# Red lines\nnever expose secrets\n", encoding="utf-8")
        out = analyze("design an auth provider", root=self.root, provider="local-fallback")
        self.assertIn("red_line_touch", out)
        self.assertIsInstance(out["red_line_touch"], bool)

    def test_idempotent_reuse_and_force(self):
        a = analyze("build a quote generator", root=self.root, provider="local-fallback")
        b = analyze("build a quote generator", root=self.root, provider="local-fallback")
        self.assertTrue(b["reused"])
        c = analyze("build a quote generator", root=self.root, provider="local-fallback", force=True)
        self.assertFalse(c["reused"])


class ParseAnalysisTest(unittest.TestCase):
    def test_roundtrip(self):
        result = LocalFallbackProvider().analyze("roundtrip intents everywhere")
        text = (
            "# Analysis\n\n## intent\nroundtrip intents everywhere\n\n"
            f"## known_facts\n- **f1** user wants roundtrip (intent, 0.5)\n"
        )
        parsed = parse_analysis(text)
        self.assertEqual(parsed["intent"], "roundtrip intents everywhere")
        self.assertEqual(len(parsed["known_facts"]), 1)


if __name__ == "__main__":
    unittest.main()
