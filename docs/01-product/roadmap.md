# Guiyuan Vibecoding vNext roadmap

> Public version line: `0.1.x` (pre-1.0). The earlier `v1.2.0` tag is a historical development
> snapshot, not a 1.0 stability statement.

> Delivery order is dependency-driven. Each milestone has one measurable acceptance sentence; a
> later milestone does not begin by widening scope around an unverified earlier loop.

| Phase | Scope | Status | Acceptance |
| --- | --- | --- | --- |
| P0 | product north star, scope, manager state machine, authority boundary | complete 2026-08-31 | product contract makes the user a decision-maker, not the operator of project management |
| P1 | field/span context compiler, delta continuation, token budgets and indexing | hardened 2026-08-31 | startup is zero-history; normal management targets 1,800 tokens and blocks above 2,500 |
| P2 | natural-language product/design/technical analysis | implemented (scoring via PB when enabled; standalone = keyword/provider) | ambiguous intent becomes labelled facts, assumptions, options, decisions, and missing questions |
| P3 | authority artifact generation and cross-artifact consistency | implemented | an agent can understand the project from accepted product/design/technical/decision/state artifacts without contradiction |
| P4 | milestone/task graph, dependencies, readiness, acceptance and next-task dispatch | implemented | the manager can explain and select the next executable task without a user-maintained board |
| P5 | code -> checks -> repair/block -> receipt -> artifact/state sync loop | implemented | one real task progresses from ready to delivered only with verification evidence |
| P6 | experience candidates, project red lines, shadow policy evaluation and rollback | implemented (red-line judgement requires a real LLM provider; local-fallback returns unknown) | a repeated failure becomes one evidence-backed candidate and cannot silently change production behavior |
| P7 | optional Private Butler capability/inbox/result bridge | VCM-side bridge implemented (`tools/pb_bridge.py` + `hydrate --semantic`); PB-side gateway/tools + response-shape consumption pending | candidates are user-gated and idempotent; embedding/semantic runs inside PB; VCM never owns a model or vector store |
| P8 | end-to-end MVP evaluation and packaging decision | complete (R42 walkthrough) | one scripted small-product journey completes analysis through reflection within token and quality budgets |
| P9 | settings UI, complete scaffold topology, reference capture, migration audit | partial (static project home + adopt/assess; complete scaffold topology and reference capture pending) | a user can configure VCM in the admin UI and adopt a legacy layout with a read-only conflict report and confirmed incremental migration |
| P10 | Guiyuan naming, universal request protocol, install preflight/update/uninstall lifecycle | complete 2026-09-04 | every public Skill uses the `guiyuan-` namespace, every request exposes understanding → solution → plan, and install/uninstall only changes manifest-owned VCM components while preserving user data and Butler MCP |

Existing-project adoption is a compatibility layer, not a Creator OS migration.
It may preserve, map, or manage one workflow at a time and never changes a project automatically.

## Roadmap iteration rule

The roadmap is the delivery-order authority, not a one-time plan. When a new requirement or scope
change is accepted into the product (`docs/01-product/`), the same round must also update this table:
add or revise the affected phase/milestone, set its status to the actual evidence state, and update
its acceptance sentence. A phase is only `implemented` when its deterministic gate and an execution
receipt exist; provider/backend-dependent items (such as semantic scoring via the PB bridge, or
red-line judgement via a real LLM provider) stay flagged as pending until that endpoint is wired.
Embedding and vector ownership always live in Private Butler, never in VCM. Never leave a status here
ahead of or behind the implementation evidence in `CHANGELOG.md` and the archive.

## MVP scope lock

The first end-to-end cut uses one local Git repository, one primary coding agent and one recommended
stack. The v0.1.0 product direction includes a repository-backed single/multi-project overview;
implementation follows after the core P2-P8 evidence loop is reliable.
