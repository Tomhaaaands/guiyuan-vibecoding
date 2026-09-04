# Guiyuan Vibecoding Agent Rules (mandatory · startup contract + index)

> Highest priority. This file holds only the required reading order, routing table, discipline,
> constraints, and index pointers; methodology lives in
> [docs/iteration-methodology.md](docs/iteration-methodology.md), progress in [CHANGELOG.md](CHANGELOG.md).

## 0. Before every task (minimum-context startup)

1. Read [NOW.md](NOW.md) only (current focus, blocker, next, and authority pointers);
2. Read only the routed authority needed for the named task (§1); use exact sections/spans;
3. Read [README.md](README.md) only for onboarding, usage, or product-positioning work;
4. Read [CHANGELOG.md](CHANGELOG.md) / archive only for history, regression, or round close-out;
5. Read the methodology only for workflow changes; read a SKILL.md only when that skill triggers.

Do not replay chat history or preload README, changelog, archives, full methodology, or unrelated
module docs. Startup context is budgeted by `python tools/context_budget.py`.

### Universal request protocol

Every new requirement, optimization, or question must be answered in this order:

1. semantic understanding (request type, goal, scope, constraints, unknowns);
2. recommended solution (alternatives and material trade-offs);
3. executable plan (steps, acceptance evidence, and user decision gates).

This is a concise, visible reasoning summary, not hidden chain-of-thought. Question-only requests may
use a one-line answer/verification plan.

## 1. Module routing table (keywords → docs → code)

| Keywords | Required reading | Code |
| --- | --- | --- |
| guided bootstrap / scaffold / one-click deploy | [skills/guiyuan-vibecoding/SKILL.md](skills/guiyuan-vibecoding/SKILL.md) | `skills/guiyuan-vibecoding/` |
| iteration close-out / changelog / archive / round wrap-up | [skills/guiyuan-iteration-close-loop/SKILL.md](skills/guiyuan-iteration-close-loop/SKILL.md) | `skills/guiyuan-iteration-close-loop/` |
| project template / skeleton | `templates/iteration-methodology/README.md` | `templates/iteration-methodology/` |
| registry / confirmation anchor / four gates | [docs/02-technical/project-registry-anchor-contract.md](docs/02-technical/project-registry-anchor-contract.md) | `tools/project_registry.py`, `tools/anchor.py` |
| project-type profiles / presets / dimensions | `skills/guiyuan-vibecoding/profiles/README.md` | `skills/guiyuan-vibecoding/profiles/` |
| template contract / topology / manifest / scale / capability overlay | [docs/02-technical/template-contract.md](docs/02-technical/template-contract.md), [skills/guiyuan-vibecoding/profiles/README.md](skills/guiyuan-vibecoding/profiles/README.md) | `skills/guiyuan-vibecoding/scripts/bootstrap.py`, `tools/project_manifest.py` |
| tooling / gates / retrieval / index | `tools/*.py` (their docstrings) | `tools/` |
| QA / testing / self-check | [docs/02-technical/qa-contract.md](docs/02-technical/qa-contract.md) | `tools/run_qa.py`, `tests/`, `tools/selfqa.py` |
| project hook / SessionStart / agent scope | [docs/02-technical/project-hook.md](docs/02-technical/project-hook.md), [docs/02-technical/agent-hook-methods.md](docs/02-technical/agent-hook-methods.md) | `tools/install_project_hook.py`, `tools/vcm_session_hook.py`, `.codex/hooks.json` |
| methodology / principles / migration guide | [docs/iteration-methodology.md](docs/iteration-methodology.md) | `docs/` |
| fact ownership / which manager / boundary | [docs/00-system/fact-ownership.md](docs/00-system/fact-ownership.md) | `docs/00-system/` |
| product north star / MVP / scope | [docs/01-product/product-spec.md](docs/01-product/product-spec.md) | `docs/01-product/` |
| manager state machine / orchestration / self-iteration | [docs/00-system/manager-architecture.md](docs/00-system/manager-architecture.md) | `docs/00-system/` |
| artifacts / context builder / progressive disclosure | [docs/02-technical/artifact-context-contract.md](docs/02-technical/artifact-context-contract.md) | `docs/02-technical/` |
| token budget / context cost / model routing | [docs/02-technical/token-budget.md](docs/02-technical/token-budget.md) | `docs/02-technical/` |
| roadmap / delivery order / acceptance | [docs/01-product/roadmap.md](docs/01-product/roadmap.md) | `docs/01-product/` |
| install / installer / scaffold | [docs/01-product/install/](docs/01-product/install/) + [docs/02-technical/packaging/](docs/02-technical/packaging/) | `skills/guiyuan-vibecoding-install/`, `skills/guiyuan-vibecoding/` |
| settings / admin UI | [docs/01-product/settings/](docs/01-product/settings/) + [docs/02-technical/frontend/](docs/02-technical/frontend/) | `skills/guiyuan-vibecoding/assets/frontend/admin/` |

## 2. Documentation discipline (non-negotiable)

- **Same-round closure**: every change updates CHANGELOG (one row) plus affected docs in the same round;
- **Roadmap is current**: accepted scope/status changes update `docs/01-product/roadmap.md` in the same round;
- **Sync rule**: `templates/iteration-methodology/` and `skills/guiyuan-vibecoding/assets/project/`
  must stay identical (edit both when the template changes);
- No full rewrites of unrelated docs; no stale "TBD / not-synced" markers left for this change;
- Tool changes must be tested (run once in a temp dir); `python tools/check_drift.py` must pass before commit.

## 3. Technical constraints (cheat sheet)

- Pure Python 3.11+ (tomllib for profiles), standard library only; UTF-8;
- Paths resolve relative to the repo root (find README.md upward); no hardcoded absolute paths;
- After doc-structure changes regenerate `llms.txt`: `python tools/gen_llms_txt.py --name "Guiyuan Vibecoding"`.

## 4. Index pointers

| Looking for | Read |
| --- | --- |
| Quick start / usage | [README.md](README.md) |
| Current focus / blockers / next | [NOW.md](NOW.md) |
| Product contract | [docs/01-product/product-spec.md](docs/01-product/product-spec.md) |
| Manager architecture | [docs/00-system/manager-architecture.md](docs/00-system/manager-architecture.md) |
| Artifact + context contract | [docs/02-technical/artifact-context-contract.md](docs/02-technical/artifact-context-contract.md) |
| Token budget | [docs/02-technical/token-budget.md](docs/02-technical/token-budget.md) |
| Product roadmap | [docs/01-product/roadmap.md](docs/01-product/roadmap.md) |
| Full methodology | [docs/iteration-methodology.md](docs/iteration-methodology.md) |
| Fact ownership boundary (vs Private_butler) | [docs/00-system/fact-ownership.md](docs/00-system/fact-ownership.md) |
| Iteration progress | [CHANGELOG.md](CHANGELOG.md) |
| Machine-readable doc index | [llms.txt](llms.txt) |
