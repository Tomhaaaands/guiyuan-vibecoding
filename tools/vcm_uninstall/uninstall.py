"""Dedicated uninstall route; ownership logic remains shared with the installer."""

from __future__ import annotations

from pathlib import Path


def uninstall(skills_root: Path) -> int:
    """Run the manifest-owned uninstall implementation without a second confirmation."""
    from tools.vcm_install.install_skills import uninstall as _uninstall

    return _uninstall(skills_root)


def main() -> int:
    import argparse
    from tools.vcm_install.install_skills import resolve_skills_root

    parser = argparse.ArgumentParser(description="Safely remove Guiyuan-owned Skill content")
    parser.add_argument("--skills-dir", default=None)
    args = parser.parse_args()
    return uninstall(resolve_skills_root(args.skills_dir))


if __name__ == "__main__":
    raise SystemExit(main())
