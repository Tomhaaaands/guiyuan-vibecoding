"""Tests for the deterministic context compiler and token budget."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from artifact_store import ArtifactStore
from context_compiler import (
    BudgetConflictError,
    PHASES,
    compile_context,
)
from context_budget import (
    DEFAULT_BUDGET,
    DEFAULT_TARGET,
    audit,
    default_startup_paths,
    estimate_tokens,
    resolve_paths,
)


class EstimateTokensTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(estimate_tokens(""), 0)

    def test_ascii_quadrant(self):
        self.assertEqual(estimate_tokens("abcd"), 1)

    def test_hanzi_counts_one_per_char(self):
        self.assertEqual(estimate_tokens("中文"), 2)

    def test_whitespace_ignored(self):
        self.assertEqual(estimate_tokens("a b"), estimate_tokens("ab"))


class ContextBudgetTest(unittest.TestCase):
    def test_default_startup_paths_resolve(self):
        paths = default_startup_paths()
        self.assertTrue(all(p.exists() for p in paths))

    def test_audit_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            f = root / "AGENTS.md"
            f.write_text("hello world", encoding="utf-8")
            rows, total = audit([f])
            self.assertEqual(len(rows), 1)
            self.assertGreater(total, 0)

    def test_resolve_paths_relative_to_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = resolve_paths(["AGENTS.md"], root)
            self.assertEqual(p[0], root / "AGENTS.md")

    def test_resolve_paths_absolute(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "x.md"
            f.write_text("x", encoding="utf-8")
            p = resolve_paths([str(f)])
            self.assertEqual(p[0], f)


def _seed_store(store: ArtifactStore):
    store.init()
    store.write(
        "product/auth",
        "product-spec",
        "## acceptance\nUser can log in.\n## scope\nemail login",
        status="accepted",
    )
    store.write(
        "technical/auth",
        "technical-spec",
        "## contract.login\nPOST /auth/login -> {token}. Ref user_id only from server.",
        status="review",
    )
    store.write(
        "decisions/auth-provider",
        "decisions",
        "## constraint\nUse local provider only.\n",
        status="accepted",
    )
    store.write(
        "tasks/auth-07",
        "tasks",
        "## acceptance\nLogin contract tests green.\n## status\nproposed\n## priority\n1\n",
        status="draft",
    )
    store.write(
        "project-state",
        "project-state",
        "## stage\nEXECUTION\n## task\ntasks/auth-07\n## blocker\nnone\n",
        status="accepted",
    )


class CompileContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = ArtifactStore(Path(self.tmp.name))
        _seed_store(self.store)

    def test_invalid_phase(self):
        with self.assertRaises(ValueError):
            compile_context(self.store, phase="BOGUS")

    def test_invalid_budget(self):
        with self.assertRaises(ValueError):
            compile_context(self.store, phase="EXECUTION", target_budget=100, hard_ceiling=50)

    def test_excludes_prohibited_archive(self):
        self.store.write("archive/r14", "archive", "## summary\nx\n", status="accepted")
        out = compile_context(self.store, phase="EXECUTION")
        self.assertTrue(any(e["reason"] == "archaeology-not-required" for e in out["excluded"]))

    def test_required_first_and_reason(self):
        out = compile_context(self.store, phase="EXECUTION", refs=[
            "product/auth", "technical/auth", "decisions/auth-provider", "tasks/auth-07",
        ])
        included = out["included"]
        self.assertGreaterEqual(len(included), 1)
        # Required (product-spec / decisions / tasks) sorts before technical-spec (optional).
        self.assertEqual(included[0]["reason"], "required-safety/acceptance")

    def test_delta_marks_unchanged(self):
        out = compile_context(
            self.store,
            phase="EXECUTION",
            refs=["product/auth", "decisions/auth-provider"],
            prev_context_id="ctx-old",
            changed=["product/auth"],
        )
        sections = out["sections"]
        self.assertTrue(any(s["unchanged"] for s in sections))
        self.assertTrue(out["delta"])
        self.assertEqual(out["prev_context_id"], "ctx-old")

    def test_hard_ceiling_conflict(self):
        # Large required content that can never fit a tiny ceiling must raise, not truncate.
        self.store.write(
            "product/big",
            "product-spec",
            "## acceptance\n" + ("very long acceptance text here. " * 200),
            status="accepted",
        )
        with self.assertRaises(BudgetConflictError):
            compile_context(self.store, phase="EXECUTION", hard_ceiling=1, target_budget=1)

    def test_default_phase_is_valid(self):
        for phase in PHASES:
            out = compile_context(self.store, phase=phase)
            self.assertIn("sections", out)

    def test_context_id_consistent(self):
        a = compile_context(self.store, phase="EXECUTION", refs=["product/auth"])["context_id"]
        b = compile_context(self.store, phase="EXECUTION", refs=["product/auth"])["context_id"]
        self.assertEqual(a, b)

    def test_budget_from_compiler_below_ceiling(self):
        out = compile_context(self.store, phase="EXECUTION", hard_ceiling=DEFAULT_BUDGET)
        self.assertLessEqual(out["estimated_tokens"], DEFAULT_BUDGET)


if __name__ == "__main__":
    unittest.main()
