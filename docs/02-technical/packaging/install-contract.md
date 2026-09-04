---
artifact_id: technical/packaging/install
kind: technical-spec
status: accepted
supports: [product/install]
---
# Install Technical Contract

安装器必须校验版本与校验和、备份同名目录、失败可恢复，并把目标路径作为显式配置；技能
正文保持 Agent 中立，`agents/openai.yaml` 仅是可选适配器。

安装目标写入 `.guiyuan-vibecoding-install.json` 清单，记录版本、组件路径和哈希。更新时
Guiyuan 自有 Skill 包整体事务化替换；用户修改过的组件不覆盖。卸载只删除清单确认的
Guiyuan 内容；旧名称仅作为迁移识别，不得据名称删除其他 Skill。

卸载必须按精确命名空间处理 MCP：当前 VCM 没有自有 MCP Server，因此无 VCM 注册时不操作；
`guiyuan_butler_*` 属于 Guiyuan Butler，永远不得删除或注销。

## Runtime packaging boundary (decision 2026-09-03)

- **Managed-project template ships the in-project loop only**: the generic iteration/gate tools
  (`rollup_round`, `check_drift`, `context_budget`, `gen_llms_txt`, `hydrate`, `distill`,
  `workflow_optimize`, `architecture_audit`, `selfqa`, `vcm_session_hook`, `render_project_home`).
  These are project-local, stdlib-only, and read/write only the host repository.
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
