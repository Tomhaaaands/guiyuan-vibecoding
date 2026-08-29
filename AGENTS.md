# VibeCoding_Manager Agent Rules (mandatory · startup contract + index)

> Highest priority. This file holds only the required reading order, routing table, discipline,
> constraints, and index pointers; methodology lives in
> [docs/iteration-methodology.md](docs/iteration-methodology.md), progress in [CHANGELOG.md](CHANGELOG.md).

## 0. Before every task (read, in order)

1. Read [README.md](README.md) (what this project is and how to start);
2. Read the latest 1-3 rows of [CHANGELOG.md](CHANGELOG.md) (one-line ledger);
3. For methodology/workflow changes → read [docs/iteration-methodology.md](docs/iteration-methodology.md);
4. For skill changes → read the relevant SKILL.md via the routing table below.

## 1. Module routing table (keywords → docs → code)

| Keywords | Required reading | Code |
| --- | --- | --- |
| guided bootstrap / scaffold / one-click deploy | [skills/project-bootstrap/SKILL.md](skills/project-bootstrap/SKILL.md) | `skills/project-bootstrap/` |
| iteration close-out / changelog / archive / round wrap-up | [skills/iteration-close-loop/SKILL.md](skills/iteration-close-loop/SKILL.md) | `skills/iteration-close-loop/` |
| project template / skeleton | `templates/iteration-methodology/README.md` | `templates/iteration-methodology/` |
| project-type profiles / presets / dimensions | `skills/project-bootstrap/profiles/README.md` | `skills/project-bootstrap/profiles/` |
| tooling / gates / retrieval / index | `tools/*.py` (their docstrings) | `tools/` |
| methodology / principles / migration guide | [docs/iteration-methodology.md](docs/iteration-methodology.md) | `docs/` |
| fact ownership / which manager / boundary | [docs/fact-ownership.md](docs/fact-ownership.md) | `docs/` |

## 2. Documentation discipline (non-negotiable)

- **Same-round closure**: every change updates CHANGELOG (one row) plus affected docs in the same round;
- **Sync rule**: `templates/iteration-methodology/` and `skills/project-bootstrap/assets/project/`
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
| Full methodology | [docs/iteration-methodology.md](docs/iteration-methodology.md) |
| Fact ownership boundary (vs Private_butler) | [docs/fact-ownership.md](docs/fact-ownership.md) |
| Iteration progress | [CHANGELOG.md](CHANGELOG.md) |
| Machine-readable doc index | [llms.txt](llms.txt) |
