# 迭代管理系统方法论（Iteration Methodology）

> 状态：✅ 生效（2026-08-27，v2.1 随 R101 沉淀）
> 定位：本文件是一套可复用的「AI 主导开发迭代管理系统」方法论。Creator OS 是它的参考实现；
> 迁移到其他项目时按第 11 节最小集裁剪，不依赖本仓库结构。

## 1. 定位与设计目标

这套方法论服务两个目的：

1. **改动可溯源**：每一次技术迭代/改动都有文档记录，能回答「这行代码为什么这样写」；
2. **随时有最新文档**：任何时刻都能从文档看到项目进行到哪一步、当前是什么状态。

适用范围：单人/小团队、AI Agent 主导的开发；通过「一行台账 + 状态卡 + 档案」也可支撑多 Agent 并行
（各自在台账登记轮次，互不从属、通过 changelog 同步）。

## 2. 核心原则（七条，不可违反）

1. **单一事实源**：每类事实只有一个权威载体（接口→api.md；路由→01-routes-pages；进度→changelog + iteration.md；红线→red-lines.md）。
2. **分层读写**：日常只读台账 1-3 行；改代码前读模块状态卡；考古才进档案分卷。
3. **同轮闭环**：代码、受影响文档、台账必须在同一轮内一起落地，禁止「事后补文档」。
4. **契约先行**：接口/路由先落文档再写实现，防止口头约定漂移。
5. **门禁前置**：能用确定性脚本/静态检查的规则，不写成「LLM 必须记住的规则」（可调试、免费、不占 token）。
6. **红线沉淀**：事故复盘结论升级为不可回退的红线，常驻可见，不归档。
7. **渐进披露**：每轮必读内容压到最小（启动契约 + 当前焦点），其余一律按需检索/按触发加载。

## 3. 五层文档体系

| 层 | 职责 | 内容 |
| --- | --- | --- |
| 00-system | 全局事实 | 架构、数据层、红线、设计系统、版本 |
| 01-product | 产品真相 | 各模块 PRD，含「现状/阶段」小节（唯一产品进度事实） |
| 02-technical | 技术真相 | 模块 iteration.md 状态卡、api.md 契约、管道/爬虫/前端文档 |
| 03-reference | 参考资料 | 教程、环境、模板 |
| 04-workflow | 流程引擎 | 总流程、台账、档案、NOW、路线图、自检、方法论文档 |

分层原则：产品与技术分离；流水与状态分离；索引与全文分离。

## 4. 全局声明层

### 4.1 启动契约（AGENTS.md）

AGENTS.md 是每次对话必读的**启动契约**，只放四类内容：

1. 必读顺序（任务开始前按序读什么）；
2. 模块路由表（关键词 → 必读文档 → 代码目录）；
3. 文档纪律与硬约束（同轮闭环、反向同步、红线、路径、门禁）；
4. 索引指针（流程细节在哪、方法论在哪、当前焦点在哪）。

规则：AGENTS.md 保持索引级瘦身（目标 ≤80 行）；详细流程不进 AGENTS.md，进 04-workflow 按需读取。

### 4.2 红线清单

红线 = 事故沉淀的不可回退约束。规则：

- 一旦写入不可绕过；新增红线必须写入 `red-lines.md`；
- 红线、坑位、关键决策**不归档**，常驻模块状态卡与红线清单，每轮可见；
- 涉及采集/爬虫/跨用户数据等高风险面，改前必查红线。

## 5. 双工作流

### Workflow 1：后端业务落地

PRD → **契约先行**（api.md）→ 数据（data-layer / database.md）→ 实现 → 自检（review-checklist）→ changelog。

每个端点三件套（强制）：

1. 契约条目：路径/方法/入参/返回/错误码；
2. 鉴权与计费口径：user_id 来源（token 解析，禁止信任前端传入）、扣减点、ref_id 幂等；
3. 测试：至少覆盖 happy path + 401/402。

### Workflow 2：前端设计协同

PRD → 路由（01-routes-pages）→ Figma → 设计系统 → 代码 → 同轮登记 api.md。

