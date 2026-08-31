# VibeCoding_Manager Agent Rules (mandatory · startup contract + index)

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

## 1. Module routing table (keywords → docs → code)

| Keywords | Required reading | Code |
| --- | --- | --- |
| guided bootstrap / scaffold / one-click deploy | [skills/vibe-coding-manager/SKILL.md](skills/vibe-coding-manager/SKILL.md) | `skills/vibe-coding-manager/` |
| iteration close-out / changelog / archive / round wrap-up | [skills/iteration-close-loop/SKILL.md](skills/iteration-close-loop/SKILL.md) | `skills/iteration-close-loop/` |
| project template / skeleton | `templates/iteration-methodology/README.md` | `templates/iteration-methodology/` |
| project-type profiles / presets / dimensions | `skills/vibe-coding-manager/profiles/README.md` | `skills/vibe-coding-manager/profiles/` |
| tooling / gates / retrieval / index | `tools/*.py` (their docstrings) | `tools/` |
| methodology / principles / migration guide | [docs/iteration-methodology.md](docs/iteration-methodology.md) | `docs/` |
| fact ownership / which manager / boundary | [docs/fact-ownership.md](docs/fact-ownership.md) | `docs/` |
| product north star / MVP / scope | [docs/product-spec.md](docs/product-spec.md) | `docs/` |
| manager state machine / orchestration / self-iteration | [docs/manager-architecture.md](docs/manager-architecture.md) | `docs/` |
| artifacts / context builder / progressive disclosure | [docs/artifact-context-contract.md](docs/artifact-context-contract.md) | `docs/` |
| token budget / context cost / model routing | [docs/token-budget.md](docs/token-budget.md) | `docs/` |
| roadmap / delivery order / acceptance | [docs/roadmap.md](docs/roadmap.md) | `docs/` |

## 2. Documentation discipline (non-negotiable)

- **Same-round closure**: every change updates CHANGELOG (one row) plus affected docs in the same round;
- **Sync rule**: `templates/iteration-methodology/` and `skills/vibe-coding-manager/assets/project/`
  must stay identical (edit both when the template changes);
- No full rewrites of unrelated docs; no stale "TBD / not-synced" markers left for this change;
- Tool changes must be tested (run once in a temp dir); `python tools/check_drift.py` must pass before commit.

## 3. Technical constraints (cheat sheet)

- Pure Python 3.11+ (tomllib for profiles), standard library only; UTF-8;
- Paths resolve relative to the repo root (find README.md upward); no hardcoded absolute paths;
- After doc-structure changes regenerate `llms.txt`: `python tools/gen_llms_txt.py --name "VibeCoding_Manager"`.

## 4. Index pointers

| Looking for | Read |
| --- | --- |
| Quick start / usage | [README.md](README.md) |
| Current focus / blockers / next | [NOW.md](NOW.md) |
| Product contract | [docs/product-spec.md](docs/product-spec.md) |
| Manager architecture | [docs/manager-architecture.md](docs/manager-architecture.md) |
| Artifact + context contract | [docs/artifact-context-contract.md](docs/artifact-context-contract.md) |
| Token budget | [docs/token-budget.md](docs/token-budget.md) |
| Product roadmap | [docs/roadmap.md](docs/roadmap.md) |
| Full methodology | [docs/iteration-methodology.md](docs/iteration-methodology.md) |
| Fact ownership boundary (vs Private_butler) | [docs/fact-ownership.md](docs/fact-ownership.md) |
| Iteration progress | [CHANGELOG.md](CHANGELOG.md) |
| Machine-readable doc index | [llms.txt](llms.txt) |
