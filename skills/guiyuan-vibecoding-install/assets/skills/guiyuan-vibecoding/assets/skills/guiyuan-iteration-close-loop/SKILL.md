---
name: guiyuan-iteration-close-loop
description: Close out an iteration round or initialize a changelog + archive + state-card documentation loop, including one-line changelog rows, archive round files, NOW/state card updates, doc sync, and structure/drift checks. Use when recording an iteration, wrapping up a work round, or setting up a minimal doc loop in a new project.
---

# Iteration Close-Loop

Ensure every round of changes closes out traceably: one ledger row, an archive file, state-card
updates, doc sync, and deterministic gates.

## Universal request protocol

For every requirement, optimization, or question, respond in this order: **semantic understanding
-> recommended solution -> executable plan**. Keep it concise and auditable; do not expose hidden
chain-of-thought. If the request changes files or performs a destructive action, state the evidence
and user gate before execution.

## When to use

- Wrapping up a round of code/doc changes (changelog, archive, NOW, self-check);
- Initializing the minimal loop in a new project that has none;
- Checking whether docs have drifted from code.

## Minimal four-file loop (new projects)

1. `AGENTS.md` — startup contract: reading order + module routing + discipline + index pointers;
2. `changelog.md` — one-line ledger, row format
   `| R1 | 08-27 | module | conclusion (what/why/verified) | [r1](archive/...) |`;
3. `archive/` — round files `YYYY-MM-DD-rNN.md` with root cause / implementation / verification;
4. `review-checklist.md` — self-check items.

## Five-step closure (when a system exists)

1. Append a changelog row + write the archive file (use `tools/rollup_round.py` if present);
2. Update NOW.md / module state card: focus, blockers, next (<=20 lines; history goes to archive);
3. Incrementally sync affected docs (no full rewrites);
4. Back-sync user-visible changes to product docs "current/status" sections;
5. Self-check: red-line review + structure/drift checks pass; no stale "TBD / not-synced" markers.
6. Regenerate the project status page: run `python tools/render_project_home.py` so the root
   `status.html` reflects this round (a derived view, intentionally gitignored).

## Rules

- The one-line conclusion must answer: what changed, why, how verified;
- Red lines, pitfalls, and key decisions never go to archive — they stay in state cards and
  red-line docs, visible every round;
- Renumber on round collisions; archive naming `YYYY-MM-DD-rNN.md`;
- Gates first: rules that can be scripts should be scripts, not prompts;
- Progressive disclosure: keep per-round required reading minimal, retrieve the rest on demand.

## Tools (use when present)

- `tools/rollup_round.py`: archive round file + changelog row;
- `tools/hydrate.py`: keyword retrieval of relevant docs;
- `tools/check_drift.py`: stale markers + llms.txt link validation;
- `tools/gen_llms_txt.py`: regenerate the doc index;
- `tools/render_project_home.py`: regenerate the self-contained project status page (`status.html`);
- `tools/check_structure.py` (if the project has one): structural gates.

## Methodology

Read `docs/iteration-methodology.md` when present; otherwise this file is the complete rule set.
