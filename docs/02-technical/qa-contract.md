---
artifact_id: technical/qa
kind: technical-spec
status: accepted
supports: product/install, product/analysis, product/dispatch, product/delivery
depends_on: technical/artifact-context-contract, technical/packaging/install-contract
---

# QA & Testing Contract

VibeCoding_Manager 把“验证”分成两层，职责与分发边界不同：**内部测试套件**只存在于本仓库，
> 用于研发自身回归；**发布版自检门禁**随项目模板下发到每个被管理项目，用于验证采纳后的
> 项目自身健康。两者都是 stdlib-only、无第三方依赖、可在任意主机直接运行。

## 内部测试套件（repo-only）

入口：`tools/run_qa.py`。单条命令串起单元测试、行为回归和交付门禁，任一阻塞项失败即非零退出。

| 层 | 覆盖 | 运行 |
| --- | --- | --- |
| 单元 | `artifact_store` / `context_compiler` / `context_budget` / `analysis` / `analysis_provider` / `analysis_labels` / `artifact_consistency` / `artifact_generate` / `task_graph` / `receipt_loop` / `experience_loop` / `mvp_walkthrough` | `python -m unittest discover -s tests -t .` |
| 行为 | `behavior_harness.py` 的 P0-P8 场景 | 随 `run_qa.py` 一起跑；也可单跑 `python tools/behavior_harness.py` |
| 交付 | `build_dist --verify` / `check_drift` / `architecture_audit` / `check_package` / `sync_copies --dry-run` / `gen_llms_txt` | 均被 `run_qa.py` 聚合 |
| 安装 | `install_skills.py` 与发布版 `install.py` 的事务化回滚 | `tests/test_install.py` |

CLI 工具（build_dist、check_package、gen_llms_txt、architecture_audit、sync_copies）通过子进程调用
真实 CLI 测试，不重构其内部逻辑；可导入模块（如 `artifact_store`、`context_compiler`）直接调用函数。

在发布版里，随项目模板下发的 `tools/vcm_session_hook.py` 配合 `.codex/hooks.json` 提供
**项目级 SessionStart 提醒**，属于代理层软约束，与 `selfqa.py` 的硬门禁不同；边界与作用域见
[technical/project-hook.md](project-hook.md)。

可选参数：

- `--coverage`：用标准库 `trace` 生成近似行覆盖，写入 `.qa/coverage/`（非阻塞）。
- `--frontend`：对 `assets/frontend/web` 与 `admin` 跑 `npm run build`，无 node/npm 或未安装
  `node_modules` 时跳过并注明（非阻塞）。
- `--skip <gate>`：跳过某阻塞门禁，便于快速隔离焦点。

报告写入 `.qa/qa-report.json`；`.qa/` 已被 `.gitignore` 忽略。

## 发布版自检门禁（随项目模板下发）

入口：`tools/selfqa.py`。它只读取被管理项目自身的文件，不依赖本仓库内部模块，因此能被
`build_dist` 打进发布包并在任何采纳项目里独立运行。

| 检查 | 语义 |
| --- | --- |
| tools | `tools/` 下通用工具齐全 |
| agents | `AGENTS.md` 启动契约存在 |
| docs-skeleton | `docs/00-system..04-workflow` 五层骨架完整 |
| check-drift | 项目内 `check_drift.py` 通过 |
| context-budget | 项目内 `context_budget.py` 未超硬上限 |
| llms-links | `llms.txt` 链接可解析（文件不存在则跳过） |
| markers | 非教学文档无 `[OUTDATED]`/TODO/TBD/FIXME |
| red-lines | 声明的 `red-lines.md` 存在；缺省记 warn，不阻塞 |

用法：`python tools/selfqa.py`（默认人类可读）或 `python tools/selfqa.py --json`。
`fail` 检查会令退出码为 1；`warn` 仅提示，不阻塞。

## 边界

- 内部套件不进入发布 zip；`selfqa.py` 通过 `templates/iteration-methodology/tools/`
  ↔ `skills/vibe-coding-manager/assets/project/tools/` 同步，随技能下发。
- 被管项目不拥有 `behavior_harness`/`build_dist`/`check_package` 等仓库专用门禁；
  它们只对研发闭环有意义，不随分发。
- 前端仅做 build/typecheck 冒烟，不做组件或浏览器 E2E，避免把 node/Puppeteer 引入
  stdlib-only 约束。

## 验收

本轮 QA 完工以 `python tools/run_qa.py` 全绿为基准，并叠加重新生成 `llms.txt`、
`python tools/sync_copies.py` 后 `check_drift` 通过。
