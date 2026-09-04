# NOW - Guiyuan Vibecoding state card (2026-09-05)

## Focus
- R67 functional-module-directory: 新增面向人的中文功能模块目录与 `functionalModules` 数据块；status.html 直接引用，PB 明确为可选 provider 桥；无 PB 独立 QA 与 suanming_os 虚拟接管渲染均通过。
- R66 registry-confirmation-anchors: scaffold now creates a topology-independent machine layer;
  registry indexes human PRD/acceptance/technical docs and immutable REQ/PLAN/QA/RELEASE anchors
  preserve user confirmations with hashes.
- R65 composable-templates: 四种项目拓扑、三档规模与能力 Overlay 已接入 scaffold；生成项目携带 manifest/template lock，工具通过语义 artifact 映射路径。
- R62 static-project-home-assets: 修复直接打开 `templates/guiyuan-vibecoding-home.html` 时背景图相对路径失效；模板旁补齐资源副本并同步安装载荷。R61 的静态 `status.html` 仍由 bootstrap / rollup_round 自动生成，不依赖 8010 监听。
- R60 guiyuan-lifecycle-close: 对外 Skill 全量迁移为 `guiyuan-*`；Agent 原生安装适配器已覆盖预检/安装/更新/卸载，卸载后残留检查与三阶段协议已同步到内部版和发布载荷。
- R63 pb-similarity: PB 已提供 `guiyuan_butler_similarity` v1；VCM 桥与 `hydrate --semantic`
  已改为真实 MCP 调用，超过 PB 字节预算或服务不可用时仍回退关键词。
- R64 pb-embedding-ownership: `analysis_eval --mode semantic` 也已改为 PB
  `guiyuan_butler_similarity`；VCM 不再调用 SiliconFlow `/embeddings` 或持有 BGE 参数，桥完成
  `initialize → tools/list → capabilities` 缓存发现。
- R58 pb-contract: 以 PB api-contract.md 对齐 VCM 桥（MCP /mcp、pb_token、guiyuan_butler_*、/healthz）。
- R52 pb-arch: 向量化归 PB（bge-m3+向量库），VCM 仅 `pb_enabled` 接入；roadmap 漂移已修、加同轮更新规则。
- R47 capability graph migration: product capabilities now have focused PRD/acceptance docs; technical docs are organized by responsibility domains; template scaffolding creates standard product/technical module files.
- R46 internal doc migration complete: root authority docs now live under `00-system/`, `01-product/`, `02-technical/`, and `03-reference/`; audit reports zero classification conflicts.
- Published/internal boundaries and the five-layer skeleton are established; module routing now loads capability docs plus only affected technical domains.
- v0.1.0 product baseline; version line `0.1.x` (`v1.2.0` is history). Authority:
  [docs/01-product/product-baseline-v0.1.0.md](docs/01-product/product-baseline-v0.1.0.md).
- Single/multi-project governance is product scope; Guiyuan Butler is an optional, user-gated
  inbox/result bridge. Creator OS is independent. Image source: `gh-proxy.com` -> `ghfast.top`.
- P0-P8 local loop is complete and verified; detailed implementation status lives in the capability
  docs and latest receipts, not this startup card.

## Blockers
- The PB semantic gate needs a reachable PB endpoint with an embedding provider (normally local
  bge-m3); VCM does not host or call an embedding model itself. Semantic evaluation now fails
  closed when the PB capability is unavailable rather than silently using a different scorer.
- Red-line judgment needs a real provider: `local-fallback` returns `unknown`, so it stays
  conservative and cannot judge a true violation.

## Next
0. 用 Creator OS 真实仓库运行 composite + large + rag + vector-db + worker + content-pipeline scaffold/adoption 验证；确认 manifest 映射、registry 与既有文档保留。
1. PB end-to-end: set pb_endpoint/pb_token and run the live interop check; source fixtures are not production evidence.
2. Run python tools/behavior_harness.py as a round gate and extend red-team scenarios.

## Authority pointers
- [Token contract](docs/02-technical/token-budget.md) · [Context contract](docs/02-technical/artifact-context-contract.md) · [Roadmap](docs/01-product/roadmap.md)
