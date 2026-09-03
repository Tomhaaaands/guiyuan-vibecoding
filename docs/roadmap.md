# VibeCoding_Manager vNext roadmap

> Public version line: `0.1.x` (pre-1.0). The earlier `v1.2.0` tag is a historical development
> snapshot, not a 1.0 stability statement.

> Delivery order is dependency-driven. Each milestone has one measurable acceptance sentence; a
> later milestone does not begin by widening scope around an unverified earlier loop.

| Phase | Scope | Status | Acceptance |
| --- | --- | --- | --- |
| P0 | product north star, scope, manager state machine, authority boundary | complete 2026-08-31 | product contract makes the user a decision-maker, not the operator of project management |
| P1 | field/span context compiler, delta continuation, token budgets and indexing | hardened 2026-08-31 | startup is zero-history; normal management targets 1,800 tokens and blocks above 2,500 |
| P2 | natural-language product/design/technical analysis | next | ambiguous intent becomes labelled facts, assumptions, options, decisions, and missing questions |
| P3 | authority artifact generation and cross-artifact consistency | planned | an agent can understand the project from accepted product/design/technical/decision/state artifacts without contradiction |
| P4 | milestone/task graph, dependencies, readiness, acceptance and next-task dispatch | planned | the manager can explain and select the next executable task without a user-maintained board |
| P5 | code -> checks -> repair/block -> receipt -> artifact/state sync loop | planned | one real task progresses from ready to delivered only with verification evidence |
| P6 | experience candidates, project red lines, shadow policy evaluation and rollback | planned | a repeated failure becomes one evidence-backed candidate and cannot silently change production behavior |
| P7 | optional Private Butler capability/inbox/result bridge | planned | candidates are user-gated and idempotent; integration improves context while either product operates independently |
| P8 | end-to-end MVP evaluation and packaging decision | planned | one scripted small-product journey completes analysis through reflection within token and quality budgets |

Existing-project adoption is a compatibility layer, not a Creator OS migration.
It may preserve, map, or manage one workflow at a time and never changes a project automatically.

## MVP scope lock

The first end-to-end cut uses one local Git repository, one primary coding agent and one recommended
stack. The v0.1.0 product direction includes a repository-backed single/multi-project overview;
implementation follows after the core P2-P8 evidence loop is reliable.
