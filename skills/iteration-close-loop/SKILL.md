---
name: iteration-close-loop
description: Close out an iteration round or initialize a changelog + archive + state-card documentation loop, including one-line changelog rows, archive round files, NOW/state card updates, doc sync, and structure/drift checks. Use when recording an iteration, wrapping up a work round, or setting up a minimal doc loop in a new project.
---

# 迭代闭环（Iteration Close-Loop）

确保任何一轮改动以可溯源方式闭环：台账一行、档案分卷、状态卡更新、文档同步、机械门禁。

## 何时使用

- 一轮代码/文档改动收尾：写 changelog、档案、NOW、自检；
- 新项目尚无闭环体系：初始化最小四件套；
- 检查文档与代码是否漂移。

## 最小闭环四件套（新项目初始化）

1. `AGENTS.md`：启动契约 = 必读顺序 + 模块路由表 + 纪律 + 索引指针；
2. `changelog.md`：一行台账，行格式
   `| R101 | 08-27 | 模块 | 一句话结论（干什么/为什么/怎么验证） | [r101](archive/...) |`；
3. `archive/`：档案分卷 `YYYY-MM-DD-rNN.md`，写根因/实现要点/验证证据；
4. `review-checklist.md`：自检清单（必查项）。

## 每轮五步闭环（已有系统时）

1. changelog 顶部加一行 + archive 写分卷（项目有 `tools/rollup_round.py` 则用它生成）；
2. 更新 NOW.md / 模块状态卡：焦点、阻塞、下一步（≤20 行，历史不保留）；
3. 受影响文档增量同步（禁止整篇重写无关章节）；
4. 用户可见变化反向同步产品文档「现状/阶段」；
5. 自检：红线核对 + 结构/漂移检查通过，不遗留「待补/未同步」过期标记。

## 规则

- 一句话结论必须能独立回答：这轮干了什么、为什么、怎么验证；
- 红线、坑位、关键决策不归档：常驻状态卡与红线清单，每轮可见；
- 轮次冲突统一重编；档案命名 `YYYY-MM-DD-rNN.md`；
- 门禁优先：能写成确定性脚本/静态检查的规则，不写成提示词；
- 渐进披露：每轮必读压到最小，其余按需检索（关键词检索而不是全量读文档）。

## 工具（项目存在时使用）

- `tools/rollup_round.py`：生成档案分卷 + 插入台账行；
- `tools/hydrate.py`：按关键词渐进检索 docs 相关章节；
- `tools/check_drift.py`：扫描过期标记 + 校验 llms.txt 链接；
- `tools/gen_llms_txt.py`：生成文档机器索引；
- `tools/check_structure.py`：结构约束 R1-R9（pre-commit 强制）。

## 方法论细节

项目内存在 `docs/04-workflow/iteration-methodology.md` 时按需读取（原则/三层记录/迁移指南）；
不存在则以上文为完整规则，不必另找。
