# VibeCoding_Manager

> An autonomous R&D butler for vibecoding: tell it what you want to build; it turns intent into
> product/design/technical facts, executable tasks, verified code, traceable delivery, and reusable
> experience. The user makes product decisions — the butler carries the management burden.

VibeCoding_Manager (repo `vibecoding_manager`) is an open-source,
local-first **vibecoding R&D manager**. The shipped v1.2 foundation provides project adoption,
scaffolding, iteration records, deterministic gates, Git/GitHub setup, and the first pitfall
distillation path. The accepted vNext direction extends that foundation into a complete loop:
requirements analysis → authoritative artifacts → task planning → development/verification →
delivery → reflection and self-iteration.

Product contract: [docs/product-spec.md](docs/product-spec.md). Architecture and delivery plan:
[docs/manager-architecture.md](docs/manager-architecture.md) and [docs/roadmap.md](docs/roadmap.md).

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

## Why VibeCoding_Manager (differentiators)

1. **Conversation-first, not command-first** — a guided Q&A deploys the full project (modules,
   routing, red-line stubs, environment, git) in one session. No CLI incantations to learn.
2. **Deterministic gates, not prompt rules** — structure and drift checks are scripts. Red lines
   and pitfalls stay **resident and visible every round**; they never disappear into an archive.
3. **Three-layer record model** — one-line ledger + module state cards + full archive. History is
   addressable but never preloaded into normal work.
4. **Hard-budget context compiler** — zero-history startup, field/span retrieval, delta-only
   continuation, and a deterministic 1,800-token target / 2,500-token ceiling.
5. **Env-aware and git-ready** — reuses your existing Python (or auto-installs one), shares
   dependencies when possible and creates a project `.venv` when not, then `git init`s and prints
   the commit command.

## Features

- **Lossless guided adoption** — give it a local folder or a GitHub URL. Empty folder → scaffold
  a new project. Existing code → a read-only assessment first: the user chooses per workflow to
  keep the old authority, map it into the manager, or make the selected manager layer active.
  Baseline hashes, local backups, and receipts protect existing management files; business code is
  never touched.
- **Upfront environment disclosure** — a read-only preflight shows what's installed, then every
  proposed install (Python, `.venv`, `npm install`) is announced in plain language with three
  choices: auto-install / commands-only / skip.
- **Iteration close-loop skill** — one-line changelog rows, archive round files, NOW state cards,
  doc sync, drift checks.
- **Reusable project template** — `templates/iteration-methodology/`: AGENTS.md skeleton, docs
  five-piece skeleton, deterministic retrieval/budget/drift tools, `.gitignore`.
- **Project-type profiles** — built-in presets (`saas` / `c-end` / `vector-db` / `cli-tool`) and
  four composable dimensions (`deploy` / `data` / `runtime` / `surface`) inject per-type modules,
  red-line stubs, constraints, and doc placeholders; custom `.toml` profiles cover the long tail.
- **Twelve deterministic tools** — build the distributable zip, install skills (with `--doctor`
  self-check), one-click install, roll up rounds, hydrate docs (keyword + reserved semantic
  backend), check drift, sync payload copies, generate `llms.txt`, and a working pitfalls→red-lines
  distillation (other directions stubbed).
- **Installable as a skill** — `$vibe-coding-install` (explicit-only) installs/updates the kit from
  inside Codex and can scaffold an existing project; `install.bat` / `install.sh` are the
  one-command entry outside Codex.

## Quick start

### 1. Install by message (primary, Quark-style)

The kit ships as one self-contained zip. Install it in any agent by sending a single message:

```text
请安装 VibeCoding_Manager Skill
技能地址：https://<host>/vibecoding-manager-1.2.0.zip
```

The agent downloads the zip, places the three skills (`iteration-close-loop`,
`vibe-coding-manager`, `vibe-coding-install`) into its global skills directory, and verifies.
No account authorization is needed for a public asset. Verify its `.sha256` companion file before
installation; an update backs up existing skills and restores them if verification fails.

Build the zip yourself with `python tools/build_dist.py --verify` (writes
`dist/vibecoding-manager-<version>.zip`), or use a published release zip.

### 2. Install from the repo (secondary)

```bash
# 1. Get the kit
git clone <your-repo-url> vibecoding_manager
cd vibecoding_manager

# 2. One-click install (skills + self-check; add `--target <folder>` to scaffold a project)
install.bat            # Windows
./install.sh           # macOS / Linux
```

### 3. Use it

Open your project folder (empty or existing), start a new conversation, and invoke:

```text
$vibe-coding-manager
```

Empty folder → it asks what you're building and scaffolds it. Existing code or a GitHub URL → it
first produces a read-only workflow assessment. You select `keep`, `map`, or `managed` for each
workflow before anything is written.

Already installed? Invoke `$vibe-coding-install` anytime to update the skills, run the doctor
self-check, or adopt/scaffold a project folder.

Answer the guided questions. The skill scaffolds new projects immediately; existing projects are
adopted only after a confirmed workflow plan. At milestone boundaries it offers a small,
evidence-backed optimization bundle and never applies it automatically.

