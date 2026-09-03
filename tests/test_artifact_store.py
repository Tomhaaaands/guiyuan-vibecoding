"""Tests for the typed authority-artifact store."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from artifact_store import (
    ArtifactStore,
    content_hash,
    split_ref,
)


class SplitRefTest(unittest.TestCase):
    def test_no_revision(self):
        self.assertEqual(split_ref("product/auth"), ("product/auth", None))

    def test_with_revision(self):
        self.assertEqual(split_ref("product/auth@7"), ("product/auth", 7))

    def test_revision_in_id_with_slash(self):
        self.assertEqual(split_ref("a/b@12"), ("a/b", 12))


class ContentHashTest(unittest.TestCase):
    def test_is_prefixed(self):
        self.assertTrue(content_hash("hello").startswith("sha256:"))

    def test_is_deterministic(self):
        self.assertEqual(content_hash("hello"), content_hash("hello"))

    def test_differs(self):
        self.assertNotEqual(content_hash("hello"), content_hash("world"))


class StoreLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = ArtifactStore(self.root)

    def _write(self, artifact_id="product/auth", kind="product-spec", content="## acceptance\nok\n", **kw):
        return self.store.write(artifact_id, kind, content, **kw)

    def test_init_creates_dirs(self):
        d = self.store.init()
        self.assertTrue((d / ".meta").is_dir())

    def test_write_then_get_roundtrip(self):
        self.store.init()
        meta = self._write()
        artifact = self.store.get("product/auth")
        self.assertEqual(artifact.metadata.artifact_id, "product/auth")
        self.assertEqual(artifact.metadata.kind, "product-spec")
        self.assertEqual(artifact.metadata.revision, 1)
        self.assertIn("acceptance", artifact.content)
        self.assertEqual(meta.content_hash, artifact.metadata.content_hash)

    def test_idempotent_same_content_no_new_revision(self):
        self.store.init()
        m1 = self._write()
        m2 = self._write()
        self.assertEqual(m1.revision, 1)
        self.assertEqual(m2.revision, 1)
        self.assertEqual(m1.content_hash, m2.content_hash)

    def test_revision_bumps_on_content_change(self):
        self.store.init()
        m1 = self._write(content="## acceptance\nv1\n")
        m2 = self._write(content="## acceptance\nv2 different\n")
        self.assertEqual(m1.revision, 1)
        self.assertEqual(m2.revision, 2)
        self.assertIsNotNone(m2.supersedes)

    def test_depends_on_sorted(self):
        self.store.init()
        meta = self._write(content="## acceptance\nx\n", depends_on=["b", "a"])
        self.assertEqual(meta.depends_on, ["a", "b"])

    def test_invalid_id_rejected(self):
        self.store.init()
        with self.assertRaises(ValueError):
            self.store.write("bad", "product-spec", "x")
        with self.assertRaises(ValueError):
            self.store.write(".hidden", "product-spec", "x")

    def test_kind_must_match_id_prefix(self):
        self.store.init()
        with self.assertRaises(ValueError):
            self.store.write("product/auth", "decisions", "x")

    def test_invalid_kind_rejected(self):
        self.store.init()
        with self.assertRaises(ValueError):
            self.store.write("product/auth", "nope", "x")

    def test_invalid_status_rejected(self):
        self.store.init()
        with self.assertRaises(ValueError):
            self._write(status="bogus")

    def test_empty_content_rejected(self):
        self.store.init()
        with self.assertRaises(ValueError):
            self._write(content="   \n")

    def test_get_missing_raises(self):
        self.store.init()
        with self.assertRaises(KeyError):
            self.store.get("product/missing")

    def test_list(self):
        self.store.init()
        self._write("product/auth", "product-spec", "## acceptance\na\n")
        self._write("decisions/auth", "decisions", "## constraint\nc\n")
        metas = self.store.list()
        self.assertEqual(len(metas), 2)
        self.assertEqual({m.artifact_id for m in metas}, {"product/auth", "decisions/auth"})

    def test_validate_clean(self):
        self.store.init()
        self._write()
        self.assertEqual(self.store.validate(), [])

    def test_validate_detects_hash_mismatch(self):
        self.store.init()
        self._write()
        content_path = self.store.root / "artifacts" / "product" / "auth.md"
        content_path.write_text("tampered", encoding="utf-8")
        errors = self.store.validate()
        self.assertTrue(any("hash mismatch" in e for e in errors))

    def test_validate_detects_missing_dep(self):
        self.store.init()
        self._write(depends_on=["tasks/nope"])
        errors = self.store.validate()
        self.assertTrue(any("missing depends_on" in e for e in errors))

    def test_validate_detects_kind_mismatch_metadata(self):
        self.store.init()
        self._write()
        meta_path = self.store.root / "artifacts" / ".meta" / "product" / "auth.json"
        data = meta_path.read_text(encoding="utf-8").replace("product-spec", "decisions")
        meta_path.write_text(data, encoding="utf-8")
        errors = self.store.validate()
        self.assertTrue(any("implies kind" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
