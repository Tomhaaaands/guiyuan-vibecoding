---
artifact_id: technical/packaging/install
kind: technical-spec
status: accepted
supports: [product/install]
---
# Install Technical Contract

安装器必须校验版本与校验和、备份同名目录、失败可恢复，并把目标路径作为显式配置；技能
正文保持 Agent 中立，`agents/openai.yaml` 仅是可选适配器。

安装目标写入 `.guiyuan-vibecoding-install.json` 清单，记录版本、组件路径和哈希。对外只
安装一个可发现的 `guiyuan-vibecoding` Skill；安装器与 close-loop 是其内部生命周期/项目
载荷，不在全局 Skill 根目录中创建独立入口。更新时 Guiyuan 自有 Skill 包整体事务化替换；
用户修改过的组件不覆盖。卸载只删除清单确认的 Guiyuan 内容；旧名称仅作为迁移识别，不得
据名称删除其他 Skill。

旧版本可能在全局 Skill 根目录留下 `guiyuan-iteration-close-loop` 或
`guiyuan-vibecoding-install`。迁移时将它们移出发现根目录（Windows junction 只解除链接），
内容保留在旁路备份目录；项目需要 close-loop 时再由主 Skill 在项目目录中物化 `SKILL.md`。

卸载必须按精确命名空间处理 MCP：当前 VCM 没有自有 MCP Server，因此无 VCM 注册时不操作；
`guiyuan_butler_*` 属于 Guiyuan Butler，永远不得删除或注销。

## Runtime packaging boundary (decision 2026-09-03; public-entry refinement 2026-09-05)

- **Managed-project template ships the in-project loop only**: the generic iteration/gate tools
  (`rollup_round`, `check_drift`, `context_budget`, `gen_llms_txt`, `hydrate`, `distill`,
  `workflow_optimize`, `architecture_audit`, `selfqa`, `vcm_session_hook`, `render_project_home`).
  These are project-local, stdlib-only, and read/write only the host repository.
- **One public Skill, internal modules**: global discovery exposes only `guiyuan-vibecoding`.
  Install/update/uninstall and iteration close-out remain independently testable modules, but are
  routed through the main Skill. The close-loop `SKILL.md` is created only in a project that opts in.
- **Repo-internal runtime stays out of the template**: the product loop (`analysis`,
  `artifact_*`, `task_graph`, `receipt_loop`, `experience_loop`, `mvp_walkthrough`) plus
  packaging/QA/install (`check_package`, `build_dist`, `run_qa`, `sync_copies`, `install_skills`,
  `one_click_install`) are VCM product runtime, invoked locally and not copied into host projects.
- **No MCP server yet**: integration stays a local script/CLI; `agents/openai.yaml` remains the only
  adapter. MCP becomes a channel only when multi-agent or cloud orchestration is actually needed.
- **Local embedding wiring is not shipped**: a shared local model hub may hold weights for other
  products, but VCM never starts or calls an embedding endpoint and never stores vectors. When
  `pb_enabled` is on, semantic scoring goes only through Guiyuan Butler's public MCP contract;
  when it is off, VCM uses its documented non-semantic path.
- **Primary channel**: repo-direct install; the install-by-message zip is self-hosted with SHA-256
  and a manifest (published GitHub release retired).

## Static project-home delivery (decision 2026-09-04)

The managed-project payload includes `templates/guiyuan-vibecoding-home.html`, its visual assets
(including copies under `templates/assets/` so the template can be opened directly),
and `tools/render_project_home.py`. Bootstrap and iteration close-out render a derived `status.html`
by replacing only the template's `PROJECT` data block. CSS and decorative images are embedded into
the output, so the page opens directly with `file://` and does not require port 8010, a browser
server, or a live API. Markdown, code, and Git remain authoritative; `status.html` is disposable
and should stay gitignored.

## Release artifact loop (decision 2026-09-05)

一个版本只创建一个 annotated tag 和一个同名 GitHub Release。GitHub 自动提供 source zip/tar.gz；
VCM 额外上传安装 zip、`.sha256` 和 `.manifest.json`。安装 zip 的根目录必须恰好只有
`guiyuan-vibecoding`，不得包含 install/close-loop 独立 Skill 或嵌套 `SKILL.md`；发布脚本会在
任何 GitHub 写操作前拒绝不符合该契约的资产。发布顺序固定为：安全闸门 → QA →
`release_prepare.py`（版本、clean worktree、构建、哈希）→ tag → push commit/tag →
`publish_release.py --publish` → 远端回读资产、tag、draft 状态和安装包哈希 → 写 RELEASE anchor。
GitHub 自动生成的 Source code 压缩包属于源码快照，不是对话安装资产，不适用上述 Skill 根目录
约束；安装流程必须指向命名的 `guiyuan-vibecoding-<version>.zip`。
发布工具默认 dry-run，避免重复创建 Release；`--publish` 是唯一外部写操作开关。

每次版本号变更进入发布准备时，`tools/release_prepare.py` 自动运行
`tools/update_catalog.py`，整合并更新 `docs/03-reference/update-catalog.json`。catalog 记录
当前版本、tag、Release 地址、安装包、SHA-256 和 manifest 地址，并保留历史版本。catalog
发生变化后必须和版本变更一起提交；`publish_release.py` 在任何 GitHub 写操作前校验它与
目标 tag/version 一致。

## MCP trigger conditions (closes R18)

The runtime stays CLI/script-first and does not add an MCP server yet. MCP becomes a channel only
when at least one of these triggers is concrete:

- external clients (Guiyuan Butler or a third-party router) must submit task candidates or consume
  result receipts programmatically beyond a local inbox/file drop;
- multi-agent or cloud orchestration requires a standard, remotely callable surface (JSON-RPC/MCP);
- a hosted deployment needs to serve the manager loop behind an API contract to thin clients.

Until then the loop is invoked locally (scripts + `agents/openai.yaml` as the only adapter). The
Guiyuan install adapter exposes the full preflight/install/update/uninstall lifecycle to an Agent;
natural-language uninstall requests route to the same safe CLI and do not require a second
confirmation. Adding
MCP is a channel/packaging decision, not a change to the core loop, and must keep the same authority
boundaries (project repo is truth; receipts carry verification; user gates remain in code).
