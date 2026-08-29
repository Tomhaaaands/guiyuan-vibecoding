# Changelog (one-line round ledger)

> One row per round; read the latest 1-3 rows for status. Full methodology:
> [docs/iteration-methodology.md](docs/iteration-methodology.md).
> Row format: `| R1 | MM-DD | module | one-line conclusion (what/why/how-verified) | [r1](archive/...) |`

## 2026-08-30

| Round | Date | Module | One-line conclusion | Archive |
| --- | --- | --- | --- | --- |
| R9 | 08-30 | naming | 品牌统一改名（用户拍板）：`_bootstrap`/鲁班 → **VibeCoding_Manager**（技术 repo 名 `project_bootstrap` 保留）；`luban-install` skill 改名 `vibe-coding-install`（触发词 `$vibe-coding-install`）；README/AGENTS/方法论（三副本）/模板/工具输出文案全部对齐；同步门禁（4 对）绿 | [r9](docs/04-workflow/archive/2026-08-30-r9.md) |
| R8 | 08-30 | release | v1.0.0 one-click install: template gains `review-checklist.md` + `roadmap.md` (both copies); check_drift adds template/asset sync gate (templates <-> assets, close-loop skill <-> asset copy, luban asset copies); new `tools/one_click_install.py` + `install.bat`/`install.sh` wrappers (Python ≥3.11 check → install skills → doctor → optional `--target` scaffold); new `luban-install` skill (explicit-only, self-contained: bundles installer + both skills as assets, so the kit installs/updates from inside Codex via `$luban-install`); VERSION bumped 1.0.0; verified doctor + check_drift green, standalone install from $CODEX_HOME, and temp-project scaffold contains the new docs | [r8](docs/04-workflow/archive/2026-08-30-r8.md) |
| R7 | 08-30 | distill | distill powered on: `pitfalls` (坑 → 红线) implemented as a deterministic first pass — scans a project's archive volumes + module `iteration.md` for pitfall/red-line/incident markers, dedupes, and emits `[AI-DRAFT]` candidates to `red-lines.draft.md` (dry-run by default, never auto-edits the authoritative `red-lines.md`); removed the wrong memory-os/embedding-service dependency (distill reads project archives only); `method`/`consolidate`/`promote` remain stubs; tool synced to template + asset copies; verified against tom_creator_os (135 files → 20 candidates); check_drift green | [r7](docs/04-workflow/archive/2026-08-30-r7.md) |

## 2026-08-29

| Round | Date | Module | One-line conclusion | Archive |
| --- | --- | --- | --- | --- |
| R6 | 08-29 | boundary | fact-ownership contract: shared docs/fact-ownership.md defines which fact goes to which manager (personal → memory-os; project record → repo; project digest → memory-os project namespace); mirrored identical in project_bootstrap + memory_os; AGENTS.md routing + index pointers added in both; check_drift green | [r6](docs/04-workflow/archive/2026-08-29-r6.md) |
| R5 | 08-29 | tooling | v0.3.0 self-iteration tooling: hydrate `--semantic` reserved interface (HYDRATE_SEMANTIC_BACKEND, graceful keyword fallback); install_skills.py `--doctor` self-check + VERSION file; distill.py + docs/distillation.md define the four-direction distillation loop (pitfalls/method/consolidate/promote, implementation deferred until the shared memory/embedding service stabilizes); methodology/README updated; template+asset copies kept identical; verified doctor + check_drift pass | [r5](docs/04-workflow/archive/2026-08-29-r5.md) |

## 2026-08-27

| Round | Date | Module | One-line conclusion | Archive |
| --- | --- | --- | --- | --- |
| R4 | 08-27 | profiles | v0.2.0 project-type profiles: 5 presets (default/saas/c-end/vector-db/cli-tool) + 4 composable dimensions (deploy/data/runtime/surface, 12 option files) + custom .toml support; bootstrap.py loads/merges profiles and injects modules, constraints, red-line stub (docs/00-system/constitution/red-lines.md), doc stubs, gitignore additions; guided stage 1 asks project type; min Python 3.11 (tomllib); verified saas/custom-dimension/default deploys | [r4](docs/04-workflow/archive/2026-08-27-r4.md) |
| R3 | 08-27 | readme | Marketing rewrite: pain points (context rot / doc drift / prompt bloat / discipline vacuum / bootstrap tax / round-trip amnesia), target audience (AI-native solo devs, small agent teams; explicitly not orgs needing spec-kit/OpenSpec), and five differentiators (conversation-first, deterministic gates, three-layer records, token-efficient, env-aware/git-ready); comparison table extended with get-shit-done | [r3](docs/04-workflow/archive/2026-08-27-r3.md) |
| R2 | 08-27 | i18n | Full English conversion for token efficiency and GitHub fit: README/AGENTS/CHANGELOG/methodology, both skills (scripts, guided stage scripts, openai.yaml), template skeleton, and all tool docstrings/outputs; English placeholders ({{MODULE_A}} etc.) with bootstrap matching both English and Chinese placeholder rows; verified end-to-end (English deploy, 0 hard markers, skills valid, no Chinese residuals except intentional dual-language matchers) | [r2](docs/04-workflow/archive/2026-08-27-r2.md) |
| R1 | 08-27 | init | v0.1.0 first open-source release, distilled from the Creator OS iteration system: guided scaffold skill (project-bootstrap, explicit-only) + close-loop skill (iteration-close-loop) + project template skeleton + 5 deterministic tools (install/rollup/hydrate/check_drift/gen_llms_txt) + full methodology doc + MIT license | [r1](docs/04-workflow/archive/2026-08-27-r1.md) |
