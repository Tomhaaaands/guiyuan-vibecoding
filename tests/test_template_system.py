"""Tests for composable topology templates and manifest path resolution."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from tools.project_manifest import artifact_path, load_manifest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "skills" / "guiyuan-vibecoding" / "scripts" / "bootstrap.py"
SPEC = importlib.util.spec_from_file_location("guiyuan_bootstrap_templates", BOOTSTRAP)
assert SPEC and SPEC.loader
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


class TemplateSystemTest(unittest.TestCase):
    def test_all_topologies_materialize_and_record_manifest(self):
        for template in ("python-service", "web-app", "monorepo", "cli"):
            with self.subTest(template=template), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                spec = bootstrap._load_template_spec(template, "small", [])
                created = bootstrap._apply_template_layout(root, spec)
                manifest = load_manifest(root)
                self.assertEqual(manifest["template_id"], template)
                self.assertIn(".guiyuan-vibecoding/project-manifest.toml", created)
                for directory in spec["dirs"]:
                    self.assertTrue((root / directory / ".gitkeep").is_file())

    def test_overlay_composes_dirs_docs_and_red_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = bootstrap._load_template_spec("composite", "large", ["rag", "worker"])
            bootstrap._apply_template_layout(root, spec)
            merged = spec["profile"]
            bootstrap._apply_profile(root, merged)
            self.assertTrue((root / "data" / "knowledge" / ".gitkeep").is_file())
            self.assertTrue((root / "workers" / ".gitkeep").is_file())
            self.assertTrue((root / "docs" / "02-technical" / "rag" / "technical-spec.md").is_file())

    def test_manifest_path_overrides_legacy_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / ".guiyuan-vibecoding"
            state.mkdir()
            (state / "project-manifest.toml").write_text(
                '[artifacts]\nproject_state = "state/current.md"\n', encoding="utf-8"
            )
            (root / "state").mkdir()
            (root / "state" / "current.md").write_text("state", encoding="utf-8")
            self.assertEqual(artifact_path(root, "project_state"), root / "state" / "current.md")


if __name__ == "__main__":
    unittest.main()