> Note: `vibe-coding-manager` is explicit-only by design — it never auto-triggers, so installed
> skills don't add per-conversation matching noise.

## CLI reference

```bash
python skills/vibe-coding-manager/scripts/bootstrap.py <folder> --name <project> \
    [--template default] \
    [--module "name=keywords"] [--code "name=dir"] \
    [--profile saas|c-end|vector-db|cli-tool|path/to/custom.toml] \
    [--dimension "deploy=saas" --dimension "data=vector-db"] \
    [--python auto|system|install|<path>] [--env auto|shared|isolated|reuse|skip] \
    [--force] [--no-venv] [--no-install-skill]
```

| Tool | Purpose |
| --- | --- |
| `tools/install_skills.py` | Install skills into `$CODEX_HOME/skills`; `--doctor` self-checks the kit |
| `tools/one_click_install.py` | One-click install: skills + doctor + optional project scaffold (`install.bat` / `install.sh` wrappers) |
| `tools/rollup_round.py` | Create an archive round file + insert the changelog row |
| `tools/hydrate.py` | Keyword-retrieve relevant docs; reserved `--semantic` backend |
| `tools/context_budget.py` | Estimate selected context and block hard-ceiling regressions |
| `tools/distill.py` | Project-memory distillation (pitfalls → red-lines implemented; others stubbed) |
| `tools/check_drift.py` | Scan markers, links, startup budget, distribution-copy drift, and the version gate |
| `tools/sync_copies.py` | Propagate source-of-truth files to distribution payload copies (`--dry-run` preview) |
| `tools/build_dist.py` | Build the install-by-message zip plus SHA-256 and release manifest (`--verify` self-checks) |
| `tools/workflow_optimize.py` | Propose up to three receipt-backed workflow improvements; user confirmation required |
| `tools/check_package.py` | Scan tracked source and reachable history for token-like secrets before a public release |
| `tools/gen_llms_txt.py` | Generate the root `llms.txt` doc index |

## How we compare

| Project | Approach | Why VibeCoding_Manager instead |
| --- | --- | --- |
| github/spec-kit (131k★) | Constitution + specify/plan/tasks/converge, CLI + extension ecosystem | We're conversation-first, no CLI ceremony; red lines stay resident; three-layer records |
| Fission-AI/OpenSpec (66k★) | propose → apply → archive change folders, 30+ assistant support | Same loop spirit, plus guided bootstrap, deterministic gates, and explicit-only skills |
| obra/superpowers (278k★) | Skills loaded on demand | Same progressive disclosure; we add a guided scaffold + project skeleton + red-line residency |
| gsd-build/get-shit-done (64k★) | Meta-prompting + context engineering + hooks/SDK | We're doc-loop-focused and dependency-free (stdlib only) |

VibeCoding_Manager is smaller, conversation-first, and opinionated about record-keeping — built for one
operator (or a few agents) who want traceability without ceremony.

## Project layout

```text
vibecoding_manager/
├── README.md
├── LICENSE
├── VERSION                     # single source of the kit version (1.2.0)
├── CHANGELOG.md                # one-line round ledger
├── AGENTS.md                   # startup contract for this repo itself
├── llms.txt                    # machine-readable doc index (generated)
├── docs/
│   └── iteration-methodology.md # the full reusable methodology
├── skills/
│   ├── iteration-close-loop/   # round close-out skill (source)
│   ├── vibe-coding-manager/    # guided manager skill (source)
│   │   └── assets/
│   │       ├── project/        # project template payload (mirror of templates/)
│   │       └── skills/iteration-close-loop/  # close-loop payload for scaffolding
│   └── vibe-coding-install/    # self-contained installer
│       └── assets/skills/      # bundles both skills as deploy payloads
├── templates/
│   └── iteration-methodology/  # skeleton copied into new projects
└── tools/                      # deterministic helpers (all cross-platform Python)
```

## Distribution & sync

The kit ships several **self-contained payload copies**: the manager skill carries the project
template (`assets/project` ↔ `templates/`) and a close-loop copy (for scaffolding new projects),
and the install skill bundles both skills (so `$vibe-coding-install` can install/update from
inside Codex). Sources are the repo copies; payloads must stay identical — `tools/check_drift.py`
gates the 4 sync pairs plus the single-sourced version, and `tools/sync_copies.py` propagates
source → payload in one command:

```bash
python tools/sync_copies.py            # propagate (edit a source, then run this)
python tools/check_drift.py            # verify gates are green before committing
```

## Docs

- [docs/iteration-methodology.md](docs/iteration-methodology.md) — seven core principles, the
  five-layer doc system, two workflows, the three-layer record model, goal-locking, output rules,
  token-saving design, and a migration guide (minimal set → standard set → full set).
- [docs/distillation.md](docs/distillation.md) — the self-iteration distillation loop (four lift
  directions; the pitfalls direction is implemented).

## License

MIT © 2026 Tomhands
