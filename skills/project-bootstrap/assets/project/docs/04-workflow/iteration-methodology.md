# Iteration Management Methodology

> Status: effective (2026-08-27, v2.1). This document is a **reusable methodology** for
> AI-driven development iteration management. The reference implementation is the Creator OS
> project; migrate to other projects using the minimal set in §11 — no dependency on this repo.

## 1. Purpose and design goals

1. **Traceability**: every technical iteration/change has a doc record that answers
   "why was this line written this way";
2. **Always-current docs**: at any moment the docs show where the project is and what's next.

Scope: single-operator or small-team, AI-agent-driven development; supports parallel agents by
having each register rounds in the shared ledger (no hierarchy, sync via changelog).

## 2. Seven core principles (non-negotiable)

1. **Single source of truth**: each fact has exactly one authoritative home
   (interfaces -> api.md; routes -> routes-pages; progress -> changelog + state cards; red lines -> red-lines).
2. **Layered read/write**: read 1-3 ledger rows daily; read the module state card before coding;
   enter the archive only for archaeology.
3. **Same-round closure**: code, affected docs, and the ledger land in the same round — never
   "document later".
4. **Contract first**: interfaces/routes land in docs before implementation.
5. **Gates first**: rules that can be deterministic scripts should be scripts, not "rules the LLM
   must remember" (debuggable, free, token-free).
6. **Red-line accumulation**: post-mortem lessons become irreversible red lines, resident and visible,
   never archived.
7. **Progressive disclosure**: minimize what every round must read (startup contract + current focus);
   everything else is retrieved on demand or loaded on trigger.

## 3. Five-layer documentation system

| Layer | Responsibility | Contents |
| --- | --- | --- |
| 00-system | global facts | architecture, data layer, red lines, design system, versioning |
| 01-product | product truth | per-module PRDs incl. "current/status" (the only product-progress fact) |
| 02-technical | technical truth | module iteration.md state cards, api.md contract, pipelines/crawler/frontend docs |
| 03-reference | reference | tutorials, environments, templates |
| 04-workflow | process engine | workflows, ledger, archive, NOW, roadmap, checklist, methodology |

Separation rules: product vs technical; flow vs state; index vs full text.

## 4. Global declaration layer

### 4.1 Startup contract (AGENTS.md)

AGENTS.md is the mandatory per-conversation **startup contract**; it holds only four things:

1. required reading order;
2. module routing table (keyword -> required docs -> code);
3. documentation discipline and hard constraints (same-round closure, back-sync, red lines, paths, gates);
4. index pointers (where details live).

Rule: keep AGENTS.md index-sized (target <= 80 lines); detailed process goes into 04-workflow, read on demand.

### 4.2 Red lines

Red lines = irreversible constraints distilled from incidents. Rules:

- once written, never bypassed; new red lines must be added to `red-lines.md`;
- red lines, pitfalls, and key decisions are **never archived** — they stay in state cards and the
  red-line doc, visible every round;
- high-risk areas (crawling, cross-user data) require a red-line check before changing.

## 5. Two workflows

### Workflow 1: backend feature delivery

PRD -> **contract first** (api.md) -> data (data-layer / database.md) -> implement -> self-check
(review-checklist) -> changelog.

Every endpoint needs a triad (mandatory):

1. contract entry: path / method / params / response / error codes;
2. auth & billing semantics: user_id from token (never trust client input), deduction point, ref_id idempotency;
3. tests: at least happy path + 401/402.

### Workflow 2: frontend design collaboration

PRD -> routes (routes-pages) -> Figma -> design system -> code -> register api.md in the same round.

Rules: **manual trigger** (only when the user asks for Figma round-trips); Figma anchors
(fileKey / node id / variables id) must be recorded — no "synced" claims without anchors; frozen
token/component definitions change only from Figma.

## 6. Three-layer record model + current-focus card

The core design — it resolves "record cost vs traceability":

| Layer | Home | Granularity | When read/written |
| --- | --- | --- | --- |
| One-line ledger | changelog.md | one row per round: round/date/module/one-line conclusion/archive link | read 1-3 rows at round start; append one row at round end |
| Current focus | NOW.md | <=20 lines: focus / blockers / next + ledger pointer | read at round start; update at round end |
| State card | module iteration.md | latest facts/TODOs/pitfalls only, no round-by-round flow | read before coding; roll forward after changes |
| Archive | archive/YYYY-MM-DD-rNN.md | root cause / implementation / verification | read only for archaeology; written every round |

### 6.1 Ledger row format

`| R101 | 08-27 | module | one-line conclusion (what/why/how-verified) | [r101](archive/...) |`

The one-line conclusion must stand alone: what changed, why, and how it was verified.

### 6.2 Round rules

- round ids increment daily; collisions are renumbered (no duplicate ids);
- archive file naming `YYYY-MM-DD-rNN.md`; pre-numbering history by date;
- red lines / pitfalls / key decisions never archived;
- use `tools/rollup_round.py` to generate archive + insert the ledger row in one step.

## 7. Goal-locking

Goal-locking prevents context drift: at task start, lock the target in three layers.

1. **Routing table locks context**: keyword -> required docs -> code, read in order, never guessed;
2. **Contract first locks interfaces**: api.md is the only interface authority; frontend consumes the
   contract instead of waiting for the backend to announce field names;
