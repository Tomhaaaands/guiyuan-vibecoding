from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.gitignore_profiles import ensure, rules_for


class GitignoreProfileTests(unittest.TestCase):
    def test_composes_topology_scale_capabilities(self):
        rules = rules_for(topology="web", scale="large", capabilities=["rag", "auth"])
        self.assertIn("node_modules/", rules)
        self.assertIn("embeddings/", rules)
        self.assertIn("*.pem", rules)
        self.assertIn("**/__pycache__/", rules)

    def test_adoption_preserves_existing_rules(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".gitignore"
            p.write_text("custom-local/\n", encoding="utf-8")
            ensure(p, topology="service", capabilities=["vector-db"])
            text = p.read_text(encoding="utf-8")
            self.assertIn("custom-local/", text)
            self.assertIn("__pycache__/", text)
            self.assertIn("*.sqlite3", text)


if __name__ == "__main__":
    unittest.main()
