#!/usr/bin/env python3
"""Behavior-evaluation harness for the P2 local core (deterministic, stdlib only).

Runs provider-free scenarios in a temporary directory to verify the typed artifact
store and the context compiler keep their safety and token contracts, and to establish
the analysis-labeling scorer that a provider will be measured against later.

Usage:
  python tools/behavior_harness.py
  python tools/behavior_harness.py --scenario store_lifecycle
  python tools/behavior_harness.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from artifact_store import ArtifactStore, content_hash
from context_compiler import BudgetConflictError, compile_context
from analysis_labels import score_labels, validate_labels
from analysis import analyze
from analysis_provider import PROVIDERS, LocalFallbackProvider
from artifact_consistency import check as check_consistency
from artifact_generate import generate as generate_artifacts
from task_graph import next_task, readiness, validate as validate_task_graph
from receipt_loop import run_cycle
from experience_loop import collect_experience, shadow_evaluate, write_experience
from mvp_walkthrough import run_walkthrough

sys.stdout.reconfigure(encoding="utf-8")


# ----- fixtures -----

def _scaffold(root: Path) -> ArtifactStore:
    store = ArtifactStore(root)
    store.init()
    store.write(
        "product/auth",
        "product-spec",
        "## acceptance\nA user can log in with email and complete the flow.\n",
        status="accepted",
    )
    store.write(
        "technical/auth",
        "technical-spec",
        "## contract.login\nPOST /auth/login -> {token}. Ref: user_id only from server.\n",
        status="review",
    )
    store.write(
        "decisions/auth-provider",
        "decisions",
        "## constraint\nUse local provider only; no third-party identity service.\n",
        status="accepted",
    )
    store.write(
        "roadmap/auth",
        "roadmap",
        "## milestone\nP5 ships a verification evidence loop.\n",
        status="accepted",
    )
    store.write(
        "tasks/auth-07",
        "tasks",
        "## acceptance\nLogin contract tests green.\n## blocker\nHarness not wired.\n",
        status="draft",
    )
    store.write(
        "project-state",
        "project-state",
        "## stage\nEXECUTION\n## task\ntasks/auth-07\n## blocker\nnone\n",
        status="accepted",
    )
    store.write(
        "archive/r14",
        "archive",
        "Historical round narrative; archaeology only.\n",
        status="archived",
    )
    return store


# ----- scenarios -----

def scenario_store_lifecycle() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        store = _scaffold(Path(tmp))
        a = store.get("product/auth")
        assert a.metadata.revision == 1
        assert a.metadata.content_hash == content_hash(a.content)
        # Idempotent same-content write.
        again = store.write("product/auth", "product-spec", a.content, status="accepted")
        if again.revision != 1:
            return False, "idempotent write bumped the revision"
        # Change -> revision 2 + supersedes link.
        v2 = store.write(
            "product/auth", "product-spec", "## acceptance\nChanged acceptance.\n", status="accepted"
        )
        if v2.revision != 2 or v2.supersedes != "product/auth@1":
            return False, f"revision/supersedes wrong: {v2.revision}, {v2.supersedes}"
        if store.validate():
            return False, "store reported errors after healthy writes"
        # Tamper content so the recorded hash no longer matches.
        (Path(tmp) / "artifacts" / "product" / "auth.md").write_text(
            "tampered", encoding="utf-8"
        )
        errors = store.validate()
        if not any("hash mismatch" in e for e in errors):
            return False, "tampered content was not detected"
        return True, "store lifecycle, idempotency, revision, hash-check all pass"


def scenario_compiler_exclusion() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        store = _scaffold(Path(tmp))
        ctx = compile_context(
            store,
            phase="EXECUTION",
            task_id="tasks/auth-07",
            refs=["tasks/auth-07", "project-state", "technical/auth", "decisions/auth-provider"],
        )
        refs = {s["ref"].split("@")[0] for s in ctx["sections"]}
        if "archive/r14" in refs:
            return False, "archive artifact leaked into EXECUTION context"
        if "tasks/auth-07" not in refs or "technical/auth" not in refs:
            return False, "required acceptance/contract slice is missing"
        if ctx["estimated_tokens"] > ctx["hard_ceiling"]:
            return False, f"context over ceiling: {ctx['estimated_tokens']}"
        return True, "EXECUTION includes required slices and excludes archive/history"


def scenario_compiler_degradation() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        store = _scaffold(Path(tmp))
        # A moderately large optional technical-spec that overruns a tiny ceiling but
        # still fits after it is downgraded to an L0 pointer card (not dropped).
        store.write(
            "technical/big",
            "technical-spec",
            "## contract\n" + ("x" * 2000) + "\n",
            status="draft",
        )
        try:
            ctx = compile_context(
                store,
                phase="PLANNING",
                refs=["roadmap/auth", "project-state", "decisions/auth-provider", "technical/big"],
                target_budget=200,
                hard_ceiling=400,
            )
        except BudgetConflictError as exc:
            return False, f"unexpected conflict: {exc}"
        big = next((s for s in ctx["sections"] if s["ref"].startswith("technical/big")), None)
        if big is None:
            return False, "optional slice was dropped before the downgrade path was exercised"
        if big["level"] != "L0":
            return False, "oversized optional slice was not downgraded to an L0 pointer card"
        if ctx["estimated_tokens"] > ctx["hard_ceiling"]:
            return False, "context over ceiling after degradation"
        return True, "oversized optional slice downgraded to L0 and required slices retained"


def scenario_compiler_conflict() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        store = _scaffold(Path(tmp))
        store.write(
            "technical/required-big",
            "technical-spec",
            "## contract\n" + ("y" * 6000) + "\n",
            status="accepted",
        )
        try:
            compile_context(
                store,
                phase="EXECUTION",
                refs=["technical/required-big", "tasks/auth-07", "product/auth"],
                target_budget=100,
                hard_ceiling=200,
            )
        except BudgetConflictError:
            return True, "required evidence that cannot fit raises BudgetConflict"
        return False, "required safety/acceptance evidence was silently truncated"


def scenario_delta() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        store = _scaffold(Path(tmp))
        ctx = compile_context(
            store,
            phase="EXECUTION",
            refs=["project-state", "technical/auth", "decisions/auth-provider"],
            prev_context_id="exec-tasks/auth-07-1",
            changed=["technical/auth"],
        )
        by_ref = {s["ref"].split("@")[0]: s for s in ctx["sections"]}
        if "technical/auth" not in by_ref or by_ref["technical/auth"]["unchanged"]:
            return False, "changed artifact was not included with text"
        if by_ref["technical/auth"]["text"].strip() == "":
            return False, "changed artifact has no text"
        for ref in ("project-state", "decisions/auth-provider"):
            if ref not in by_ref or not by_ref[ref]["unchanged"]:
                return False, f"unchanged {ref} was replayed instead of referenced"
        if by_ref["project-state"]["text"].strip() != "":
            return False, "unchanged artifact replayed text in delta mode"
        return True, "delta mode references unchanged context and emits only changed slices"


def scenario_analysis_labels() -> tuple[bool, str]:
    gold = {
        "known_facts": [{"id": "f1", "statement": "Uses email login"}],
        "assumptions": [{"id": "a1", "statement": "User has an account"}],
        "options": [{"id": "o1", "statement": "OAuth"}],
        "decisions": [{"id": "d1", "statement": "Local provider"}],
        "open_questions": [{"id": "q1", "statement": "Rate limit?"}],
    }
    candidate = {
        "known_facts": [{"id": "f1", "statement": "Uses email login"}, {"id": "f9", "statement": "extra"}],
        "assumptions": [],
        "options": [{"id": "o1", "statement": "OAuth"}],
        "decisions": [{"id": "d1", "statement": "Local provider"}],
        "open_questions": [{"id": "q1", "statement": "Rate limit?"}],
    }
    errors = validate_labels(candidate)
    if errors:
        return False, f"label validator rejected a well-formed candidate: {errors}"
    scores = score_labels(candidate, gold)
    if not (0.0 < scores["overall"]["f1"] < 1.0):
        return False, f"scorer did not produce a meaningful partial score: {scores['overall']}"
    if scores["assumptions"]["recall"] != 0.0 or scores["assumptions"]["precision"] != 0.0:
        return False, "empty candidate bucket should score zero"
    return True, "analysis-label validator and ground-truth scorer are usable"


def scenario_analysis_local_fallback() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = analyze("build an email login", root=root)
        if validate_labels(out["result"]):
            return False, "local-fallback produced an invalid labeled result"
        if out["provider"] != "local-fallback" or out["reused"]:
            return False, "expected a fresh local-fallback result"
        store = ArtifactStore(root)
        artifact_id = "analysis/build-an-email-login"
        if not store.exists(artifact_id):
            return False, "analysis result was not persisted"
        meta = store.get(artifact_id).metadata
        if meta.kind != "analysis" or meta.status != "draft":
            return False, "analysis artifact has the wrong kind/status"
        again = analyze("build an email login", root=root)
        if not again["reused"]:
            return False, "idempotent re-analysis did not reuse the stored result"
        if store.validate():
            return False, "analysis write left the store inconsistent"
        return True, "provider isolation, persistence, and idempotency all hold"


def scenario_analysis_empty_intent() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            analyze("   ", root=Path(tmp))
        except ValueError:
            return True, "empty intent is rejected"
        return False, "empty intent was accepted"


def scenario_analysis_provider_fallback() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        class _Bad(LocalFallbackProvider):
            name = "bad"

            def analyze(self, intent, context=None):  # noqa: D102
                raise RuntimeError("provider boom")

        PROVIDERS["bad"] = _Bad
        try:
            out = analyze("build an email login", root=Path(tmp), provider="bad")
        finally:
            PROVIDERS.pop("bad", None)
        if not out["degraded"] or out["provider"] != "local-fallback":
            return False, "provider failure was not degraded to local-fallback"
        if validate_labels(out["result"]):
            return False, "degraded result is invalid"
        return True, "provider failure degrades to a valid local-fallback result"


def scenario_store_kind_mismatch() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        store = ArtifactStore(Path(tmp))
        try:
            store.write("product/auth", "technical-spec", "content", status="draft")
        except ValueError:
            return True, "kind that contradicts the artifact namespace is rejected"
        return False, "contradictory kind was accepted"


def scenario_compiler_missing_ref() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        store = _scaffold(Path(tmp))
        try:
            compile_context(store, phase="EXECUTION", refs=["product/nope"])
        except KeyError:
            return True, "a missing artifact reference raises instead of silently omitting"
        return False, "missing artifact reference was silently ignored"


def scenario_analysis_similarity_mode() -> tuple[bool, str]:
    gold = {
        "known_facts": [
            {"id": "k1", "statement": "users need email authentication"},
            {"id": "k2", "statement": "password reset is required"},
        ],
        "assumptions": [],
        "options": [{"id": "o1", "statement": "email magic link login as an alternative"}],
        "decisions": [{"id": "d1", "statement": "store only a hashed password"}],
        "open_questions": [{"id": "q1", "statement": "what is the reset link expiry"}],
    }
    good = {
        "known_facts": [
            {"id": "x1", "statement": "users authenticate with email"},
            {"id": "x2", "statement": "password reset needed"},
        ],
        "assumptions": [],
        "options": [{"id": "y1", "statement": "offer an email magic link alternative"}],
        "decisions": [{"id": "y2", "statement": "keep only a hashed password"}],
        "open_questions": [{"id": "y3", "statement": "reset link expiry"}],
    }
    bad = {
        "known_facts": [{"id": "z1", "statement": "user stated an intent unknown"}],
        "assumptions": [{"id": "z2", "statement": "nothing is certain yet"}],
        "options": [],
        "decisions": [],
        "open_questions": [{"id": "z3", "statement": "clarify the intent"}],
    }
    good_scores = score_labels(good, gold, mode="similarity")
    bad_scores = score_labels(bad, gold, mode="similarity")
    if good_scores["overall"]["f1"] < 0.9:
        return False, f"a semantically-close candidate scored too low: {good_scores['overall']['f1']}"
    if bad_scores["overall"]["f1"] > good_scores["overall"]["f1"]:
        return False, "a generic candidate outscored a semantically-close one"
    return True, "similarity mode rewards paraphrase quality independent of ids"


def scenario_analysis_red_line() -> tuple[bool, str]:
    from analysis import _apply_red_lines, _load_red_lines

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "red-lines.md").write_text(
            "# Red lines\n- Admin routes require server-side role checks; UI hiding alone is not authorization\n",
            encoding="utf-8",
        )
        reds = _load_red_lines(root)
        if not reds or "server-side role" not in reds[0]:
            return False, "red-lines.md was not parsed"
        result = {
            "intent": "add admin dashboard",
            "known_facts": [],
            "assumptions": [],
            "options": [{"id": "o1", "statement": "enforce roles on the server"}],
            "decisions": [{"id": "d2", "statement": "trust the client-side role flag"}],
            "open_questions": [],
        }
        out, touched = _apply_red_lines(result, reds)
        if not touched:
            return False, "red-line overlap was not detected"
        if out["decisions"] or out["options"]:
            return False, "red-line-adjacent decision/option was retained as confirmed"

        class _Violate(LocalFallbackProvider):
            name = "violate"

            def analyze(self, intent, context=None):  # noqa: D102
                return {
                    "intent": intent,
                    "known_facts": [],
                    "assumptions": [],
                    "options": [{"id": "o1", "statement": "trust the client-side role flag"}],
                    "decisions": [],
                    "open_questions": [],
                }

        PROVIDERS["violate"] = _Violate
        try:
            out2 = analyze("add admin dashboard", root=root, provider="violate")
        finally:
            PROVIDERS.pop("violate", None)
        if not out2.get("red_line_touch"):
            return False, "red-line touch was not recorded in provenance"
        if out2["result"]["options"]:
            return False, "violating option survived the orchestrator's red-line gate"
        if not any("client-side role flag" in q["statement"] for q in out2["result"]["open_questions"]):
            return False, "violating option was not surfaced as an open question"
        return True, "red-line overlap surfaces as an open question and is not silently accepted"


def scenario_analysis_red_line_judge() -> tuple[bool, str]:
    from analysis import _apply_red_lines

    reds = ["Admin routes require server-side role checks; UI hiding alone is not authorization"]

    def judge(statement: str, red_line: str) -> dict:
        if "client-side role flag" in statement.lower() or "trust the client" in statement.lower():
            return {"verdict": "violates", "confidence": 0.9, "reason": "auth bypass"}
        return {"verdict": "respects", "confidence": 0.9, "reason": "server-side check"}

    result = {
        "intent": "add admin dashboard",
        "known_facts": [],
        "assumptions": [],
        "options": [{"id": "o1", "statement": "enforce roles on the server"}],
        "decisions": [{"id": "d2", "statement": "trust the client-side role flag"}],
        "open_questions": [],
    }
    out, touched = _apply_red_lines(result, reds, judge=judge)
    if not touched:
        return False, "violating decision was not detected by the model judge"
    if out["decisions"]:
        return False, "violating decision was kept as confirmed"
    if not (out["options"] and out["options"][0].get("red_line_reviewed")):
        return False, "a 'respects' option was not kept and marked red_line_reviewed"
    if not any("client-side role flag" in q["statement"] for q in out["open_questions"]):
        return False, "violating decision was not surfaced as an open question"
    return True, "model-routed judge keeps 'respects' and surfaces 'violates/unknown'"


def scenario_artifact_consistency() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        store = ArtifactStore(Path(tmp))
        store.init()
        store.write("product/auth", "product-spec", "## acceptance\nlogin works\n", status="accepted")
        store.write("tasks/auth-07", "tasks", "## acceptance\ntests green\n", status="accepted")
        store.write("receipts/auth-07", "receipts", "## verdict\npass\n", status="accepted")
        store.write("project-state", "project-state", "## stage\nDELIVERY\n", status="accepted")
        clean = [i for i in check_consistency(store) if i["severity"] == "error"]
        if clean:
            return False, f"consistent store was flagged: {clean}"
        # Broken references/gaps.
        store.write("product/broken", "product-spec", "no acceptance here\n", status="accepted")
        store.write(
            "product/broken2",
            "product-spec",
            "## acceptance\nok\n",
            status="accepted",
            supersedes="product/auth@99",
        )
        broken = check_consistency(store)
        rules = {i["rule"] for i in broken if i["severity"] == "error"}
        if not {"missing_acceptance", "supersedes_revision_gap"}.issubset(rules):
            return False, f"expected errors missing: {rules}"
        if not any(i["rule"] == "accepted_superseded" and i["severity"] == "warn" for i in broken):
            return False, "accepted-but-superseded was not a warning"

    with tempfile.TemporaryDirectory() as tmp:
        store2 = ArtifactStore(Path(tmp))
        store2.init()
        store2.write("project-state", "project-state", "## stage\nDELIVERY\n", status="accepted")
        states = check_consistency(store2)
        if not any(i["rule"] == "state_without_receipt" and i["severity"] == "error" for i in states):
            return False, "delivery-stage state without a receipt was not flagged"
    return True, "missing acceptance, supersedes gap, and state-without-receipt are all caught"


def scenario_artifact_generate() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = ArtifactStore(root)
        store.init()
        store.write(
            "analysis/build-an-email-login",
            "analysis",
            "## intent\nbuild an email login\n\n## known_facts\n- **k1** users authenticate with email\n\n"
            "## decisions\n- **d1** store a salted password hash\n\n"
            "## open_questions\n- **q1** what is the reset link expiry\n",
            status="accepted",
        )
        out = generate_artifacts(root, "analysis/build-an-email-login")
        if not store.exists("product/build-an-email-login") or not store.exists(
            "decisions/build-an-email-login"
        ):
            return False, "generated authority artifacts are missing"
        product = store.get("product/build-an-email-login")
        if product.metadata.kind != "product-spec" or "## acceptance" not in product.content:
            return False, "generated product-spec has no acceptance clause"
        if product.metadata.status != "draft" or "analysis/build-an-email-login" not in product.metadata.depends_on:
            return False, "generated product-spec is not a draft linked to its source analysis"
        errors = [i for i in check_consistency(store) if i["severity"] == "error"]
        if errors:
            return False, f"generated artifacts failed consistency: {errors}"
    return True, "analysis maps to draft product/decision artifacts that pass consistency"


def scenario_task_graph() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = ArtifactStore(root)
        store.init()

        def task(tid: str, title: str, status: str, priority: str, deps: str, acceptance: str) -> None:
            store.write(
                tid,
                "tasks",
                f"## id\n{tid}\n## title\n{title}\n## acceptance\n{acceptance}\n"
                f"## status\n{status}\n## priority\n{priority}\n## depends_on\n{deps}\n",
                status="accepted",
            )

        task("tasks/auth-01", "contract login", "proposed", "1", "", "login contract tests green")
        task("tasks/auth-02", "implement login", "proposed", "2", "tasks/auth-01", "login works end to end")
        task("tasks/auth-03", "acceptance run", "proposed", "3", "tasks/auth-02", "suite green")

        first = next_task(store)
        if first is None or first["task"] != "tasks/auth-01":
            return False, f"expected first task tasks/auth-01, got {first}"
        ready = readiness(store)["tasks/auth-02"]
        if ready["ready"] or ready["missing_deps"] != ["tasks/auth-01"]:
            return False, f"tasks/auth-02 should wait on tasks/auth-01: {ready}"
        if validate_task_graph(store):
            return False, "valid task graph flagged issues"

        def mark(tid: str) -> None:
            store.write(
                tid,
                "tasks",
                f"## id\n{tid}\n## title\ndone\n## acceptance\nok\n## status\ndone\n## priority\n1\n## depends_on\n\n",
                status="accepted",
            )

        mark("tasks/auth-01")
        second = next_task(store)
        if second["task"] != "tasks/auth-02":
            return False, f"after auth-01 done, expected auth-02, got {second}"
        mark("tasks/auth-02")
        third = next_task(store)
        if third["task"] != "tasks/auth-03":
            return False, f"after auth-02 done, expected auth-03, got {third}"
    return True, "dependency readiness and priority-based next-task dispatch work"


def scenario_receipt_loop() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = ArtifactStore(root)
        store.init()
        store.write(
            "tasks/auth-01",
            "tasks",
            "## status\nproposed\n## acceptance\nok\n## priority\n1\n## depends_on\n\n",
            status="accepted",
        )
        store.write("project-state", "project-state", "## stage\nEXECUTION\n", status="accepted")
        out = run_cycle(root, "tasks/auth-01", checks=[{"name": "tests", "ok": True, "output": "green"}])
        if out["verdict"] != "pass" or out["task_status"] != "done" or out["stage"] != "DELIVERY":
            return False, f"pass cycle wrong: {out}"
        if not store.exists("receipts/auth-01"):
            return False, "pass cycle did not write a receipt"
        errors = [i for i in check_consistency(store) if i["severity"] == "error"]
        if errors:
            return False, f"delivery state without receipt flagged: {errors}"

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = ArtifactStore(root)
        store.init()
        store.write("tasks/auth-01", "tasks", "## status\nproposed\n## acceptance\nok\n", status="accepted")
        failing = [{"name": "lint", "ok": False, "output": "error"}]
        retry = run_cycle(root, "tasks/auth-01", checks=failing, retry=1)
        if retry["verdict"] != "fail" or retry["task_status"] != "in_progress":
            return False, f"repairable failure wrong: {retry}"
        blocked = run_cycle(root, "tasks/auth-01", checks=failing, retry=0)
        if blocked["verdict"] != "blocked" or blocked["task_status"] != "blocked":
            return False, f"no-budget failure wrong: {blocked}"
    return True, "pass -> done+receipt, fail repairs, no-budget blocks"


def scenario_experience_loop() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = ArtifactStore(root)
        store.init()
        store.write(
            "receipts/auth-01",
            "receipts",
            "## task\ntasks/auth-01\n## verdict\nblocked\n## error\nlint error\n"
            "## checks\n- lint: fail\n",
            status="accepted",
        )
        cands = collect_experience(store)
        if len(cands) != 1 or cands[0]["frequency"] != 1:
            return False, f"expected one blocked-receipt candidate, got {cands}"
        target = write_experience(store, "auth-01", cands[0])
        artifact = store.get(target)
        if artifact.metadata.kind != "experience" or artifact.metadata.status != "draft":
            return False, "experience candidate is not a draft experience artifact"
        if "[AI-DRAFT]" not in artifact.content:
            return False, "experience candidate is missing the [AI-DRAFT] marker"
        qualifying = shadow_evaluate(store, min_frequency=1)
        if not any(c["slug"] == "auth-01" for c in qualifying):
            return False, "shadow evaluation did not surface the candidate"
        if (root / "red-lines.md").exists() or (root / "docs" / "00-system" / "constitution" / "red-lines.md").exists():
            return False, "shadow evaluation edited an authoritative red-lines.md"
    return True, "blocked receipt becomes a draft [AI-DRAFT] experience candidate, never a red line"


def scenario_mvp_walkthrough() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        report = run_walkthrough(
            Path(tmp),
            "Add an admin dashboard with role-based access for user growth metrics.",
            provider="local-fallback",
        )
        if not report["passed"]:
            return False, f"walkthrough did not pass: {report}"
        if report["consistency_errors"]:
            return False, f"walkthrough left consistency errors: {report['consistency_errors']}"
        if not report["analysis_id"].startswith("analysis/"):
            return False, "walkthrough did not create an analysis artifact"
        if not report["generated"]["product_id"].startswith("product/"):
            return False, "walkthrough did not generate product artifacts"
        if report["receipt"]["verdict"] != "pass" or report["receipt"]["stage"] != "DELIVERY":
            return False, f"walkthrough receipt wrong: {report['receipt']}"
        if report["context_tokens"] > report["ceiling"]:
            return False, "walkthrough exceeded the context ceiling"
        return True, "analysis -> artifacts -> dispatch -> receipt -> reflection completes within budget"


SCENARIOS = {
    "store_lifecycle": scenario_store_lifecycle,
    "compiler_exclusion": scenario_compiler_exclusion,
    "compiler_degradation": scenario_compiler_degradation,
    "compiler_conflict": scenario_compiler_conflict,
    "delta": scenario_delta,
    "analysis_labels": scenario_analysis_labels,
    "analysis_local_fallback": scenario_analysis_local_fallback,
    "analysis_empty_intent": scenario_analysis_empty_intent,
    "analysis_provider_fallback": scenario_analysis_provider_fallback,
    "store_kind_mismatch": scenario_store_kind_mismatch,
    "compiler_missing_ref": scenario_compiler_missing_ref,
    "analysis_similarity_mode": scenario_analysis_similarity_mode,
    "analysis_red_line": scenario_analysis_red_line,
    "analysis_red_line_judge": scenario_analysis_red_line_judge,
    "artifact_consistency": scenario_artifact_consistency,
    "artifact_generate": scenario_artifact_generate,
    "task_graph": scenario_task_graph,
    "receipt_loop": scenario_receipt_loop,
    "experience_loop": scenario_experience_loop,
    "mvp_walkthrough": scenario_mvp_walkthrough,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Behavior harness for the P2 local core")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), help="run a single scenario")
    parser.add_argument("--json", action="store_true", help="emit machine-readable results")
    args = parser.parse_args()

    names = [args.scenario] if args.scenario else list(SCENARIOS)
    results: list[dict] = []
    for name in names:
        try:
            ok, detail = SCENARIOS[name]()
        except Exception as exc:  # noqa: BLE001 - harness reports any scenario failure
            ok, detail = False, f"unexpected exception: {type(exc).__name__}: {exc}"
        results.append({"scenario": name, "ok": ok, "detail": detail})

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            status = "[pass]" if r["ok"] else "[FAIL]"
            print(f"{status} {r['scenario']}: {r['detail']}")

    if not all(r["ok"] for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