3. **One-line milestone acceptance**: each roadmap milestone has a one-sentence acceptance criterion;
   status table uses ✅/🚧/⏳;
4. **Status markers lock freshness**: `[AI-DRAFT]` (AI-written, unconfirmed) / `[CONFIRMED]` /
   `[OUTDATED]` (must not persist).

## 8. Output rules

### 8.1 Five-step closure (any code change)

1. **Ledger + archive**: append a changelog row + write the archive volume (rollup_round.py);
2. **Incremental doc sync**: only the affected sections per the change-mapping table; no full rewrites;
3. **PRD back-sync**: user-visible behavior/field changes update the product doc "current/status" in
   the same round;
4. **Red-line check**: confirm nothing bypassed; new red lines written;
5. **Final self-check**: NOW.md updated, checklist passed, structure gates passed, no stale
   "TBD / not-synced" markers for this change.

### 8.2 Self-check (mandatory)

- changelog appended, affected docs updated same-round, PRD back-synced;
- no stale markers, no legacy path literals;
- backend: contract triad, user_id on new tables, ref_id idempotency, structure check passed,
  backend restarted and verified;
- frontend: routes/tokens/components synced, Figma anchors recorded, build passed;
- crawler: red-line check, cache-status verified.

### 8.3 Prohibitions

- code changes without doc updates (technical AND product);
- leaving stale markers for this change;
- bypassing deterministic gates (structure check, pre-commit).

## 9. Token-saving design (progressive disclosure in practice)

Core strategy: **minimize what every round must read; retrieve everything else on demand.**

| Layer | Resident/on-demand | Content | Size |
| --- | --- | --- | --- |
| resident | every conversation | AGENTS.md startup contract + NOW focus card | ~1-2k tokens |
| on-demand | module hit | _module.yaml + iteration.md via routing table | ~1-2k tokens/module |
| on-demand | before work | hydrate retrieval of relevant sections | on demand |
| triggered | skill hit | skill frontmatter resident (~tens of tokens); body loads on trigger | <5k |
| external | tools/crawlers | llms.txt machine index (a few hundred tokens) | optional |

Companion tools: `tools/hydrate.py` (keyword retrieval), `llms.txt` (doc index), skills
(behavior loaded on trigger). Rules: retrieve instead of inject; script instead of prompt;
reference instead of copy.

## 10. Toolchain (deterministic first)

| Tool | Responsibility | Trigger |
| --- | --- | --- |
| `tools/rollup_round.py` | archive volume + ledger row | every round closure |
| `tools/hydrate.py` | keyword retrieval of relevant docs | before work |
| `tools/check_drift.py` | stale markers + llms.txt link validation | periodic / closure |
| `tools/gen_llms_txt.py` | regenerate root llms.txt | doc-structure changes |
| `tools/install_skills.py` | install skills into $CODEX_HOME/skills | first setup |
| skill `project-bootstrap` | one-click guided scaffold (explicit-only) | new project's first conversation |
| skill `iteration-close-loop` | round close-out | every round wrap-up |

## 11. Reuse & migration guide (how to apply elsewhere)

### Minimal set (single new project, half a day)

1. `AGENTS.md`: startup contract (reading order + routing + discipline + index);
2. `docs/04-workflow/changelog.md`: one-line ledger (round/date/module/conclusion/archive link);
3. `docs/04-workflow/archive/`: archive volumes (`YYYY-MM-DD-rNN.md`);
4. `docs/04-workflow/review-checklist.md`: self-check list;
5. one-sentence acceptance per roadmap milestone.

### Standard set (+ template)

Copy `templates/iteration-methodology/`: AGENTS.md index skeleton, docs five-piece skeleton, NOW.md,
rollup/hydrate/check_drift/gen_llms_txt scripts; replace placeholders and you're live.

### Full set (+ behavior packaging)

Install the skills: `iteration-close-loop` closes rounds in any project; `project-bootstrap`
one-click deploys the kit into new projects and auto-installs the close-loop skill.

### Steps

1. copy the template -> 2. fill project name / module routing -> 3. write the R1 init row ->
4. run rollup_round once to verify -> 5. run the five-step loop for every round after.

## 12. Design sources and external comparison (evolution basis)

Same lineage as the 2025-2026 SDD ecosystem; reference implementations include:

- **github/spec-kit** (131k★): constitution + specify/plan/tasks/implement/converge ->
  maps to "startup contract + two workflows";
- **Fission-AI/OpenSpec** (66k★): propose/apply/archive change isolation ->
  maps to "five-step closure + archive volumes";
- **obra/superpowers** (278k★): skills loaded on demand ->
  maps to "progressive disclosure + skill packaging";
- **context-harness / ai-context**: AGENTS.md as a thin index + NOW/PLAN layers ->
  maps to "startup contract + NOW.md + hydrate";
- **gsd-build/get-shit-done** (64k★): context-rot prevention ->
  maps to "contract first + check_drift".

Differentiators: **red-line/pitfall residency**, **three-layer record model**
(ledger/state card/archive), and **deterministic gates**.

## 13. Iterating on this system itself

- changes to AGENTS.md / workflows / this doc -> sync `templates/iteration-methodology/` and
  `skills/project-bootstrap/assets/project/` in the same round;
- tool changes -> sync template copies and re-run tests;
- every round ends with: changelog row + archive volume + NOW.md update.
