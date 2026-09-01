# VibeCoding_Manager product contract

> Status: accepted vNext direction (2026-08-31). Current v0.1.0 remains the bootstrap/iteration
> foundation; capabilities in this document become shipped only when their roadmap acceptance gate
> passes.

## 1. One-line promise

The user describes what they want to build and confirms consequential choices; VibeCoding_Manager
accepts the management burden of turning that intent into coherent requirements, authoritative
artifacts, executable work, verified delivery, and reusable engineering experience.

It is a **vibecoding R&D butler**, not a project-management system that asks the user to operate a
backlog, maintain a board, or understand the internal workflow.

## 2. User responsibility vs butler responsibility

The user is responsible for:

- expressing goals, examples, preferences, constraints, and feedback;
- deciding material product trade-offs, cost, credentials, destructive operations, and releases;
- accepting or rejecting milestone outcomes.

The butler is responsible for:

- clarifying ambiguous intent and identifying missing decisions;
- analysing product scope, design direction, technical stack, and framework options;
- producing and maintaining product/design/technical authority artifacts;
- decomposing goals into dependency-aware tasks with measurable acceptance;
- choosing the next executable task and assembling its minimum context;
- coordinating coding, testing, documentation, Git, and delivery receipts;
- keeping progress current without asking the user to manage it;
- extracting project red lines and reusable experience from verified outcomes.

## 3. Product loop

```text
intent -> analyse -> specify -> plan -> execute -> verify -> deliver
       -> reflect -> improve policy/experience -> choose next work
```

The loop is complete only when delivery evidence updates the project state and reflection has had
an opportunity to produce experience candidates. A plan is not a completed task; model output is
not verification; a commit is not automatically a released product.

## 4. Authority and evidence

- Project facts live in the project repository and are versioned with the artifact.
- Every task has explicit inputs, outputs, dependencies, acceptance criteria, and state.
- Every execution produces a receipt: changed artifacts, commands/checks run, outcomes, and
  unresolved risk.
- User statements, agent inferences, accepted decisions, implementation state, and verified
  outcomes are distinct fact classes.
- LLMs may understand and propose; deterministic checks authorize state transitions where a
  deterministic check is possible.
- Reversible low-risk work may proceed automatically. Cost, external authorization, destructive
  change, sensitive data, material scope change, and production release require a user gate.

### Existing-project adoption

Existing projects begin with a read-only workflow assessment. Each management surface is chosen
independently by the user: **keep** leaves the prior workflow authoritative, **map** indexes it
without rewriting it, and **managed** activates only that VibeCoding_Manager layer. A confirmed
adoption records baseline hashes, backups, and a receipt in the repository; changed baselines block
application and require reassessment. Business code and unselected workflow files are never changed.

At milestone boundaries, receipts may produce at most three evidence-backed workflow suggestions.
They are a user-confirmed optimization bundle, not an automatic policy change; dismissed candidates
remain suppressed until new evidence creates a different candidate.

## 5. MVP scope fence

The first end-to-end MVP supports:

- one user, one local Git repository, and one primary coding agent;
- natural-language intake for one small software product;
- product, design, technical, decision, task, and state artifacts;
- dependency-aware task selection;
- one complete task loop: context -> code -> checks -> receipt -> artifact/state sync;
- milestone reflection that emits reviewable experience/red-line candidates;
- optional Private_butler context read and project-digest write-back;
- token accounting and blocking context-budget gates.

Deferred until the core loop is stable:

- multi-user project management and team assignment;
- a Kanban/Sprint user interface;
- broad multi-agent parallel orchestration;
- many framework/deployment profiles;
- autonomous production policy promotion;
- cloud-hosted code execution, mobile clients, and multi-tenant service operation.
- migration or replacement of CreatorOS / Flash_assistant; those remain independent projects.

## 6. User-facing experience

Normal interaction exposes four messages, not internal management machinery:

1. "I understand the goal as ..."
2. "I am working on ..."
3. "I need your decision because ..."
4. "This is complete; here is the evidence and next step."

Internal artifacts, task graphs, archives, Git operations, and gates remain inspectable but do not
become routine chores for the user.

## 7. Product success measures

- A vague idea reaches an accepted product/design/technical baseline without the user manually
  authoring management documents.
- At any moment the butler can explain current stage, current task, blockers, and next action.
- No task reaches verified/delivered state without acceptance evidence.
- A new conversation resumes from project facts without restating the project history.
- Normal task-management context remains within the budget in `docs/token-budget.md`.
- Repeated failures converge into one evidence-backed experience candidate rather than prompt
  accumulation.

## 8. Private_butler boundary

VibeCoding_Manager owns project truth. Private_butler owns personal memory and lightweight project
pointers. Integration is optional and low-coupling:

- at project start, read approved user preferences and related project pointers when available;
- during work, use repository artifacts as the only authority for project facts;
- at milestone close, return a short project digest plus artifact pointer;
- either system remains fully usable when the other is unavailable.

The shared ownership rules remain in `docs/fact-ownership.md`.
