"""Tests for delivery/package gates: build_dist, architecture_audit, llms, drift, package."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import architecture_audit as arch
import build_dist
import check_drift
import check_package
from gen_llms_txt import _desc, ROOT as GEN_ROOT
import publish_release
import update_catalog

PY = sys.executable


def _run_cli(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


class BuildDistTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)

    def test_build_writes_zip_checksum_manifest(self):
        zip_path = build_dist.build(self.out, verify=False)
        self.assertTrue(zip_path.is_file())
        sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
        checksum = zip_path.with_suffix(zip_path.suffix + ".sha256").read_text(encoding="utf-8")
        self.assertIn(sha, checksum)
        manifest = json.loads(zip_path.with_suffix(zip_path.suffix + ".manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["sha256"], sha)
        self.assertIn("version", manifest)
        self.assertEqual(manifest["skills"], ["guiyuan-vibecoding"])

    def test_verify_cli_passes(self):
        r = _run_cli([PY, str(GEN_ROOT / "tools" / "build_dist.py"), "--verify", "--out", str(self.out)])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("verify passed", r.stdout)


class PublishReleaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)

    def test_publish_validator_accepts_single_public_skill_asset(self):
        asset = build_dist.build(self.out, verify=False)
        digest = publish_release.validate_installer_asset(
            asset,
            asset.with_suffix(asset.suffix + ".sha256"),
            asset.with_suffix(asset.suffix + ".manifest.json"),
        )
        self.assertEqual(digest, hashlib.sha256(asset.read_bytes()).hexdigest())

    def test_publish_validator_rejects_nested_skill_asset(self):
        asset = self.out / "guiyuan-vibecoding-0.1.1.zip"
        with zipfile.ZipFile(asset, "w") as zf:
            zf.writestr("guiyuan-vibecoding/SKILL.md", "---\nname: guiyuan-vibecoding\n---\n")
            zf.writestr("guiyuan-vibecoding/assets/skills/old/SKILL.md", "old")
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
        checksum = asset.with_suffix(asset.suffix + ".sha256")
        checksum.write_text(f"{digest} *{asset.name}\n", encoding="utf-8")
        manifest = asset.with_suffix(asset.suffix + ".manifest.json")
        manifest.write_text(json.dumps({"skills": ["guiyuan-vibecoding"], "sha256": digest}), encoding="utf-8")
        with self.assertRaises(ValueError):
            publish_release.validate_installer_asset(asset, checksum, manifest)


class UpdateCatalogTest(unittest.TestCase):
    def test_catalog_build_uses_version_and_release_assets(self):
        catalog = update_catalog.build("9.9.9", status="pending")
        self.assertEqual(catalog["current"]["version"], "9.9.9")
        self.assertEqual(catalog["current"]["tag"], "v9.9.9")
        self.assertEqual(catalog["current"]["status"], "pending")
        self.assertTrue(catalog["current"]["assets"]["installer"].endswith("guiyuan-vibecoding-9.9.9.zip"))


class ArchitectureAuditTest(unittest.TestCase):
    def test_clean_tree_zero_conflicts(self):
        r = arch.audit(build_dist.ROOT)
        self.assertEqual(r["authority_conflicts"], [])
        self.assertEqual(r["legacy_directories"], [])
        self.assertTrue(r["read_only"])

    def test_audit_detects_missing_layers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "Apps").mkdir()
            r = arch.audit(root)
            self.assertTrue(any("missing canonical layer" in c["reason"] for c in r["authority_conflicts"]))
            self.assertEqual(r["legacy_directories"], ["Apps/ -> apps/"])


class GenLlmsTest(unittest.TestCase):
    def test_desc_reads_first_h1(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "a.md"
            f.write_text("# My Title\n\nbody\n", encoding="utf-8")
            self.assertEqual(_desc(f), "My Title")

    def test_desc_empty_when_no_h1(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "a.md"
            f.write_text("no heading\n", encoding="utf-8")
            self.assertEqual(_desc(f), "")

    def test_regenerate_llms_cli(self):
        r = _run_cli([PY, str(GEN_ROOT / "tools" / "gen_llms_txt.py")])
        self.assertEqual(r.returncode, 0, r.stderr)


class CheckDriftTest(unittest.TestCase):
    def test_repo_no_hard_markers(self):
        hard, _ = check_drift.check_markers()
        self.assertEqual(hard, 0)

    def test_llms_links_valid(self):
        self.assertEqual(check_drift.check_links(), 0)

    def test_sync_pairs_clean(self):
        self.assertEqual(check_drift.check_sync(), 0)

    def test_version_single_source(self):
        self.assertEqual(check_drift.check_version(), 0)

    def test_context_budget_pass(self):
        self.assertLessEqual(check_drift.check_context_budget(), 0)

    def test_cli_passes(self):
        r = _run_cli([PY, str(GEN_ROOT / "tools" / "check_drift.py")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class CheckPackageTest(unittest.TestCase):
    def test_scan_text_detects_tokens(self):
        fixture = "key=" + "sk-" + "abcdefghijklmnopqrstuvwxyz0123456789"
        hits = check_package.scan_text("x", fixture)
        self.assertGreater(hits, 0)

    def test_scan_text_clean(self):
        self.assertEqual(check_package.scan_text("x", "no secrets here"), 0)

    def test_cli_passes_on_repo(self):
        r = _run_cli([PY, str(GEN_ROOT / "tools" / "check_package.py")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class SyncCopiesTest(unittest.TestCase):
    def test_sync_dry_run_is_clean(self):
        r = _run_cli([PY, str(GEN_ROOT / "tools" / "sync_copies.py"), "--dry-run"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
