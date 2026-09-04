# Fact ownership — which manager owns which memory

> Shared boundary contract, updated 2026-09-02, between **Guiyuan Vibecoding** (repo `vibecoding_manager`, the per-project
> manager") and **Private Butler** (repo `private_butler`, the personal "life manager"). Mirrored in both repos and kept
> identical; if the two copies drift, fix them here and re-sync.

## Purpose

The two managers must never grab the same fact. This table triages every "should I remember this?"
into exactly one home, so project state stays versioned and traceable in git, while the personal
library stays clean and personal.

## Three buckets

| Bucket | Holds | Home | Lifetime |
| --- | --- | --- | --- |
| 1 · Personal memory | about the human: identity, stable preferences, habits, life events, ideas, personal trajectory | Private_butler (`basic` / `life` / `idea`) | permanent / long / decaying |
| 2 · Project record | about the project artifact: why code/design/decisions, interfaces, routes, schema, red lines, round ledger, archive | the repo (AGENTS.md / docs / changelog / archive / red-lines / state cards) | versioned, immutable, git |
| 3 · Project digest | a lightweight pointer about a project, for cross-project awareness | Private_butler (`project` namespace, never injected into personal context) | pointer only, non-authoritative |

## Decision table

| Example fact | Owner | Home |
| --- | --- | --- |
| "I prefer dark theme and work at night" | Private_butler | personal library (`basic`) |
| "I'm increasingly into building personal AI assistants" | Private_butler | personal library (`life`) |
| "Flash idea: auto-draft my weekly recap" | Private_butler | idea track (`idea=true`) |
| "This endpoint is `POST /api/x` with fields a/b/c" | project record | repo (`api.md` + changelog) |
| "Why models were moved out of the repo (R121)" | project record | repo (`archive/...-r121.md`) |
| "Crawler must never bypass login state" | project record | repo (`red-lines.md`) |
| "Tom is building Creator OS; latest round R129 completed product naming" | project digest | Private Butler `project` namespace (pointer) |

## Triage (three questions, in order)

1. About **the human**? → Private_butler (bucket 1).
2. About a **project artifact** that must be versioned, co-located with code, and survive a NAS
   outage? → the repo (bucket 2).
3. About **"what I'm doing across projects"** (a pointer, not the record)? → Private_butler `project`
   namespace (bucket 3, pointer only).

## Tie-breakers (non-negotiable)

- The repo is the **single source of truth for project facts**; Private_butler never holds the
  authoritative copy.
- Private_butler is the **only home for personal / life / idea facts**; the repo never stores them.
- A fact that is both a personal preference and a project decision is **split into two**, never merged.
- In doubt: a project-artifact fact goes to the repo; a human fact goes to Private_butler.
- A `project` write into Private_butler is a pointer/summary, not a copy; it stays out of personal
  context (see Private_butler `product-spec.md` §2).
