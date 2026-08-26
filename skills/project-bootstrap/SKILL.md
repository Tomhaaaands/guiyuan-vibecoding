---
name: project-bootstrap
description: Explicit-only skill (implicit auto-selection disabled). Invoke with $project-bootstrap to run guided conversational bootstrap that turns an empty folder into a production-ready single-agent project, asking for folder and project name, offering default business modules or a recommended template, then generating README, AGENTS.md, docs skeleton, tooling, .venv and git, and auto-installing iteration-close-loop when missing.
---

# 项目一键部署（Project Bootstrap · 引导式）

本 skill 是**显式触发**的引导式问答流程（`policy.allow_implicit_invocation=false`，
不参与自动检索，只有用户点名 `$project-bootstrap` 时激活）。激活后，无论用户
第一条消息是什么（hello、粘贴代码、问问题），一律先执行「阶段 0」开场白，不做其他事。

## 阶段 0 · 开场（必回，先于一切）

回复（措辞可微调，但必须包含这三项信息）：

> 我是一键搭建项目助手，可以帮你从一个空文件夹直接搭建成一个可直接投产的单 Agent 工程。
> 现在请给我以下信息：
> 1. 指定一个项目文件夹（默认当前目录）
> 2. 项目名

## 阶段 1 · 模块选择

收到用户回复后，列出默认通用模块：

> 默认通用模块如下（可多选，逗号分隔）：
> - web：前端页面
> - api：后端接口
> - db：数据库
> - worker：异步任务/队列
> - tests：测试
> 也可以回复「默认模板」，由我生成推荐组合（web + api + db + worker + tests，推荐）。

用户也可以直接描述自定义模块（名称/关键词/代码目录），照实记录，不猜测。

接着确认运行环境（默认不确认时按 auto 处理）：

> Python 运行时（优先复用你已有的）：
> - 自动（推荐）：检测你已装的 Python（py 启动器 / PATH / uv），直接复用
> - 帮我安装：检测不到时自动部署（uv python install 或 winget）
> - 指定路径：给我 Python 可执行文件路径
>
> 依赖方式：
> - 自动（推荐）：已有 .venv 直接复用；否则用 uv 创建（共享依赖缓存）；
>   都没有则项目内创建 .venv
> - 共用系统依赖：项目 .venv 直接可见你 Python 已装的包
> - 仅复用已有 / 跳过

## 阶段 2 · 执行部署

按用户选择运行：

```bash
python <本skill路径>/scripts/bootstrap.py <文件夹> --name <项目名> \
    [--template default | --module web --module api ...] [--code "名称=目录"] \
    [--python auto|system|install|<路径>] [--env auto|shared|isolated|reuse|skip]
```

- 用户选「默认模板」→ `--template default`（web + api + db + worker + tests）；
- 用户点名模块 → 对应 `--module web` 等（命中目录自动带关键词与代码目录）；
- 自定义模块 → `--module "名称=关键词1,关键词2" --code "名称=目录"`；
- Python 运行时 → `--python auto`（默认，检测复用用户已有）/ `install`（自动部署）/ 路径；
- 依赖方式 → `--env auto`（默认，复用已有/uv/项目内创建）/ `shared`（共用系统依赖）/
  `isolated`（项目内干净 .venv）/ `reuse` / `skip`；
- 目标目录非空且已有 AGENTS.md → 先向用户确认是否 `--force` 覆盖；
- 用户未提供任何信息直接要求开始 → 用当前目录 + 目录名 + 默认模板执行。

脚本自动完成：复制骨架（README / AGENTS.md / docs / tools / .gitignore）→
填路由表 → 替换系统占位符 → 建模块占位目录 → 写 R1 档案 → 生成 llms.txt →
解析 Python 运行时（默认复用用户已有）→ 按依赖策略处理 .venv（默认复用已有，
无则 uv/项目内创建）→ git init → 缺 iteration-close-loop 时自动安装。

## 阶段 3 · 校验

运行目标目录 `tools/check_drift.py`，确认硬标记 0；列出剩余 `{{占位符}}`。

## 阶段 4 · 收尾话术（必说）

> 一键部署完毕 ✅
> 已生成完整工程骨架：README、AGENTS.md 启动契约、docs 五层目录、台账/档案/状态卡、
> 工具链、.venv、git 仓库（提交命令：git add -A && git commit -m "chore: init"）。
> 你现在可以新开一个对话框，描述你想做什么，或从哪个功能模块开始设计。

若还有剩余占位符，附一句：「剩余待填：……（可按我列出的清单逐项补齐）」。

## 规则

- 阶段 0 永远先于其他回应；即使目录非空，也先走开场，覆盖确认留在阶段 2；
- 只部署用户确认过的模块，不猜测名称/关键词/代码目录；
- 幂等：已存在文件不覆盖（`--force` 显式才覆盖）；
- 部署完成后不再追问业务细节，按阶段 4 引导用户新开对话。
