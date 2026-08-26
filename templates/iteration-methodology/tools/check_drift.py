#!/usr/bin/env python3
"""防文档腐烂：扫描过期标记 + 校验 llms.txt 链接。

用法：
  python tools/check_drift.py            # 全量扫描（过期标记 + llms.txt 链接）
  python tools/check_drift.py --markers  # 只扫过期标记
  python tools/check_drift.py --links    # 只校验 llms.txt 链接

过期标记分级：
  - 硬标记（失败）：`[OUTDATED]`、TODO、TBD、FIXME；
  - 软标记（警告，不失败）：待补 / 待补充（常为刻意占位语义，人工判断）。
教学类文件（讲解这些标记本身规则的文件）默认跳过，避免误报。
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
SKIP_FILES = {
    "docs/04-workflow/review-checklist.md",
    "docs/04-workflow/product-update-protocol.md",
    "docs/04-workflow/iteration-methodology.md",
    "docs/04-workflow/AGENTS_WORKFLOW.md",
    "docs/iteration-methodology.md",
}
STALE_RE = re.compile(r"\[OUTDATED\]|\bTODO\b|\bTBD\b|\bFIXME\b")
SOFT_RE = re.compile(r"待补(?:充)?")
LINK_RE = re.compile(r"\]\(([^)#]+?)\)")


def _files():
    return [p for p in DOCS.rglob("*.md") if not any(part in SKIP_PARTS for part in p.parts)]


def check_markers() -> tuple[int, int]:
    hard = 0
    soft = 0
    for p in _files():
        rel = p.relative_to(ROOT).as_posix()
        if rel in SKIP_FILES:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if STALE_RE.search(line):
                print(f"  [marker] {rel}:{i}: {line.strip()[:100]}")
                hard += 1
            elif SOFT_RE.search(line):
                print(f"  [warn] {rel}:{i}: {line.strip()[:100]}")
                soft += 1
    return hard, soft


def check_links() -> int:
    if not LLMS.exists():
        print("  [info] 无 llms.txt，跳过链接校验（可运行 tools/gen_llms_txt.py 生成）")
        return 0
    found = 0
    for i, line in enumerate(LLMS.read_text(encoding="utf-8").splitlines(), 1):
        for target in LINK_RE.findall(line):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = (ROOT / target).resolve()
            if not path.exists():
                print(f"  [link] llms.txt:{i}: 链接不存在 -> {target}")
                found += 1
    return found


def main() -> None:
    ap = argparse.ArgumentParser(description="扫描文档过期标记与 llms.txt 链接有效性")
    ap.add_argument("--markers", action="store_true", help="只扫过期标记")
    ap.add_argument("--links", action="store_true", help="只校验 llms.txt 链接")
    args = ap.parse_args()

    do_markers = args.markers or not args.links
    do_links = args.links or not args.markers
    total = 0
    if do_markers:
        print("== 过期标记扫描 ==")
        hard, soft = check_markers()
        total += hard
        print(f"  硬标记 {hard} 处 / 软标记 {soft} 处（软标记仅提示，不阻断）")
    if do_links:
        print("== llms.txt 链接校验 ==")
        total += check_links()
    if total:
        print(f"\n发现 {total} 处问题，请清理后重跑。")
        sys.exit(1)
    print("\n文档漂移检查通过 ✓")


if __name__ == "__main__":
    main()
