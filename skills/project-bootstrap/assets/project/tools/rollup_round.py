#!/usr/bin/env python3
"""迭代档案归档助手：新增一轮迭代时，创建 archive 分卷 + changelog 一行索引。

用法：
  python tools/rollup_round.py --round R27 --date 2026-08-23 --module 文档 ^
      --summary "一句话结论" --detail path/to/detail.md

行为：
  1. 把 --detail 内容写入 docs/04-workflow/archive/{date}-{round}.md（加档案头，已存在则跳过）；
  2. 在 changelog.md 一行台账表顶部（表头分隔线之后）插入一行，链接指向新档案。
"""

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
ARCH = ROOT / "docs" / "04-workflow" / "archive"
CL = ROOT / "docs" / "04-workflow" / "changelog.md"

NOTE = (
    "> 全量迭代记录（changelog 一行台账的档案分卷）。日常不读；考古从 `../changelog.md` 索引进入。\n"
    "> 来源：tools/rollup_round.py 生成。\n"
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True, help="轮次标识，如 R27")
    ap.add_argument("--date", required=True, help="日期，如 2026-08-23")
    ap.add_argument("--module", required=True, help="模块名，如 文档")
    ap.add_argument("--summary", required=True, help="一句话结论")
    ap.add_argument("--detail", required=True, help="本轮完整细节 Markdown 文件路径")
    args = ap.parse_args()

    r = args.round.upper()
    fname = f"{args.date}-{r.lower()}.md"
    out = ARCH / fname
    if out.exists():
        print(f"已存在，跳过写入：{fname}")
    else:
        detail = Path(args.detail).read_text(encoding="utf-8")
        out.write_text(f"# {r} · {args.module}（{args.date}）\n\n{NOTE}\n{detail.rstrip()}\n", encoding="utf-8")
        print(f"档案已写入：{out.relative_to(ROOT)}")

    text = CL.read_text(encoding="utf-8")
    row = f"| {r} | {args.date[5:]} | {args.module} | {args.summary} | [{r.lower()}](archive/{fname}) |"
    sep = "| --- | --- | --- | --- | --- |"
    if sep in text:
        text = text.replace(sep, sep + "\n" + row, 1)
    else:
        text += f"\n| 轮次 | 日期 | 模块 | 一句话结论 | 档案 |\n{sep}\n{row}\n"
    CL.write_text(text, encoding="utf-8")
    print(f"changelog 已插入一行：{row}")


if __name__ == "__main__":
    main()
