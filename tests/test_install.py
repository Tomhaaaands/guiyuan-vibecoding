"""Tests for transactional install (backup -> swap -> validate -> rollback)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import install_skills


class _FakeOrMissing:
    pass


class InstallSkillsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = Path(self.tmp.name)
        self.src = Path(self.tmp.name) / "skills_src"

    def _make_source(self):
        (self.src / "a").mkdir(parents=True, exist_ok=True)
        (self.src / "b").mkdir(parents=True, exist_ok=True)
        (self.src / "a" / "SKILL.md").write_text("skill a", encoding="utf-8")
        (self.src / "b" / "SKILL.md").write_text("skill b", encoding="utf-8")

    def test_fresh_install(self):
        self._make_source()
        names = ("a", "b")
        with mock.patch.object(install_skills, "_validate_installed", return_value=[]):
            args, rc = install_skills._install_transactional(self.dest, self.src, names, False)
        self.assertEqual(rc, 0)
        self.assertTrue((self.dest / "a" / "SKILL.md").is_file())
        self.assertTrue((self.dest / "b" / "SKILL.md").is_file())

    def test_skip_when_present_without_force(self):
        self._make_source()
        names = ("a", "b")
        with mock.patch.object(install_skills, "_validate_installed", return_value=[]):
            install_skills._install_transactional(self.dest, self.src, names, False)
            (self.dest / "a" / "SKILL.md").write_text("modified", encoding="utf-8")
            args, rc = install_skills._install_transactional(self.dest, self.src, names, False)
        self.assertEqual(rc, 0)
        self.assertEqual((self.dest / "a" / "SKILL.md").read_text(encoding="utf-8"), "modified")

    def test_overwrite_creates_backup(self):
        self._make_source()
        names = ("a", "b")
        with mock.patch.object(install_skills, "_validate_installed", return_value=[]):
            install_skills._install_transactional(self.dest, self.src, names, False)
            (self.dest / "a" / "SKILL.md").write_text("old", encoding="utf-8")
            args, rc = install_skills._install_transactional(self.dest, self.src, names, True)
        self.assertEqual(rc, 0)
        self.assertTrue(args["backed_up"])
        backups = list((self.dest / ".guiyuan-vibecoding-backups").glob("*/a/SKILL.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "old")
        self.assertEqual((self.dest / "a" / "SKILL.md").read_text(encoding="utf-8"), "skill a")

    def test_rollback_on_validation_failure(self):
        self._make_source()
        names = ("a", "b")
        with mock.patch.object(install_skills, "_validate_installed", return_value=[]):
            install_skills._install_transactional(self.dest, self.src, names, False)
            (self.dest / "a" / "SKILL.md").write_text("old", encoding="utf-8")
        # Validation now fails: existing 'a' restored, newly installed 'b' removed.
        with mock.patch.object(install_skills, "_validate_installed",
                               side_effect=lambda root: ["a: broken"] if (root / "a").exists() else ["a: broken"]):
            args, rc = install_skills._install_transactional(self.dest, self.src, names, True)
        self.assertEqual(rc, 1)
        self.assertEqual((self.dest / "a" / "SKILL.md").read_text(encoding="utf-8"), "old")
        # 'b' existed before the forced overwrite, so it is restored from its backup.
        self.assertEqual((self.dest / "b" / "SKILL.md").read_text(encoding="utf-8"), "skill b")

    def test_missing_source_returns_rc1(self):
        names = ("nope",)
        with mock.patch.object(install_skills, "_validate_installed", return_value=[]):
            args, rc = install_skills._install_transactional(self.dest, Path(self.tmp.name) / "fake", names, False)
        self.assertEqual(rc, 1)


class InstallFinishTest(unittest.TestCase):
    def test_finish_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(install_skills, "_validate_installed", return_value=[]):
                self.assertEqual(install_skills._install_finish(Path(tmp), False), 0)

    def test_finish_fails_on_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(install_skills, "_validate_installed", return_value=["x: broken"]):
                self.assertEqual(install_skills._install_finish(Path(tmp), False), 1)


class InstallLifecycleTest(unittest.TestCase):
    def _skill(self, root: Path, name: str, body: str = "content") -> Path:
        path = root / name
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(f"---\nname: {name}\n---\n{body}\n", encoding="utf-8")
        return path

    def test_preflight_is_read_only_and_lists_similar_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._skill(root, "guiyuan-vibecoding")
            self._skill(root, "other-skill")
            before = sorted(p.name for p in root.iterdir())
            self.assertEqual(install_skills.preflight(root), 0)
            self.assertEqual(before, sorted(p.name for p in root.iterdir()))

    def test_uninstall_removes_owned_but_keeps_other_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._skill(root, "guiyuan-vibecoding")
            self._skill(root, "other-skill")
            self.assertEqual(install_skills.uninstall(root), 0)
            self.assertFalse((root / "guiyuan-vibecoding").exists())
            self.assertTrue((root / "other-skill").exists())

    def test_uninstall_preserves_manifest_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._skill(root, "guiyuan-vibecoding")
            (root / install_skills.MANIFEST_NAME).write_text(
                '{"skills":{"guiyuan-vibecoding":{"sha256":"not-the-current-hash"}}}\n', encoding="utf-8"
            )
            (skill / "SKILL.md").write_text("user edit", encoding="utf-8")
            self.assertEqual(install_skills.uninstall(root), 0)
            self.assertTrue(skill.exists())


if __name__ == "__main__":
    unittest.main()
