# Guiyuan Vibecoding cognitive and execution architecture

> Status: accepted architecture direction (2026-08-31). Implement as a modular monolith first;
> Skills, plugins, desktop surfaces, and services are channels or packaging choices, not the core.

## 1. Four-plane model

### Project Brain

Maintains authoritative product, design, technical, decision, task, state, verification, and
experience artifacts. Its context compiler serves pointer cards, exact field/span slices, and
receipt excerpts under a 1,800-token operating target and 2,500-token hard ceiling. Continuations
send deltas and content hashes instead of replaying unchanged context.

### Planning and Dispatch

Determines the current stage, detects missing decisions, decomposes milestones, maintains task
dependencies, selects the next executable task, and routes work to an executor.

### Development Operations

Coordinates code/design/tool execution, build and tests, Git changes, deployment adapters, and
structured receipts. Codex, Claude, Figma, browsers, GitHub, and hosting providers are executors or
channels behind provider seams.

### Reflection and Evolution

Converts verified task outcomes into project red-line candidates, reusable experiences, workflow
candidates, and product-improvement proposals. Policy candidates run in shadow mode before
promotion and remain revisioned and rollbackable.

## 2. Manager state machine

```text
INTAKE -> ANALYSIS -> SPECIFICATION -> PLANNING -> EXECUTION
       -> VERIFICATION -> DELIVERY -> REFLECTION -> NEXT
```

| State | Manager responsibility | Exit gate |
| --- | --- | --- |
| INTAKE | capture raw user intent and evidence | source retained; no unsupported assumption promoted |
| ANALYSIS | clarify product/design/technical choices | scope, constraints, unknowns, decisions identified |
| SPECIFICATION | publish authority artifacts | cross-artifact consistency gate passes |
| PLANNING | create milestone/task dependency graph | every ready task has acceptance and inputs |
| EXECUTION | build the selected task | executor receipt and changed-artifact list exist |
| VERIFICATION | run deterministic and judgement checks | acceptance evidence passes or failure is recorded |
| DELIVERY | commit/release and sync project state | delivery receipt, version/state, and rollback path exist |
| REFLECTION | extract lessons from outcome evidence | candidates deduped, scored, and stored as reviewable |
| NEXT | select next ready work or stop | current state card updated |

State transitions are persisted; a conversation ending does not reset them.

## 3. Task execution loop

```text
select ready task
  -> build minimum context package
  -> executor proposes/changes artifacts
  -> run build/tests/gates
  -> compare evidence with acceptance
  -> repair or record a blocker
  -> update affected authority artifacts only
  -> create execution receipt
  -> update task/project state
  -> reflect at task or milestone boundary
```

Required task fields:

- stable id, title, module, parent milestone;
- reason and expected product value;
- dependencies and blockers;
- input artifact references and target code paths;
- output contract and measurable acceptance criteria;
- risk/permission class;
- state: proposed, blocked, ready, active, verifying, delivered, failed, cancelled;
- execution and verification receipt references.

## 4. Proposed modular-monolith layout

```text
manager/
  intake/          raw intent, provenance, classification
  analysis/        product/design/technical analysis
  artifacts/       authority store, summaries, revisions, consistency
  planning/        milestones, task graph, readiness and selection
  context/         L0/L1/L2 retrieval, budgets, cache
  execution/       executor adapters and receipts
  verification/    build/test/acceptance gates
  reflection/      experiences, red lines, shadow policies
  bridges/         Private_butler and optional external context
  evaluation/      fixtures, metrics and regression thresholds
providers/
  agent/ git/ design/ browser/ deploy/ memory/
```

Keep one local runtime and repository-backed authority for the MVP. Introduce provider interfaces
without splitting the product into services.

## 5. Decision and authorization boundary

Automatic by default:

- reading project files and building context;
- generating draft analysis/artifacts;
- reversible edits inside the authorized task scope;
- local builds, tests, and read-only diagnostics;
- state updates supported by deterministic receipts.

User approval required:

- material scope or product-priority changes;
- paid service use, credentials, external account authorization;
- destructive data/file/schema operations without a verified rollback;
- privacy-sensitive handling beyond the accepted contract;
- production release or an action affecting real users.

## 6. Reflection ladder

```text
receipt/evidence
  -> project lesson candidate
  -> deduped experience with task signature
  -> shadow policy/workflow candidate
  -> evaluation against historical fixtures
  -> approved reusable rule/template/profile
```

Project-private facts never become universal policy. Promotion requires repeated evidence, no
quality regression, and review for high-risk behavior. Product/code improvements become planned
work; the manager never silently rewrites its production implementation.

## 7. Private_butler bridge

The bridge uses an optional provider seam:

- read: budgeted user preferences, prior interests, and project pointers;
- write: milestone-level digest and authoritative artifact reference;
- never copy full project specifications into personal memory;
- never make project execution depend on Private_butler availability;
- preserve lineage when an idea dispatch starts a project.
- expose project-analysis, implementation, verification and documentation capabilities through an
  optional executor declaration; inbox receipt never grants execution permission.
- return an idempotent result receipt containing status, authoritative artifact references and
  verification evidence.

### 7.1 Embedding/vector ownership (decision 2026-09-03)

VCM never owns an embedding model or a vector database. All embedding/semantic/vector state lives in
Private Butler (bge-m3 + a vector store). VCM exposes a single `pb_enabled` toggle:

- `pb_enabled=off` (default, standalone VCM): no PB connection, no model, no index. Retrieval is
  deterministic (docs + L0/L1/L2 + keyword), and the LLM provider runs analysis/judgement. This is
  the stdlib-only, zero-model release baseline.
- `pb_enabled=on` (empowered): VCM delegates semantic ranking and user-context to PB over a stable
  interface and never touches vectors. PB unreachable degrades to keyword + no user context, and
  never blocks the iteration loop.

The interface is stateless and does not copy project facts into personal memory:

- `similarity(query, texts[]) -> ranked ids + scores` — on-demand scoring for VCM's own candidate
  spans; nothing is persisted by VCM, and the index for project facts stays in the project repo.
- `memory_context(query) -> budgeted user preferences/project pointers` — existing read path.
- `memory_result(...) -> idempotent result receipt` — existing write path.

PB may change its model or index implementation without a VCM redeploy, because both sides depend on
the contract, never on PB internals.

## 8. Evaluation authority

Before autonomous progression expands, create privacy-safe fixtures covering:

- ambiguous requirement clarification and assumption labelling;
- product/design/technical artifact consistency;
- task dependency/readiness selection;
- minimum-context package relevance and budget;
- failed build/test and repair/blocked transitions;
- false completion prevention;
- reflection dedup, shadow promotion, and rollback;
- optional bridge unavailable/degraded behavior.

One command must run structural, unit, integration, and behavior fixtures; model/provider/config
versions and token usage belong in the evaluation receipt.
