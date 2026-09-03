"""Tests for the published project self-QA gate (tools/selfqa.py)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
TEMPLATE_SELFQA = REPO_ROOT / "templates" / "iteration-methodology" / "tools" / "selfqa.py"


def _make_project(tmp: Path) -> Path:
    """Build a minimal managed project with the generic tools available."""
    tools_dir = tmp / "tools"
    tools_dir.mkdir(parents=True)
    src_tools = REPO_ROOT / "templates" / "iteration-methodology" / "tools"
    for f in ("architecture_audit.py", "check_drift.py", "context_budget.py", "distill.py",
              "gen_llms_txt.py", "hydrate.py", "rollup_round.py", "workflow_optimize.py",
              "selfqa.py", "vcm_session_hook.py"):
        shutil.copy2(src_tools / f, tools_dir / f)
    (tmp / "README.md").write_text("# Test Project\n\nA scaffolded managed project.\n", encoding="utf-8")
    (tmp / "AGENTS.md").write_text(
        "# AGENTS\n\n## startup\nkeep minimal\n", encoding="utf-8"
    )
    (tmp / "NOW.md").write_text("# NOW\nfocus: test\n", encoding="utf-8")
    (tmp / "red-lines.md").write_text("# Red lines\nnever expose secrets\n", encoding="utf-8")
    for layer in ("00-system", "01-product", "02-technical", "03-reference", "04-workflow"):
        layer_dir = tmp / "docs" / layer
        layer_dir.mkdir(parents=True)
        (layer_dir / ".gitkeep").write_text("", encoding="utf-8")
    return tmp


def _run(project: Path, *extra: str) -> subprocess.CompletedProcess:
    # Run the copy installed into the project, not the source path, so ROOT resolves to
    # the project's own AGENTS.md (matching real post-install behavior).
    installed_selfqa = project / "tools" / "selfqa.py"
    return subprocess.run(
        [PY, str(installed_selfqa), *extra],
        cwd=project, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


class SelfQaTest(unittest.TestCase):
    def test_module_is_importable(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("selfqa", TEMPLATE_SELFQA)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertTrue(hasattr(mod, "run"))

    def test_clean_project_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _make_project(Path(tmp))
            r = _run(project)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("passed", r.stdout)

    def test_json_emits_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _make_project(Path(tmp))
            r = _run(project, "--json")
            self.assertEqual(r.returncode, 0)
            payload = json.loads(r.stdout)
            self.assertTrue(payload["passed"])

    def test_fail_on_missing_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _make_project(Path(tmp))
            (project / "tools" / "check_drift.py").unlink()
            r = _run(project, "--json")
            self.assertEqual(r.returncode, 1)
            payload = json.loads(r.stdout)
            self.assertFalse(payload["passed"])

    def test_warn_on_missing_red_lines_is_nonblocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = _make_project(Path(tmp))
            (project / "red-lines.md").unlink()
            r = _run(project, "--json")
            self.assertEqual(r.returncode, 0)
            payload = json.loads(r.stdout)
            checks = {c["check"]: c for c in payload["checks"]}
            self.assertEqual(checks["red-lines"]["status"], "warn")


if __name__ == "__main__":
    unittest.main()
