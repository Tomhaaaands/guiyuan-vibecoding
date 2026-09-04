"""Tests for the project-scoped Codex SessionStart hook and its installer."""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

import install_project_hook
import vcm_session_hook


def _touch(root: Path, rel: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("", encoding="utf-8")
    return p


class HookDetectTest(unittest.TestCase):
    def test_empty_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state, signals = vcm_session_hook._detect(root)
            self.assertEqual(state, "ambiguous")
            self.assertEqual(signals, [])

    def test_notes_only_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root, "ideas.md")
            state, _ = vcm_session_hook._detect(root)
            self.assertEqual(state, "ambiguous")

    def test_coding_marker_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root, "pyproject.toml")
            state, signals = vcm_session_hook._detect(root)
            self.assertEqual(state, "coding")
            self.assertIn("pyproject.toml", signals)

    def test_coding_source_count_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(4):
                _touch(root, f"a{i}.py")
            state, signals = vcm_session_hook._detect(root)
            self.assertEqual(state, "coding")
            self.assertTrue(any("source" in s for s in signals))

    def test_vcm_shape_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root, "AGENTS.md")
            _touch(root, "NOW.md")
            _touch(root, "CHANGELOG.md")
            _touch(root, "docs/04-workflow/foo.md")
            state, _ = vcm_session_hook._detect(root)
            self.assertEqual(state, "vcm-shaped")

    def test_managed_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".guiyuan-vibecoding").mkdir()
            state, _ = vcm_session_hook._detect(root)
            self.assertEqual(state, "managed")


class HookAdvisoryTest(unittest.TestCase):
    def test_advisory_not_empty_and_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = vcm_session_hook.build_advisory(root)
            self.assertIn("guiyuan-vibecoding", text)
            self.assertIn("意图", text)  # ambiguous intent gate

    def test_emit_returns_hook_specific_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = vcm_session_hook.emit(root, {})
            self.assertEqual(rc, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
            self.assertTrue(payload["hookSpecificOutput"]["additionalContext"])

    def test_full_check_not_run_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = os.environ.pop("VCM_HOOK_CHECK", None)
            try:
                text = vcm_session_hook.build_advisory(root)
                self.assertNotIn("checks:", text)
            finally:
                if old is not None:
                    os.environ["VCM_HOOK_CHECK"] = old

    def test_full_check_runs_when_opted_in_without_breakage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root, "tools/selfqa.py")
            old = os.environ.get("VCM_HOOK_CHECK")
            os.environ["VCM_HOOK_CHECK"] = "1"
            try:
                text = vcm_session_hook.build_advisory(root)
                self.assertIn("checks:", text)
            finally:
                if old is None:
                    os.environ.pop("VCM_HOOK_CHECK", None)
                else:
                    os.environ["VCM_HOOK_CHECK"] = old


class HookInstallerTest(unittest.TestCase):
    def test_install_writes_hooks_json_idempotent(self):
        runner_src = vcm_session_hook.__file__
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            (root / "tools" / "vcm_session_hook.py").write_text(
                Path(runner_src).read_text(encoding="utf-8"), encoding="utf-8")
            status, path = install_project_hook.install(root)
            self.assertEqual(status, "ok")
            self.assertTrue(path.is_file())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("SessionStart", data["hooks"])
            self.assertIn("vcm_session_hook.py", path.read_text(encoding="utf-8"))
            status2, _ = install_project_hook.install(root)
            self.assertEqual(status2, "unchanged")

    def test_install_missing_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status, _ = install_project_hook.install(root)
            self.assertEqual(status, "missing-runner")


if __name__ == "__main__":
    unittest.main()
