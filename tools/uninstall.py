"""Compatibility CLI for the dedicated VCM uninstall route."""
try:
    from tools._compat import expose, run_main
except ModuleNotFoundError:
    from _compat import expose, run_main
expose("tools.vcm_uninstall.uninstall", globals())
if __name__ == "__main__": run_main(_main)