规则：**手动触发**（用户点名才跑图面往返）；Figma 锚点（fileKey/node id/variables id）必须登记，
缺失锚点禁止声称「已同步」；token/组件定义一次性冻结后只允许从 Figma 发起变更。

## 6. 迭代记录三层模型 + 当前焦点卡

这是整套系统的核心设计，解决「记录成本 vs 可追溯性」的矛盾：

| 层 | 载体 | 粒度 | 何时读/写 |
| --- | --- | --- | --- |
| 一行台账 | changelog.md | 每轮一行：轮次/日期/模块/一句话结论/档案链接 | 每轮开始读 1-3 行；每轮结束顶部加一行 |
| 当前焦点 | NOW.md | ≤20 行：焦点/阻塞/下一步 + 台账指针 | 每轮开始读；每轮结束更新 |
| 状态卡 | 各模块 iteration.md | 只留最新事实/待办/坑位，不重复流水 | 改代码前必读；改动后滚动追加 |
| 全量档案 | archive/YYYY-MM-DD-rNN.md | 根因/实现要点/验证证据 | 考古才读；每轮闭环写入 |

### 6.1 台账行格式

`| R101 | 08-27 | 模块 | 一句话结论（含根因/实证/验证） | [r101](archive/...) |`

一句话结论要求：能独立回答「这轮干了什么、为什么、怎么验证」，不写流水账。

### 6.2 轮次规则

- 编号按天递增，冲突统一重编（不保留重复编号）；
- 档案文件命名 `YYYY-MM-DD-rNN.md`；未编号历史段按日期；
- 红线/坑位/关键决策不归档；
- 归档可用 `tools/rollup_round.py` 一键生成档案 + 插入台账。

## 7. 目标锁定逻辑

目标锁定解决「上下文漂移」：任何任务开始时，用三层锁定把 Agent 钉在正确目标上。

1. **路由表锁定上下文**：任务关键词 → 必读文档 → 代码目录，按序读取，不凭记忆猜；
2. **契约先行锁定接口**：api.md 是接口唯一权威，前端按 api-contract 消费，禁止等后端口播字段名；
3. **里程碑验收一句话**：roadmap 每个里程碑只留一句验收标准，状态表 ✅/🚧/⏳ 为准；
4. **状态标记锁定文档时效**：`[AI-DRAFT]` AI 起草未确认 / `[CONFIRMED]` 人工确认 / `[OUTDATED]` 禁止长期存在。

## 8. 产出规则

### 8.1 每轮五步闭环（任何代码改动）

1. **台账 + 档案**：changelog 顶部加一行 + archive 写分卷（可用 rollup_round.py）；
2. **增量更新文档**：按变更映射表只改受影响章节，禁止整篇重写无关内容；
3. **反向同步 PRD**：用户可见行为/字段变化 → 同轮更新 01-product 对应「现状/阶段」；
4. **红线检查**：涉及红线确认未被绕过，新增红线必须写入；
5. **收尾自检**：NOW.md 更新 + 自检清单过 + 结构校验过，不遗留「待补/未同步」过期标记。

### 8.2 自检清单（必查）

- changelog 已追加、受影响文档已同轮更新、PRD 已反向同步；
- 无「待补/未同步」过期标记、无旧路径字面量；
- 后端：契约三件套、新表带 user_id、ref_id 幂等、check_structure 通过、后端重启验证；
- 前端：路由/token/组件同步、Figma 锚点登记、tsc/build 通过；
- 采集：红线核对、`/api/ingest/cache-status` 回显 creator。

### 8.3 禁止项

- 禁止只改代码不回头更新文档（技术文档 + PRD）；
- 禁止遗留过期标记对应本次改动；
- 禁止绕过确定性门禁（check_structure、pre-commit）。

## 9. 省 token 设计（渐进披露落地）

核心策略：**每轮必读压到极小，其余按需检索**。

| 层 | 常驻/按需 | 内容 | 量级 |
| --- | --- | --- | --- |
| 常驻 | 每次对话 | AGENTS.md 启动契约 + NOW.md 焦点卡 | ~1-2k tokens |
| 按需 | 任务命中模块 | 路由表指向的 _module.yaml + iteration.md | ~1-2k tokens/模块 |
| 按需 | 动手前 | hydrate 检索相关章节 / 受影响文档章节 | 按需 |
| 触发 | 技能命中 | skill 的 frontmatter 常驻（~几十 token），正文激活才加载 | <5k |
| 外部 | 工具/爬虫 | llms.txt 机器索引（几百 token） | 可选 |

