# Iteration Methodology Template (templates/iteration-methodology)

> Source: the VibeCoding_Manager open-source kit. Copy into any new project, replace the placeholders,
> and you get an AI-driven development iteration loop: startup contract + one-line ledger +
> archive volumes + state cards + deterministic gates.

## Contents

```text
AGENTS.md                       # startup-contract skeleton (reading order/routing/discipline/index)
docs/
  00-system/                    # global facts (architecture, data, red lines, versioning)
  01-product/                   # product truth and module PRDs
  02-technical/                 # technical truth and module state/contracts
  03-reference/                 # tutorials, environments, reusable references
  04-workflow/                  # process engine and iteration records
  AGENTS_WORKFLOW.md            # process skeleton (routing/two workflows/five-step closure/mapping)
  changelog.md                  # one-line ledger skeleton
  NOW.md                        # current-focus card skeleton (focus/blockers/next)
  roadmap.md                    # milestones + one-line acceptance skeleton
  review-checklist.md           # per-round self-check gate skeleton
  iteration-methodology.md      # the full methodology (reusable as-is)
  archive/README.md             # archive-volume rules
tools/
  rollup_round.py               # archive volume + ledger row
  hydrate.py                    # keyword retrieval over docs
  context_budget.py             # conservative token estimate + hard budget gate
  check_drift.py                # markers + links + startup budget + copy sync
  gen_llms_txt.py               # generate root llms.txt
  workflow_optimize.py          # receipt-backed, user-approved workflow suggestions
scripts/
  hooks/pre-commit              # commit gate: runs check_drift before every commit
  install_hooks.py              # install the gate into .git/hooks (idempotent)
```

## Three steps to go live

1. **Copy**: copy this directory into the new project root;
2. **Fill placeholders**: replace `{{PROJECT_NAME}}`; trim the routing table and technical
   constraints in AGENTS.md; write the R1 init row into changelog
   (or run `python tools/rollup_round.py --round R1 ...`);
3. **Generate + verify**: `python tools/gen_llms_txt.py` for llms.txt, then
   `python tools/context_budget.py` and `python tools/check_drift.py` plus the project's own structural checks; install the
   commit gate once: `python scripts/install_hooks.py` (bootstrap installs it automatically).

## Release vs internal boundary

The published payload contains reusable, agent-neutral skills and this project template. It does
not contain this repository's internal product PRD, `NOW.md`, `CHANGELOG.md`, or root `docs/`
content. Those files describe the VibeCoding_Manager repository itself and remain internal.
When installed into a host project, the template's `docs/` five-layer skeleton is created there.

Host-project authors' existing `CHANGELOG.md`, `NOW.md`, and `docs/` are treated as user-owned
content: adoption detects and preserves them; it does not hide them with blanket `.gitignore`
rules or overwrite them without an explicit managed workflow choice.

## Optional: behavior packaging

The template can be used with global skills installed once, or with a project-local copy under
`.vibecoding-manager/skills/`. `$iteration-close-loop` closes out rounds when the client supports
skill triggers; otherwise the project rules point to the local close-loop `SKILL.md` and scripts.

## Relationship to the full methodology

Principles and migration guide: `docs/04-workflow/iteration-methodology.md` (§11).
This template = the minimal set (four files) + standard set (toolchain), materialized.

## Existing-project adoption

An existing project is assessed before anything is changed. The manager inventories only its
management workflow, then the user selects `keep` (old workflow remains authoritative), `map`
(old workflow is indexed), or `managed` (the selected VibeCoding_Manager layer becomes active).
Before adoption it also computes a compatibility score and pauses when the match is low or an
existing similar management system is present; the user then chooses full takeover, scoped
takeover, keep-and-map, defer, or abandon. None of those choices writes business code.
The adoption record and receipts live in `.vibecoding-manager/`; backups stay local and are ignored.
At milestone boundaries `workflow_optimize.py` can propose at most three evidence-backed changes.
It never applies them without a new user confirmation.
