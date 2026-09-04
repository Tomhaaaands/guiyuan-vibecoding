# NOW - Guiyuan Vibecoding state card (2026-09-04)

## Focus
- R62 static-project-home-assets: 修复直接打开 `templates/guiyuan-vibecoding-home.html` 时背景图相对路径失效；模板旁补齐资源副本并同步安装载荷。R61 的静态 `status.html` 仍由 bootstrap / rollup_round 自动生成，不依赖 8010 监听。
- R60 guiyuan-lifecycle-close: 对外 Skill 全量迁移为 `guiyuan-*`；Agent 原生安装适配器已覆盖预检/安装/更新/卸载，卸载后残留检查与三阶段协议已同步到内部版和发布载荷。
- R58 pb-contract: 以 PB api-contract.md 对齐 VCM 桥（MCP /mcp、pb_token、guiyuan_butler_*、/healthz）。
- R52 pb-arch: 向量化归 PB（bge-m3+向量库），VCM 仅 `pb_enabled` 接入；roadmap 漂移已修、加同轮更新规则。
- R47 capability graph migration: product capabilities now have focused PRD/acceptance docs; technical docs are organized by responsibility domains; template scaffolding creates standard product/technical module files.
- R46 internal doc migration complete: root authority docs now live under `00-system/`, `01-product/`, `02-technical/`, and `03-reference/`; audit reports zero classification conflicts.
- Published/internal boundaries and the five-layer skeleton are established; module routing now loads capability docs plus only affected technical domains.
- v0.1.0 product baseline; version line `0.1.x` (`v1.2.0` is history). Authority:
  [docs/01-product/product-baseline-v0.1.0.md](docs/01-product/product-baseline-v0.1.0.md).
- Single/multi-project governance is product scope; Private Butler is an optional, user-gated
  inbox/result bridge. Creator OS is independent. Image source: `gh-proxy.com` -> `ghfast.top`.
- P0-P8 local loop is complete and verified; detailed implementation status lives in the capability
  docs and latest receipts, not this startup card.

## Blockers
- The semantic gate needs an embedding provider to run (SiliconFlow `BAAI/bge-m3` today; a local
  bge-m3 endpoint would make the exact gate run without a third-party key).
- Red-line judgment needs a real provider: `local-fallback` returns `unknown`, so it stays
  conservative and cannot judge a true violation.

## Next
0. PB end-to-end: wait for PB to ship versioned `similarity`; set `pb_endpoint`/`pb_token` and run live联调.
1. Run `python tools/behavior_harness.py` as a round gate and extend red-team scenarios.

## Authority pointers
- [Token contract](docs/02-technical/token-budget.md) · [Context contract](docs/02-technical/artifact-context-contract.md) · [Roadmap](docs/01-product/roadmap.md)