配套工具：`tools/hydrate.py`（关键词检索文档）、`llms.txt`（文档索引）、skill 封装（行为按需加载）。
原则：能按需读取就不全量注入；能写进脚本就不写进提示词；能引用就不复制。

## 10. 工具链（确定性优先）

| 工具 | 职责 | 触发 |
| --- | --- | --- |
| `tools/rollup_round.py` | 生成档案分卷 + 插入台账行 | 每轮闭环 |
| `tools/hydrate.py` | 按关键词检索 docs 相关章节（渐进检索） | 动手前 |
| `tools/check_drift.py` | 扫描过期标记 + 校验 llms.txt 链接 | 定期/收尾 |
| `tools/gen_llms_txt.py` | 生成根目录 llms.txt 文档索引 | 文档结构变化时 |
| `tools/check_structure.py` | 结构约束 R1-R9（pre-commit 强制） | 任何改动后 |
| skill `project-bootstrap` | 新项目一键部署：复制骨架 + 替换占位符 + 写 R1 + 生成索引 + 自动装闭环 skill（可选 `--module` 交互式模块清单填路由表） | **显式触发** `$project-bootstrap`（`allow_implicit_invocation=false`，不参与自动检索） |

## 11. 复用与迁移指南（新项目怎么用）

### 最小集（单人新项目，半天可搭）

1. `AGENTS.md`：启动契约（必读顺序 + 路由表 + 纪律 + 索引）；
2. `docs/04-workflow/changelog.md`：一行台账（轮次/日期/模块/结论/档案链接）；
3. `docs/04-workflow/archive/`：档案分卷（文件名 `YYYY-MM-DD-rNN.md`）；
4. `docs/04-workflow/review-checklist.md`：自检清单；
5. 一句话验收：roadmap 每个里程碑配一句验收标准。

### 标准集（+模板）

复制 `templates/iteration-methodology/`：自动获得 AGENTS.md 索引版、docs 五层骨架、
NOW.md、rollup/hydrate/check_drift/gen_llms_txt 四个脚本；改占位符即可用。

### 完整集（+行为封装）

把方法论装成本地 skill：`iteration-close-loop` 负责轮次收尾；`project-bootstrap`
负责新项目一键部署（复制模板 + 自动安装闭环 skill），任何项目第一条对话触发即用。

### 落地步骤

1. 复制模板 → 2. 填项目名/模块路由表 → 3. 建 changelog 首行（初始化轮）→
4. 跑一次 rollup_round 验证 → 5. 后续每轮按五步闭环执行。

## 12. 设计来源与外部对照（演进依据）

本方法论与 2025-2026 主流 SDD（Spec-Driven Development）生态同源，参考实现包括：

- **github/spec-kit**：constitution + specify/plan/tasks/implement/converge → 对应本系统「启动契约 + 双工作流」；
- **Fission-AI/OpenSpec**：propose/apply/archive 变更隔离 → 对应「五步闭环 + 档案分卷」；
- **obra/superpowers**：skill 按需加载 → 对应「渐进披露 + skill 封装」；
- **context-harness / ai-context**：AGENTS.md 瘦身为索引 + NOW/PLAN 分层 → 对应「启动契约 + NOW.md + hydrate」；
- **gsd-build/get-shit-done**：context rot 防治 → 对应「契约先行 + check-drift」。

本系统差异化优势：**红线/坑位常驻机制**、**三层记录模型（台账/状态卡/档案）**、**确定性门禁（check_structure）**。

## 13. 本系统自身的迭代规则

- 改 AGENTS.md / AGENTS_WORKFLOW / 本方法论文档 → 同轮同步 `templates/iteration-methodology/` 与 `skills/iteration-close-loop/`；
- 改工具脚本 → 同轮同步模板内脚本 + 更新工具链表；
- 每轮结束必更：changelog 一行 + archive 分卷 + NOW.md。
