from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import git_safety_gate


class GitSafetyGateTests(unittest.TestCase):
    def repo(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        return tmp, root

    def stage(self, root: Path, name: str, content: bytes):
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        subprocess.run(["git", "add", name], cwd=root, check=True)

    def test_secret_and_cache_are_blocked(self):
        tmp, root = self.repo()
        self.addCleanup(tmp.cleanup)
        token = ("ghp_" + "a" * 40).encode()
        self.stage(root, "config.txt", b"token=" + token + b"\n")
        self.stage(root, "__pycache__/x.pyc", b"\0cache")
        findings = git_safety_gate.scan(root)
        rules = {f["rule"] for f in findings}
        self.assertIn("SEC002", rules)
        self.assertIn("FILE002", rules)

    def test_env_example_is_allowed(self):
        tmp, root = self.repo()
        self.addCleanup(tmp.cleanup)
        self.stage(root, ".env.example", b"API_KEY=replace_me\n")
        self.assertEqual(git_safety_gate.scan(root), [])


if __name__ == "__main__":
    unittest.main()
