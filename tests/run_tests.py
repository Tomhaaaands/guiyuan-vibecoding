"""Entry point for `python -m trace --module tests.run_tests` coverage runs."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import tests  # ensure sys.path injection runs first

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(REPO_ROOT / "tests"), top_level_dir=str(REPO_ROOT))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
