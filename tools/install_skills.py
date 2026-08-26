#!/usr/bin/env python3
"""安装本仓库的 skills 到 Codex 技能目录。

用法：
  python tools/install_skills.py [--force]

行为：
  把 skills/iteration-close-loop 与 skills/project-bootstrap 复制到
  $CODEX_HOME/skills（默认 ~/.codex/skills）；已存在时跳过，--force 覆盖。
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
SKILLS = ("iteration-close-loop", "project-bootstrap")


def main() -> None:
    ap = argparse.ArgumentParser(description="安装 skills 到 Codex 技能目录")
    ap.add_argument("--force", action="store_true", help="覆盖已存在技能")
    args = ap.parse_args()

    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    dest_root = home / "skills"
    dest_root.mkdir(parents=True, exist_ok=True)

    for name in SKILLS:
        src = ROOT / "skills" / name
        dst = dest_root / name
        if dst.exists() and not args.force:
            print(f"已存在，跳过：{name}（--force 覆盖）")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"已安装：{dst}")
    print(f"完成。新项目第一条对话输入 $project-bootstrap 即可开始。")


if __name__ == "__main__":
    main()
