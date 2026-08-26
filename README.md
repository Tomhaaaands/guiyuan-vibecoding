# _bootstrap

> Turn an empty folder into a production-ready single-agent project in one guided conversation.

_bootstrap_ is an open-source **iteration-management bootstrap kit for AI-driven development**.
It packages a battle-tested methodology (born from the Creator OS project) into installable
skills, a reusable project template, and deterministic tooling — so any new project starts with
the same discipline: single source of truth, traceable rounds, and gates that live in scripts
instead of prompts.

## Features

- **Guided conversational scaffold** — the first conversation walks you through: project folder &
  name → business modules (or a recommended default template: web/api/db/worker/tests) → Python
  runtime (reuse your existing Python, or auto-install) → dependency policy (share existing deps,
  or create a project-local `.venv`).
- **Iteration close-loop skill** — one-line changelog rows, archive round files, NOW state cards,
  doc sync, drift checks. Every round is traceable; red lines and pitfalls stay visible, never archived.
- **Token-efficient by design** — AGENTS.md is a thin startup contract (routing table + constraints +
  index); heavy docs load on demand (`hydrate`), a machine-readable index (`llms.txt`) points agents
  where to look, and one-shot skills are explicit-only (`$project-bootstrap`).
- **Deterministic gates** — `check_drift` flags stale markers and broken links; structure checks are
  enforced by scripts, not by "rules the LLM must remember".
- **Git-ready** — module placeholder dirs, `.gitignore`, `git init`, and a ready commit command.

## Quick start

```bash
# 1. Get the kit
git clone <your-repo-url> _bootstrap
cd _bootstrap

# 2. Install the skills for Codex (or adjust the destination for other agents)
python tools/install_skills.py

# 3. Open a NEW empty project folder, start a new conversation, and invoke:
$project-bootstrap
```

Answer the guided questions. The skill scaffolds the project, installs `iteration-close-loop`
if it's missing, and tells you to open a new conversation for your first real task.

> Note: `project-bootstrap` is explicit-only by design — it never auto-triggers, so installed
> skills don't add per-conversation matching noise.

## CLI reference

```bash
python skills/project-bootstrap/scripts/bootstrap.py <folder> --name <project> \
    [--template default] \
    [--module "name=keywords"] [--code "name=dir"] \
    [--python auto|system|install|<path>] [--env auto|shared|isolated|reuse|skip] \
    [--force] [--no-venv] [--no-install-skill]
```

| Tool | Purpose |
| --- | --- |
| `tools/install_skills.py` | Install skills into `$CODEX_HOME/skills` |
| `tools/rollup_round.py` | Create an archive round file + insert the changelog row |
| `tools/hydrate.py` | Keyword-retrieve relevant docs (progressive disclosure) |
| `tools/check_drift.py` | Scan stale markers (hard/soft) + validate `llms.txt` links |
| `tools/gen_llms_txt.py` | Generate the root `llms.txt` doc index |

## Why not just use spec-kit / OpenSpec / superpowers?

| Project | Approach | Our differentiator |
| --- | --- | --- |
| github/spec-kit (131k★) | Constitution + specify/plan/tasks/converge | Red lines & pitfalls stay resident and visible per round |
| Fission-AI/OpenSpec (66k★) | propose → apply → archive change folders | Same loop, plus a three-layer record model and deterministic gates |
| obra/superpowers (278k★) | Skills loaded on demand | Same progressive disclosure, plus guided bootstrap + project skeleton |

_bootstrap_ is smaller, conversation-first, and opinionated about record-keeping — built for one
operator (or a few agents) who want traceability without ceremony.

## Project layout

```text
_bootstrap/
├── README.md
├── LICENSE
├── CHANGELOG.md                 # one-line round ledger
├── AGENTS.md                    # startup contract for this repo itself
├── llms.txt                     # machine-readable doc index (generated)
├── docs/
│   └── iteration-methodology.md # the full reusable methodology
├── skills/
│   ├── iteration-close-loop/    # round close-out skill
│   └── project-bootstrap/       # guided scaffold skill (assets = project template)
├── templates/
│   └── iteration-methodology/   # skeleton copied into new projects
└── tools/                       # deterministic helpers (all cross-platform Python)
```

## Docs

- [docs/iteration-methodology.md](docs/iteration-methodology.md) — seven core principles, the
  five-layer doc system, two workflows, the three-layer record model, goal-locking, output rules,
  token-saving design, and a migration guide (minimal set → standard set → full set).

## License

MIT © 2026 Tomhands
