# 迭代档案（archive）

> 本目录是 `changelog.md` 一行台账的全量档案分卷：只做考古用，日常不读。

## 规则

- 每个编号轮次一个文件：`YYYY-MM-DD-rNN.md`；
- 每次改动的完整细节（根因 / 实现要点 / 验证证据）写入对应档案卷；changelog 只留一行索引；
- **红线、坑位、关键决策不归档**：常驻各模块 `iteration.md` 与红线清单；
- 新增档案用 `python tools/rollup_round.py --round R27 --date 2026-08-23 --module 文档 --summary "一句话结论" --detail path/to/detail.md`。
