# Changelog (one-line round ledger)

> One row per round; read the latest 1-3 rows for status. Full methodology:
> [docs/iteration-methodology.md](docs/iteration-methodology.md).
> Row format: `| R1 | MM-DD | module | one-line conclusion (what/why/how-verified) |`

## 2026-08-27

| Round | Date | Module | One-line conclusion |
| --- | --- | --- | --- |
| R2 | 08-27 | i18n | Full English conversion for token efficiency and GitHub fit: README/AGENTS/CHANGELOG/methodology, both skills (scripts, guided stage scripts, openai.yaml), template skeleton, and all tool docstrings/outputs; English placeholders ({{MODULE_A}} etc.) with bootstrap matching both English and Chinese placeholder rows; verified end-to-end (English deploy, 0 hard markers, skills valid, no Chinese residuals except intentional dual-language matchers) |
| R1 | 08-27 | init | v0.1.0 first open-source release, distilled from the Creator OS iteration system: guided scaffold skill (project-bootstrap, explicit-only) + close-loop skill (iteration-close-loop) + project template skeleton + 5 deterministic tools (install/rollup/hydrate/check_drift/gen_llms_txt) + full methodology doc + MIT license |
