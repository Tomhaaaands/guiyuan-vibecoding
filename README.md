# _bootstrap

> Turn an empty folder into a production-ready single-agent project in one guided conversation.
> One scaffold. One loop. Zero context rot.

_bootstrap_ is an open-source **iteration-management bootstrap kit for AI-driven development**:
installable skills + a reusable project template + deterministic tooling, so every new project
starts with the same discipline — single source of truth, traceable rounds, and gates that live
in scripts instead of prompts.

## The problem

AI-driven development is fast — and messy. If any of these sound familiar, you've felt it:

- **Context rot** — every new conversation starts from zero. Decisions, constraints, and the
  "why" live in chat history that disappears the moment you open a new thread.
- **Document drift** — docs go stale the day they're written. "Why is this code like this"
  becomes unanswerable, and nobody updates anything because the process costs more than the code.
- **Prompt bloat** — AGENTS.md/CLAUDE.md grows into a manual nobody reads. Every session pays
  tokens for rules the agent ignores.
- **Discipline vacuum** — "rules the LLM must remember" don't hold. There are no gates, no red
  lines, no trace — just vibes.
- **Bootstrap tax** — every new project rebuilds the same skeleton by hand: folder structure,
  AGENTS.md, environment, git. Hours of setup before the first real task.
- **Round-trip amnesia** — after a round of changes there's no record of what changed, why, and
  how it was verified. Next week's "fix" is this week's mystery.

## Who this is for

- **AI-native solo developers & indie hackers** shipping with Codex / Claude Code across many
  small projects, who want each project to start clean and stay traceable without a PMO.
- **Small agent-driven teams (1-5 people)** who want "docs as truth" with a process lighter than
  the code itself — one-line ledgers, not sprint ceremonies.
- **Builders who iterate in rounds** and need to answer "what did we change and why" weeks later,
  from files, not chat history.

Not for you? If you run a large org with compliance teams, 30+ tool integrations, or need a
spec-driven process spanning every assistant on the market — spec-kit and OpenSpec are the
heavier, more general tools; this kit deliberately isn't.

## Why _bootstrap (differentiators)

1. **Conversation-first, not command-first** — a guided Q&A deploys the full project (modules,
   routing, red-line stubs, environment, git) in one session. No CLI incantations to learn.
2. **Deterministic gates, not prompt rules** — structure and drift checks are scripts. Red lines
   and pitfalls stay **resident and visible every round**; they never disappear into an archive.
3. **Three-layer record model** — one-line ledger + module state cards + full archive. Daily cost
   is ~1-2k tokens; complete history is one link away, read only when needed.
4. **Token-efficient by default** — AGENTS.md is a thin startup contract; heavy docs load on
   demand; one-shot skills are explicit-only, so installed skills add zero per-conversation noise.
5. **Env-aware and git-ready** — reuses your existing Python (or auto-installs one), shares
   dependencies when possible and creates a project `.venv` when not, then `git init`s and prints
   the commit command.

## Features

- **Guided conversational scaffold** — folder/name → business modules (or a recommended default
  template: web/api/db/worker/tests) → Python runtime → dependency policy.
- **Iteration close-loop skill** — one-line changelog rows, archive round files, NOW state cards,
  doc sync, drift checks.
- **Reusable project template** — `templates/iteration-methodology/`: AGENTS.md skeleton, docs
  five-piece skeleton, four tools, `.gitignore`.
- **Project-type profiles** — built-in presets (`saas` / `c-end` / `vector-db` / `cli-tool`) and
  four composable dimensions (`deploy` / `data` / `runtime` / `surface`) inject per-type modules,
  red-line stubs, constraints, and doc placeholders; custom `.toml` profiles cover the long tail.
- **Five deterministic tools** — install skills, roll up rounds, hydrate docs, check drift,
  generate `llms.txt`.

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
    [--profile saas|c-end|vector-db|cli-tool|path/to/custom.toml] \
    [--dimension "deploy=saas" --dimension "data=vector-db"] \
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

## How we compare

| Project | Approach | Why _bootstrap instead |
| --- | --- | --- |
| github/spec-kit (131k★) | Constitution + specify/plan/tasks/converge, CLI + extension ecosystem | We're conversation-first, no CLI ceremony; red lines stay resident; three-layer records |
| Fission-AI/OpenSpec (66k★) | propose → apply → archive change folders, 30+ assistant support | Same loop spirit, plus guided bootstrap, deterministic gates, and explicit-only skills |
| obra/superpowers (278k★) | Skills loaded on demand | Same progressive disclosure; we add a guided scaffold + project skeleton + red-line residency |
| gsd-build/get-shit-done (64k★) | Meta-prompting + context engineering + hooks/SDK | We're doc-loop-focused and dependency-free (stdlib only) |

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
