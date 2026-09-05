"""Legacy compatibility entry point."""
try:
    from tools._compat import expose, run_main
except ModuleNotFoundError:
    from _compat import expose, run_main
expose("tools.vcm_release.git_safety_gate", globals())
if __name__ == "__main__": run_main(_main)
