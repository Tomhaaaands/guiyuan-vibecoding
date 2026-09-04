# {{PROJECT_NAME}} Agent Rules (mandatory · startup contract + index)

> Highest priority. This file holds only the reading order, routing table, discipline,
> constraints, and index pointers; full process in
> [AGENTS_WORKFLOW](docs/04-workflow/AGENTS_WORKFLOW.md), methodology in
> [iteration-methodology](docs/04-workflow/iteration-methodology.md), current focus in [NOW](docs/04-workflow/NOW.md).

## 0. Before every task (minimum-context startup)

1. Read [NOW.md](docs/04-workflow/NOW.md) only (focus / blocker / next / authority pointers);
2. Read only the named module's relevant authority fields or exact spans per §1;
3. Read [AGENTS_WORKFLOW](docs/04-workflow/AGENTS_WORKFLOW.md) only for process/routing changes;
4. Read changelog/archive only for history, regression, or round close-out;
5. For interfaces, [api.md](docs/02-technical/api-gateway/api.md) is the sole authority when present.

Do not preload history, full methodology, or unrelated docs. Audit the startup package with
the context-budget tool; the hard management-context ceiling is 2,500 tokens.

## 0.1 Universal request protocol

Every new requirement, optimization, or question follows this visible response order:

1. semantic understanding (request type, goal, scope, constraints, unknowns);
2. recommended solution (alternatives and material trade-offs);
3. executable plan (steps, acceptance evidence, and user gates).

This is a concise reasoning summary, not hidden chain-of-thought. A question-only response may use a
one-line plan for the answer and verification path. Do not perform a material or destructive action
before its required user gate.

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
| Project status page | `status.html` (derived, static); rebuild `tools/render_project_home.py` and open the file directly (no local port listener) |
| Round close-out (skill/scripts) | `$guiyuan-iteration-close-loop` when the client supports it; otherwise read `.guiyuan-vibecoding/skills/guiyuan-iteration-close-loop/SKILL.md` and run `tools/rollup_round.py` |
| Kit install/update | `$guiyuan-vibecoding-install` when the client supports it; otherwise use the repo installer or project-local skill copy |
