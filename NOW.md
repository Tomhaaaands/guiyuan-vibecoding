# NOW - Guiyuan Vibecoding state card (2026-09-05)

## Focus
- R69 secure-git-release-loop: scaffold/adopt now materializes profile-aware `.gitignore`; staged
  `git_safety_gate.py` is a fail-closed pre-commit/CI/QA gate; release preparation and remote asset
  verification are scripted as one-tag/one-Release flow. Existing cache/dist history was removed
  from the index while preserving local files.
- R67 functional-module-directory: 新增面向人的中文功能模块目录与 `functionalModules` 数据块；status.html 直接引用，PB 明确为可选 provider 桥；无 PB 独立 QA 与 suanming_os 虚拟接管渲染均通过。
- R66 registry-confirmation-anchors: scaffold now creates a topology-independent machine layer;
  registry indexes human PRD/acceptance/technical docs and immutable REQ/PLAN/QA/RELEASE anchors
  preserve user confirmations with hashes.
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
