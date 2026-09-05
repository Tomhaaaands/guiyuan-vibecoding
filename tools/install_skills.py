"""Legacy compatibility entry point.

The module is aliased to the implementation object so callers that historically
patched private helpers continue to patch the globals used by the implementation.
"""
import sys
try:
    from tools._compat import expose, run_main
except ModuleNotFoundError:
    from _compat import expose, run_main
_implementation = expose("tools.vcm_install.install_skills", globals())
sys.modules[__name__] = _implementation

# Functions whose implementation resolves collaborators through module globals
# get a tiny forwarding shim.  This keeps historical monkey-patching semantics
# (notably tests patching ``install_skills._validate_installed``) intact while
# the real code lives in ``vcm_install``.
def _install_transactional(*args, **kwargs):
    _implementation._validate_installed = globals().get("_validate_installed", _implementation._validate_installed)
    return _implementation._install_transactional(*args, **kwargs)


def _install_finish(*args, **kwargs):
    _implementation._validate_installed = globals().get("_validate_installed", _implementation._validate_installed)
    return _implementation._install_finish(*args, **kwargs)

if __name__ == "__main__": run_main(_main)
