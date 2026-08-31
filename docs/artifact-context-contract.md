# Authority artifact and context contract

> Status: P1 contract (2026-08-31). This contract prevents project drift and controls token cost by
> separating authoritative storage from the minimum view used for one decision.

## 1. Authority artifact catalog

| Artifact | Owns | Must not own |
| --- | --- | --- |
| product-spec | user problem, audience, scope, requirements, product acceptance | implementation detail |
| design-brief | experience goals, flows, visual direction, design constraints | backend contracts |
| technical-spec | stack, architecture, data, interfaces, runtime/deployment constraints | product priority |
| decisions | accepted trade-offs, alternatives, evidence, date/revision | transient discussion |
| roadmap | milestones, ordering, one-line acceptance | task execution history |
| tasks | dependency graph, task contracts and lifecycle | duplicated specifications |
| project-state | current stage, current task, blockers, next | historical narrative |
| receipts | execution/verification/delivery evidence | future plans |
| experience | outcome-backed lessons and policy candidates | unverified guesses |
| archive | historical round narrative and archaeology | current authoritative status |

Every fact has one authority artifact. Other artifacts reference its stable id rather than copying
the fact.

## 2. Required metadata

Every managed artifact exposes machine-readable metadata, whether stored in front matter or a
sidecar index:

```yaml
artifact_id: technical/auth
kind: technical-spec
revision: 7
status: accepted
content_hash: sha256:...
updated_at: 2026-08-31
depends_on: [product/auth, decisions/auth-provider]
supersedes: technical/auth@6
l0_ref: summaries/technical-auth.l0
l1_ref: summaries/technical-auth.l1
```

Accepted status values are draft, review, accepted, superseded, and archived. An inference remains
draft until the relevant gate accepts it.

## 3. L0/L1/L2 views

- **L0 pointer card**: 20–80 tokens; ids, revision/hash, status, one conclusion/constraint, pointers.
- **L1 field slice**: 100–600 tokens; only named fields or exact spans needed for the current task.
- **L2 evidence slice**: exact source spans or receipt excerpts. A full artifact is loaded only for
  creation, dispute, audit, or when bounded evidence cannot support the decision.

Views are derived, not new authorities. L1 is compiled from fields rather than stored as a prose
mini-document. A source field/revision/hash change invalidates only affected cached slices.

## 4. Context builder input and output

Input:

- manager state and current task id;
- task dependencies, acceptance, risk class, target code paths;
- artifact graph and revision/hash cache;
- phase policy and token budget;
- optional user-context provider.

Output is a context manifest plus ordered sections:

```yaml
context_id: task-auth-07@3
phase: EXECUTION
target_budget: 1800
hard_ceiling: 2500
included:
  - {ref: project-state@12, fields: [stage, task, blocker], reason: current-state}
  - {ref: product/auth@4, fields: [acceptance], reason: acceptance-source}
  - {ref: technical/auth@7, spans: [contract.login], reason: implementation-contract}
  - {ref: decisions/auth-provider@2, fields: [constraint], reason: safety-boundary}
excluded:
  - {ref: archive/r14, reason: archaeology-not-required}
  - {ref: product/billing, reason: unrelated-module}
```

The manifest makes context choice inspectable and supports evaluation of missing or unused context.

## 5. Phase retrieval policy

| Phase | Default artifact levels |
| --- | --- |
| ANALYSIS | raw intent + labelled knowns/unknowns; relevant accepted fields only |
| SPECIFICATION | accepted analysis/decision fields; exact target artifact spans while writing |
| PLANNING | acceptance/constraint pointers; affected module fields only |
| EXECUTION | task/acceptance fields, contract spans, target code; no roadmap/history prose |
| VERIFICATION | acceptance clauses, diff hunks, verdict/excerpts; full logs only on failure |
| DELIVERY | verification verdict, version/release fields, rollback pointer |
| REFLECTION | receipt excerpts plus hashes of similar experience; milestone-batched |

Archives, unrelated modules, and the full methodology are excluded by default.

## 6. Consistency and update rules

- Update the smallest authority region that owns the changed fact.
- User-visible behavior changes product acceptance in the same round.
- Interface/schema changes update the technical contract before implementation is delivered.
- Task completion updates project-state but does not rewrite historical receipts.
- A decision change creates a revision and explicit supersession link.
- Derived summaries refresh only for changed source revisions.
- Cross-artifact checks validate references, incompatible accepted facts, missing acceptance, and
  state claims without receipts.

## 7. Context compilation and degradation

Before retrieval, the compiler reserves space for safety, permission, and acceptance, then fills
state, authority fields, and evidence in priority order. It must not spend unused budget merely
because capacity remains.

When a context exceeds budget:

1. remove repeated policy prose, duplicate facts, unchanged context, and successful log bodies;
2. narrow evidence to exact spans/excerpts and convert rationale to decision ids;
3. replace optional field slices with L0 pointers;
4. remove history, rejected alternatives, and unrelated dependency background;
5. stop with a budget conflict if required safety, permission, acceptance, or evidence cannot fit.

Required safety, permission, acceptance, and destructive-operation evidence are never silently
truncated. Continuation calls are delta-only: new user input, changed fields, new evidence, and the
next requested output. Unchanged context is referenced by context id/hash and is not replayed.
