"""Helpers for preserving the historical ``tools/*.py`` import and CLI paths.

The compatibility modules intentionally expose the implementation module's complete
namespace (including private helpers used by downstream callers and tests).  A few
old modules were libraries without a ``main`` function, so command execution is
conditional instead of making import fail.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import MutableMapping

# Direct ``python tools/foo.py`` execution places ``tools/`` (not the repository
# parent) on sys.path.  Add the parent once so the package-qualified imports used
# by the relocated modules remain valid.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def expose(module_name: str, target_globals: MutableMapping[str, object]) -> ModuleType:
    """Load *module_name* and expose its full namespace in a legacy wrapper."""
    implementation = importlib.import_module(module_name)
    # Do not copy import metadata (``__name__``, ``__file__``, ``__package__``)
    # into the wrapper: it would disable its ``__main__`` guard when invoked as
    # a script and confuse import machinery.  Public and private implementation
    # symbols are intentionally all retained.
    target_globals.update({
        key: value for key, value in vars(implementation).items()
        if not key.startswith("__")
    })
    target_globals["_implementation"] = implementation
    target_globals["_main"] = getattr(implementation, "main", None)
    return implementation


def run_main(main: object) -> None:
    """Run an optional implementation CLI, preserving normal exit semantics."""
    if callable(main):
        raise SystemExit(main())
