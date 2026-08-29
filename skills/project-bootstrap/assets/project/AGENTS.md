# {{PROJECT_NAME}} Agent Rules (mandatory · startup contract + index)

> Highest priority. This file holds only the reading order, routing table, discipline,
> constraints, and index pointers; full process in
> [AGENTS_WORKFLOW](docs/04-workflow/AGENTS_WORKFLOW.md), methodology in
> [iteration-methodology](docs/04-workflow/iteration-methodology.md), current focus in [NOW](docs/04-workflow/NOW.md).

## 0. Before every task (read, in order)

1. Read [AGENTS_WORKFLOW](docs/04-workflow/AGENTS_WORKFLOW.md) (process + module routing);
2. Read the latest 1-3 rows of [changelog](docs/04-workflow/changelog.md); archaeology goes to [archive](docs/04-workflow/archive/README.md);
3. Read [NOW.md](docs/04-workflow/NOW.md) (focus / blockers / next);
4. For a named module, read the relevant product/technical docs per §1;
5. For interfaces, [api.md](docs/02-technical/api-gateway/api.md) is the only authority (when present).

## 1. Module routing table (keywords → docs → code)

| Keywords | Required reading | Code |
| --- | --- | --- |
| {{MODULE_A_KEYWORDS}} | `docs/01-product/{{MODULE_A}}/` + `docs/02-technical/{{MODULE_A}}/` | {{CODE_DIR}} |
| {{MODULE_B_KEYWORDS}} | `docs/01-product/{{MODULE_B}}/` + `docs/02-technical/{{MODULE_B}}/` | {{CODE_DIR}} |

> Trim per project: one row per business module; keywords use the words users actually say.

## 2. Documentation discipline (non-negotiable)

- **Same-round closure**: every change completes changelog row + archive volume + incremental doc
  sync in the same round (AGENTS_WORKFLOW §4);
- **Back-sync**: user-visible behavior/field changes update the product doc "current/status" in
  the same round;
- **Red lines**: never bypassed; new red lines go into `docs/00-system/constitution/red-lines.md`;
- No full rewrites of unrelated docs; no stale "TBD / not-synced" markers for this change.

## 3. Technical constraints (cheat sheet)

- build/test commands: {{FILL_PER_PROJECT}};
- paths/storage/dependency constraints: {{FILL_PER_PROJECT}};
- every change must pass the project's structural check (e.g. `tools/check_structure.py` when present).
- a pre-commit gate runs `tools/check_drift.py` before every commit (bypass only with
  `git commit --no-verify`); reinstall with `python scripts/install_hooks.py`.

## 4. Index pointers

| Looking for | Read |
| --- | --- |
| Process details / change mapping | [AGENTS_WORKFLOW.md](docs/04-workflow/AGENTS_WORKFLOW.md) |
| Methodology / migration guide | [iteration-methodology.md](docs/04-workflow/iteration-methodology.md) |
| Current focus / blockers / next | [NOW.md](docs/04-workflow/NOW.md) |
| Machine-readable doc index | [llms.txt](llms.txt) |
| Round close-out (skill) | `$iteration-close-loop` |
| One-click install (skill) | `$vibe-coding-install` |
