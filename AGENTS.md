# _bootstrap Agent 规范（强制 · 启动契约 + 索引）

> 优先级最高。本文件只放必读顺序、路由表、纪律、约束与索引；方法论见
> [docs/iteration-methodology.md](docs/iteration-methodology.md)，进度见 [CHANGELOG.md](CHANGELOG.md)。

## 0. 任务开始前（必读，按序）

1. 读 [README.md](README.md)（项目定位与快速开始）；
2. 读 [CHANGELOG.md](CHANGELOG.md) 最近 1-3 行（一行台账）；
3. 涉及方法论/流程改动 → 读 [docs/iteration-methodology.md](docs/iteration-methodology.md)；
4. 涉及 skill 改动 → 按 §1 路由表读对应 SKILL.md。

## 1. 模块路由表（关键词 → 文档 → 代码）

| 任务关键词 | 必读文档 | 代码目录 |
| --- | --- | --- |
| 引导部署 / bootstrap / 一键部署 | [skills/project-bootstrap/SKILL.md](skills/project-bootstrap/SKILL.md) | `skills/project-bootstrap/` |
| 迭代闭环 / 台账 / 档案 / 收尾 | [skills/iteration-close-loop/SKILL.md](skills/iteration-close-loop/SKILL.md) | `skills/iteration-close-loop/` |
| 模板骨架 / 新项目结构 | `templates/iteration-methodology/README.md` | `templates/iteration-methodology/` |
| 工具 / 门禁 / 检索 / 索引 | `tools/*.py`（各自 docstring） | `tools/` |
| 方法论 / 原则 / 迁移指南 | [docs/iteration-methodology.md](docs/iteration-methodology.md) | `docs/` |

## 2. 文档纪律（不可违反）

- **同轮闭环**：每次改动同轮完成 CHANGELOG 一行 + 受影响文档增量同步；
- **同步约束**：`templates/iteration-methodology/` 与
  `skills/project-bootstrap/assets/project/` 必须保持一致（模板演进两边同改）；
- 禁止整篇重写无关文档、禁止遗留「待补/未同步」过期标记对应本次改动；
- 工具脚本改动必须实测（临时目录跑一遍），提交前 `python tools/check_drift.py` 通过。

## 3. 技术约束速记

- 纯 Python 3.10+，无第三方依赖（标准库即可）；UTF-8；
- 路径一律相对仓库根定位（沿父目录找 README.md）；禁止硬编码绝对路径；
- 文档索引变更后重新生成 `llms.txt`：`python tools/gen_llms_txt.py --name "_bootstrap"`。

## 4. 索引指针

| 想知道 | 去哪读 |
| --- | --- |
| 快速开始 / 使用方式 | [README.md](README.md) |
| 完整方法论 | [docs/iteration-methodology.md](docs/iteration-methodology.md) |
| 迭代进度 | [CHANGELOG.md](CHANGELOG.md) |
| 文档机器索引 | [llms.txt](llms.txt) |
