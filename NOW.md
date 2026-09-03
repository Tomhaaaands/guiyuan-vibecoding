# NOW - VibeCoding_Manager state card (2026-09-03)

## Focus
- v0.1.0 product baseline; version line `0.1.x` (`v1.2.0` is history). Authority:
  [docs/product-baseline-v0.1.0.md](docs/product-baseline-v0.1.0.md).
- Single/multi-project governance is product scope; Private Butler is an optional, user-gated
  inbox/result bridge. Creator OS is independent. Image source: `gh-proxy.com` -> `ghfast.top`.
- P2 analysis core is live and verified: typed artifact store, deterministic context compiler,
  analysis orchestrator with `siliconflow` (Qwen/Qwen3-8B) + `local-fallback`, and model-routed
  red-line guarding (`judge_red_line` returns respects/violates/unknown). Details in
  [docs/provider-boundary.md](docs/provider-boundary.md).
- Promotion gate: `analysis_eval --mode semantic --min-f1 0.25` on 5 sentence-level fixtures;
  `siliconflow` ~0.299, `local-fallback` ~0.169. API key only via `VCM_SILICONFLOW_API_KEY`, never
  committed. `--mode similarity` (char-bigram) is experimental and unsound on sentence-level gold.
- P3 is in place: `tools/artifact_consistency.py` (validation) and `tools/artifact_generate.py`
  (labeled analysis -> draft product/decision artifacts) are verified by the harness.
- P4 dispatch is in place: `tools/task_graph.py` computes dependency readiness and selects the next
  executable task by priority (harness 17/17).
- P5 delivery loop is in place: `tools/receipt_loop.py` turns checks into a verdict, writes a
  revisioned receipt, marks the task done/in_progress/blocked, and syncs project-state (harness 18/18).
- P6 reflection is in place: `tools/experience_loop.py` turns failed/blocked receipts into draft
  `[AI-DRAFT]` experience candidates with a shadow red-line evaluation that never edits the
  authoritative red-lines.md (harness 19/19).
- P8 end-to-end MVP is in place: `tools/mvp_walkthrough.py` runs analysis -> artifacts -> dispatch ->
  receipt -> reflection within a context budget gate; the P0-P8 local loop (analysis to reflection)
  is complete (harness 20/20).
- Packaging is archived and documented: the P0-P8 loop is written into
  [docs/iteration-methodology.md](docs/iteration-methodology.md) §5a, the GitHub published
  `v0.1.0` release zip is retired and its release deleted, and repo clone is the default install.

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
- [Token contract](docs/token-budget.md) · [Context contract](docs/artifact-context-contract.md) · [Roadmap](docs/roadmap.md)
