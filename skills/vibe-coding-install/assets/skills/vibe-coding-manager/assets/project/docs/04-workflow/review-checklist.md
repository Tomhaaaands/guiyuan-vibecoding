# Review Checklist (per-round self-check)

> Run before closing a round. Every item is a gate; nothing is deferred to "later".
> Full process: [AGENTS_WORKFLOW.md](AGENTS_WORKFLOW.md) §4.

## Closure items

- [ ] changelog row appended (what / why / how-verified, archive link)
- [ ] archive volume written (`archive/YYYY-MM-DD-rNN.md`)
- [ ] NOW.md updated (focus / blockers / next, ≤20 lines)
- [ ] module state cards (`iteration.md`) rolled forward for touched modules
- [ ] affected docs incrementally synced (no full rewrites)
- [ ] product docs "current/status" back-synced for user-visible changes
- [ ] red-line review: no bypass; new red lines go to `red-lines.md`, never archived
- [ ] no stale "TBD / not-synced" markers left for this change
- [ ] structural gates pass: `tools/check_drift.py` + project-specific checks

## Opening items (start of a round)

- [ ] read AGENTS_WORKFLOW + latest 1-3 changelog rows + NOW.md
- [ ] read the target module's state card (`_module.yaml` -> `iteration.md`)
- [ ] interfaces: `api.md` is current; red lines: `red-lines.md` is current
