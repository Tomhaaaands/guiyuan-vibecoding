"""Legacy compatibility entry point."""
try:
    from tools._compat import expose, run_main
except ModuleNotFoundError:
    from _compat import expose, run_main
expose("tools.vcm_workflow.rollup_round", globals())

def main(*args, **kwargs):
    """Forward CLI while honoring legacy patches of path constants."""
    for name in ("ROOT", "ARCH", "CL"):
        if name in globals():
            setattr(_implementation, name, globals()[name])
    return _implementation.main(*args, **kwargs)

if __name__ == "__main__": run_main(_main)
