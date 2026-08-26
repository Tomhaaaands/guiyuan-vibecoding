# AI 操作总览 · 模块路由与开发总流程（AGENTS_WORKFLOW）

> 本文件是开发流程的唯一入口：模块路由表 + 两条 Workflow + 每轮检查清单 + 变更映射。

## 1. 模块路由表（用户点明任务 → Agent 必读，按顺序）

| 任务关键词 | 必读文档 | 代码目录 |
| --- | --- | --- |
| {{模块A}} | `01-product/{{模块A}}/` → `02-technical/{{模块A}}/iteration.md` | {{代码目录}} |
| {{模块B}} | `01-product/{{模块B}}/` → `02-technical/{{模块B}}/iteration.md` | {{代码目录}} |

## 2. 两条 Workflow

- **Workflow 1 后端业务落地**：PRD → 契约（`api.md` 先行）→ 数据 → 实现 → 自检 → changelog；
- **Workflow 2 前端设计协同**：PRD → 路由 → Figma → 设计 → 代码（手动触发）；
- 方法论与复用指南见 [iteration-methodology.md](iteration-methodology.md)。

## 3. 文档地图（谁负责 · 何时更新）

| 文档 | 内容 | 更新时机 |
| --- | --- | --- |
| `changelog.md` | 一行索引台账（强制每轮必写） | 每次改动顶部加一行 |
| `NOW.md` | 当前焦点状态卡（≤20 行） | 每轮结束更新 |
| `archive/` | 全量迭代档案分卷 | 每次改动详情追加对应卷 |
| `roadmap.md` | 里程碑与验收一句话 | 里程碑变化 |
| `iteration-methodology.md` | 可复用方法论 | 方法论演进 |
| 根目录 `llms.txt` | 文档机器索引 | 文档结构变化（`tools/gen_llms_txt.py`） |

> 职责边界：changelog=一行索引；NOW=当前焦点；archive=考古档案；各模块 iteration.md=滚动状态卡；
> 红线/坑位/关键决策不归档。

## 4. 每次改动的标准动作（最小闭环）

1. 写 changelog 一行 + archive 分卷（可用 `tools/rollup_round.py`）；
2. 更新 NOW.md（焦点/阻塞/下一步）；
3. 增量更新对应文档（禁止整篇重写）；
4. 反向同步 PRD「现状/阶段」；
5. 红线检查；
6. 收尾自检：无「待补/未同步」过期标记，结构校验通过。

## 5. 每轮对话开始检查清单

- [ ] 已读本文件
- [ ] 已读 changelog 最近 1-3 行
- [ ] 已读 NOW.md
- [ ] 已读目标模块 iteration.md 卡
- [ ] 涉及接口 → api.md 为最新；涉及红线 → red-lines 为最新

## 6. 变更类型 → 文档映射（速查）

| 变更 | 必更文档 |
| --- | --- |
| 任何代码/文档改动 | changelog（一行）+ archive（详情）+ 模块 iteration.md |
| 新增/改 API | api.md + changelog |
| 迭代系统自身改动 | iteration-methodology.md + templates/ + skill + llms.txt + changelog |
