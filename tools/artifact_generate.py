"""Legacy compatibility entry point."""
try:
    from tools._compat import expose, run_main
except ModuleNotFoundError:
    from _compat import expose, run_main
expose("tools.vcm_requirement.artifact_generate", globals())
if __name__ == "__main__": run_main(_main)
