"""Project-state detection regressions for Markdown-managed projects."""

from __future__ import annotations

import importlib.util
import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "skills" / "guiyuan-vibecoding" / "scripts" / "bootstrap.py"
SPEC = importlib.util.spec_from_file_location("guiyuan_bootstrap", BOOTSTRAP)
assert SPEC and SPEC.loader
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


class BootstrapDetectionTest(unittest.TestCase):
    def test_markdown_managed_without_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "04-workflow").mkdir(parents=True)
            for name in ("AGENTS.md", "NOW.md", "CHANGELOG.md"):
                (root / name).write_text("managed", encoding="utf-8")
            detected = bootstrap.detect_project_type(root)
            self.assertEqual(detected["type"], "md-managed")
            self.assertEqual(detected["runtime"], "none")

    def test_assessment_keeps_template_choice_user_gated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = bootstrap._assessment(
                root,
                bootstrap.detect_project_type(root),
                intent="想做一个知识库网页，支持语义搜索",
                project_name="knowledge",
            )
            self.assertEqual(data["project_name"], "knowledge")
            self.assertTrue(data["template_recommendations"]["decision_required"])
            self.assertEqual(data["template_recommendations"]["candidate_profile"], "vector-db")
            self.assertTrue(data["template_recommendations"]["candidates"])
            self.assertIn("directory_groups", data["template_recommendations"]["candidates"][0])
            self.assertIn("数据与知识", data["template_recommendations"]["candidates"][0]["directory_groups"])
            self.assertTrue(data["functional_modules"])

    def test_environment_inventory_is_read_only_metadata(self):
        inventory = bootstrap._environment_inventory()
        self.assertTrue(inventory["read_only"])
        self.assertIn("agents", inventory)
        self.assertIn("shared_skill_dirs", inventory)
        self.assertIn("python", inventory)
        self.assertIn("node", inventory)
        self.assertIn("github_cli", inventory)

    def test_human_assessment_hides_internal_match_details(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = bootstrap._assessment(root, bootstrap.detect_project_type(root), intent="一个网页")
            output = io.StringIO()
            with redirect_stdout(output):
                bootstrap._print_assessment(data, as_json=False)
            text = output.getvalue()
            self.assertIn("接管选择", text)
            self.assertNotIn("match:", text)
            self.assertNotIn("risk:", text)

    def test_assessment_reports_size_and_data_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "knowledge").mkdir()
            (root / "knowledge" / "records.jsonl").write_text('{"id": 1}\n', encoding="utf-8")
            data = bootstrap._assessment(root, bootstrap.detect_project_type(root), intent="知识库")
            self.assertEqual(data["project_size"]["level"], "small")
            self.assertEqual(data["data_inventory"]["count"], 1)
            self.assertEqual(data["data_inventory"]["entries"][0]["path"], "knowledge")

    def test_full_takeover_plan_maps_data_and_path_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "knowledge").mkdir()
            (root / "knowledge" / "records.jsonl").write_text('{"id": 1}\n', encoding="utf-8")
            (root / "app.py").write_text('ROOT = "knowledge"\n', encoding="utf-8")
            assessment = bootstrap._assessment(root, bootstrap.detect_project_type(root), intent="知识库")
            spec = bootstrap._load_template_spec("python-service", "medium", ["rag"])
            plan = bootstrap._build_migration_plan(root, assessment, spec)
            self.assertEqual(plan["mappings"][0]["target"], "data/knowledge")
            self.assertEqual(plan["mappings"][0]["references"][0]["file"], "app.py")
            receipt = bootstrap._execute_migration(plan, root)
            self.assertTrue((root / "data" / "knowledge" / "records.jsonl").is_file())
            self.assertIn("data/knowledge", (root / "app.py").read_text(encoding="utf-8"))
            bootstrap._rollback_migration(receipt, root)
            self.assertTrue((root / "knowledge" / "records.jsonl").is_file())
            self.assertIn('"knowledge"', (root / "app.py").read_text(encoding="utf-8"))

    def test_auto_empty_folder_requires_intent(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    bootstrap.sys.executable,
                    str(BOOTSTRAP),
                    tmp,
                    "--name",
                    "demo",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            self.assertIn("请先告诉我，你想做一个什么样的产品", result.stdout)
            self.assertEqual([p.name for p in Path(tmp).iterdir()], [])


if __name__ == "__main__":
    unittest.main()
