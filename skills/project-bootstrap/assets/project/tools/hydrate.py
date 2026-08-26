#!/usr/bin/env python3
"""渐进检索：按关键词从 docs/ 拉取最相关章节，避免全量注入。

用法：
  python tools/hydrate.py 灵感库 赛道统计
  python tools/hydrate.py "api 契约" --top 5 --lines 3

行为：
  1. 扫描 docs/**/*.md（跳过 archive/ 与 _archive/）；
  2. 按关键词命中数排序，输出前 N 个文件及命中行；
  3. 打印各文件近似 token 量（字符数/4），供上下文预算参考。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
DOCS = ROOT / "docs"
SKIP_PARTS = {"archive", "_archive"}


def _files():
    return [p for p in DOCS.rglob("*.md") if not any(part in SKIP_PARTS for part in p.parts)]


def main() -> None:
    ap = argparse.ArgumentParser(description="按关键词检索 docs 相关章节")
    ap.add_argument("keywords", nargs="+", help="检索关键词（多词按任一命中计）")
    ap.add_argument("--top", type=int, default=8, help="最多输出文件数")
    ap.add_argument("--lines", type=int, default=3, help="每个文件最多输出命中行数")
    args = ap.parse_args()

    pats = [re.compile(re.escape(k), re.IGNORECASE) for k in args.keywords]
    hits: list[tuple[int, Path, list[str]]] = []
    for p in _files():
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lines = text.splitlines()
        matched = [ln.strip() for ln in lines if any(pat.search(ln) for pat in pats)]
        if matched:
            hits.append((len(matched), p, matched[: args.lines]))

    if not hits:
        print(f"未命中任何文档：{args.keywords}")
        return

    hits.sort(key=lambda x: x[0], reverse=True)
    print(f"命中 {len(hits)} 个文件（关键词：{' '.join(args.keywords)}），按相关度排序：\n")
    for count, path, lines in hits[: args.top]:
        rel = path.relative_to(ROOT).as_posix()
        tokens = max(1, len(path.read_text(encoding="utf-8")) // 4)
        print(f"== {rel}  [命中 {count} · ~{tokens} tokens]")
        for ln in lines:
            print(f"   - {ln[:120]}")
        print()


if __name__ == "__main__":
    main()
