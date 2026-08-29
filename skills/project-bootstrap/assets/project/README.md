# Iteration Methodology Template (templates/iteration-methodology)

> Source: the VibeCoding_Manager open-source kit. Copy into any new project, replace the placeholders,
> and you get an AI-driven development iteration loop: startup contract + one-line ledger +
> archive volumes + state cards + deterministic gates.

## Contents

```text
AGENTS.md                       # startup-contract skeleton (reading order/routing/discipline/index)
docs/04-workflow/
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
  check_drift.py                # stale markers + llms.txt link validation
  gen_llms_txt.py               # generate root llms.txt
```

## Three steps to go live

1. **Copy**: copy this directory into the new project root;
2. **Fill placeholders**: replace `{{PROJECT_NAME}}`; trim the routing table and technical
   constraints in AGENTS.md; write the R1 init row into changelog
   (or run `python tools/rollup_round.py --round R1 ...`);
3. **Generate + verify**: `python tools/gen_llms_txt.py` for llms.txt, then
   `python tools/check_drift.py` plus the project's own structural checks.

## Optional: behavior packaging

Install the skills once and every project inherits them:
`$iteration-close-loop` closes out rounds; `$project-bootstrap` one-click deploys
(this template ships inside it — the first conversation copies the skeleton, writes R1,
generates the index, and auto-installs the close-loop skill).

## Relationship to the full methodology

Principles and migration guide: `docs/04-workflow/iteration-methodology.md` (§11).
This template = the minimal set (four files) + standard set (toolchain), materialized.
