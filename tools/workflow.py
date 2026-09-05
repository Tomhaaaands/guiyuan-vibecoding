"""Compatibility CLI for the VCM workflow router."""
try:
    from tools._compat import expose, run_main
except ModuleNotFoundError:
    from _compat import expose, run_main
expose("tools.vcm_workflow.orchestrator", globals())
if __name__ == "__main__": run_main(_main)
