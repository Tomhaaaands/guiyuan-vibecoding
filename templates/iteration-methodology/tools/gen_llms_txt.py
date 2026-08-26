#!/usr/bin/env python3
"""生成根目录 llms.txt：docs 的机器可读索引（供 LLM 工具/爬虫定位文档）。

用法：
  python tools/gen_llms_txt.py [--name "项目名"]

规则：
  - 跳过 archive/ 与 _archive/（考古卷不进索引）；
  - 每个 .md 用首个 `# ` 标题作为一行描述；
  - 按 00-system / 01-product / 02-technical / 03-reference / 04-workflow 分组；
  - 标题默认取 README 首个 H1，可用 --name 覆盖；
  - 文档结构变化后重新生成。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
DOCS = ROOT / "docs"
LLMS = ROOT / "llms.txt"
SKIP_PARTS = {"archive", "_archive"}
GROUPS = ["00-system", "01-product", "02-technical", "03-reference", "04-workflow"]
HEADING_RE = re.compile(r"^#\s+(.+)$", re.M)


def _desc(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""
    m = HEADING_RE.search(text)
    return m.group(1).strip() if m else ""


def main() -> None:
    ap = argparse.ArgumentParser(description="生成 llms.txt")
    ap.add_argument("--name", default=None, help="索引标题（默认取 README 首个 H1）")
    args = ap.parse_args()

    files = sorted(
        (p for p in DOCS.rglob("*.md") if not any(part in SKIP_PARTS for part in p.parts)),
        key=lambda p: p.as_posix(),
    )
    title = args.name
    if not title:
        m = HEADING_RE.search((ROOT / "README.md").read_text(encoding="utf-8"))
        title = m.group(1).strip() if m else ROOT.name
    lines = [
        f"# {title}",
        "",
        "> 文档机器索引（由 tools/gen_llms_txt.py 生成，文档结构变化后重新生成）。",
        "",
        "## 项目入口",
        "",
        "- [README.md](README.md): 项目根说明",
        "- [AGENTS.md](AGENTS.md): Agent 启动契约 + 模块路由表",
        "- [NOW.md](docs/04-workflow/NOW.md): 当前焦点/阻塞/下一步",
        "- [changelog.md](docs/04-workflow/changelog.md): 迭代一行台账",
        "",
    ]
    for group in GROUPS:
        group_files = [p for p in files if p.parts[1] == group]
        if not group_files:
            continue
        lines.append(f"## {group}")
        lines.append("")
        for p in group_files:
            rel = p.relative_to(ROOT).as_posix()
            desc = _desc(p)
            lines.append(f"- [{p.name}]({rel}): {desc}" if desc else f"- [{p.name}]({rel})")
        lines.append("")
    LLMS.write_text("\n".join(lines), encoding="utf-8")
    print(f"llms.txt 已生成：{LLMS.relative_to(ROOT)}（{len(files)} 个文档入索引）")


if __name__ == "__main__":
    main()
