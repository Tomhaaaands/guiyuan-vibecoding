# NOW - VibeCoding_Manager state card (2026-09-03)

## Focus
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
1. Run `python tools/behavior_harness.py` as a round gate and extend red-team scenarios.
2. Wire a local bge-m3 embedder so the semantic gate and red-line judgment run without a key
   (hardening).
3. Then make the packaging/release decision for the runtime loop (which tools ship inside the skill
   template vs stay repo-internal), and optionally the P7 Private Butler inbox/result bridge
   (user-gated).
4. Keep proxy URLs under periodic browser checks.

## Authority pointers
- [Token contract](docs/02-technical/token-budget.md) · [Context contract](docs/02-technical/artifact-context-contract.md) · [Roadmap](docs/01-product/roadmap.md)
