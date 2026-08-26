# {{PROJECT_NAME}} Agent 规范（强制 · 启动契约 + 索引）

> 优先级最高。本文件只放必读顺序、路由表、纪律、约束与索引；
> 详细流程见 [AGENTS_WORKFLOW](docs/04-workflow/AGENTS_WORKFLOW.md)，方法论见
> [iteration-methodology](docs/04-workflow/iteration-methodology.md)，当前焦点见 [NOW](docs/04-workflow/NOW.md)。

## 0. 任务开始前（必读，按序）

1. 读 [AGENTS_WORKFLOW](docs/04-workflow/AGENTS_WORKFLOW.md)（开发总流程 + 模块路由表）；
2. 读 [changelog](docs/04-workflow/changelog.md) 最近 1-3 行（一行台账）；考古才进 [archive](docs/04-workflow/archive/README.md)；
3. 读 [NOW.md](docs/04-workflow/NOW.md)（当前焦点/阻塞/下一步）；
4. 用户点明模块 → 按 §1 路由表读对应产品/技术文档；
5. 涉及接口 → [api.md](docs/02-technical/api-gateway/api.md) 为唯一权威（存在时）。

## 1. 模块路由表（关键词 → 文档 → 代码）

| 任务关键词 | 必读文档 | 代码目录 |
| --- | --- | --- |
| {{模块A 关键词}} | `docs/01-product/{{模块A}}/` + `docs/02-technical/{{模块A}}/` | {{代码目录}} |
| {{模块B 关键词}} | `docs/01-product/{{模块B}}/` + `docs/02-technical/{{模块B}}/` | {{代码目录}} |

> 按项目裁剪：每行一个业务模块，关键词用用户最常用的说法。

## 2. 文档纪律（不可违反）

- **同轮闭环**：每次改动同轮完成 changelog 一行 + archive 分卷 + 受影响文档增量同步（AGENTS_WORKFLOW §4）；
- **反向同步**：用户可见行为/字段变化同轮更新产品文档对应「现状/阶段」；
- **红线**：不得绕过；新增红线必须写入 `docs/00-system/constitution/red-lines.md`；
- 禁止整篇重写无关文档、禁止遗留「待补/未同步」过期标记对应本次改动。

## 3. 技术约束速记

- 构建/测试命令：{{按项目填写}}；
- 路径/存储/依赖方向等硬约束：{{按项目填写}}；
- 任何改动后必须通过项目结构校验（如 `python tools/check_structure.py`，存在时）。

## 4. 索引指针

| 想知道 | 去哪读 |
| --- | --- |
| 流程细节 / 变更映射 | [AGENTS_WORKFLOW.md](docs/04-workflow/AGENTS_WORKFLOW.md) |
| 方法论 / 复用迁移指南 | [iteration-methodology.md](docs/04-workflow/iteration-methodology.md) |
| 当前焦点 / 阻塞 / 下一步 | [NOW.md](docs/04-workflow/NOW.md) |
| 文档机器索引 | [llms.txt](llms.txt) |
| 迭代闭环执行（skill） | `$iteration-close-loop` |
| 新项目一键部署（skill） | `$project-bootstrap` |
