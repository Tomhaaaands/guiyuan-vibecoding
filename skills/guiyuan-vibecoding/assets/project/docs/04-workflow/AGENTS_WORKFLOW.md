# AI Operation Overview · Module Routing and Development Workflow

> Single entry point for the development process: module routing + two workflows +
> per-round checklist + change mapping.

## 1. Module routing table (agent must read, in order)

| Keywords | Required reading | Code |
| --- | --- | --- |
| {{MODULE_A}} | `01-product/{{MODULE_A}}/` → `02-technical/{{MODULE_A}}/iteration.md` | {{CODE_DIR}} |
| {{MODULE_B}} | `01-product/{{MODULE_B}}/` → `02-technical/{{MODULE_B}}/iteration.md` | {{CODE_DIR}} |

## 2. Two workflows

- **Workflow 1 backend**: PRD → contract (`api.md` first) → data → implement → self-check → changelog;
- **Workflow 2 frontend**: PRD → routes → Figma → design → code (manual trigger);
- Methodology and migration guide: [iteration-methodology.md](iteration-methodology.md).

## 3. Document map (owner · when to update)

| Doc | Content | Update timing |
| --- | --- | --- |
| `changelog.md` | one-line ledger (mandatory every round) | append a row on every change |
| `NOW.md` | current-focus card (≤20 lines) | every round end |
| `archive/` | full archive volumes | every round detail |
| `roadmap.md` | milestones + one-line acceptance | milestone changes |
| `review-checklist.md` | per-round self-check gates | every round close |
| `iteration-methodology.md` | reusable methodology | methodology evolution |
| root `llms.txt` | machine-readable doc index | doc-structure changes (`tools/gen_llms_txt.py`) |

> Boundaries: changelog=one-line index; NOW=current focus; archive=archaeology; module
> iteration.md=rolling state card; red lines/pitfalls/key decisions are never archived.

## 4. Standard actions for every change (minimal closure)

1. Append a changelog row + write the archive volume (`tools/rollup_round.py`);
2. Update NOW.md (focus / blockers / next);
3. Incrementally sync affected docs (no full rewrites);
4. Back-sync the PRD "current/status" section;
5. Red-line check;
6. Final self-check: no stale "TBD / not-synced" markers; structural checks pass.

## 5. Minimum-context opening checklist

- [ ] read NOW.md only; obtain current task/module authority pointers
- [ ] read exact target authority fields/spans, not whole module folders
- [ ] load this workflow only for process/routing changes
- [ ] load changelog/archive only for regression, history, or close-out
- [ ] interfaces → api.md exact contract; safety → relevant red-line clauses
- [ ] startup package passes the context-budget hard ceiling

## 6. Change type → doc mapping (quick reference)

| Change | Docs to update |
| --- | --- |
| any code/doc change | changelog (row) + archive (detail) + module iteration.md |
| new/changed API | api.md + changelog |
| iteration-system changes | iteration-methodology.md + templates/ + skills + llms.txt + changelog |
