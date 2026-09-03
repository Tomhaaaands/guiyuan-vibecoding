# VibeCoding_Manager

> 中文说明 / Chinese guide: [README.zh-CN.md](README.zh-CN.md)

> An autonomous R&D butler for vibecoding: tell it what you want to build; it turns intent into
> product/design/technical facts, executable tasks, verified code, traceable delivery, and reusable
> experience. The user makes product decisions — the butler carries the management burden.

VibeCoding_Manager (repo `vibecoding_manager`) is an open-source,
local-first **vibecoding R&D manager**. The shipped v0.1.0 foundation provides project adoption,
scaffolding, iteration records, deterministic gates, Git/GitHub setup, and the first pitfall
distillation path. The public version line is pre-1.0 (`0.1.x`); the earlier `v1.2.0` tag remains
as a historical development snapshot. The accepted vNext direction extends that foundation into a complete loop:
requirements analysis → authoritative artifacts → task planning → development/verification →
delivery → reflection and self-iteration.

Product contract: [docs/01-product/product-spec.md](docs/01-product/product-spec.md). Architecture and delivery plan:
[docs/00-system/manager-architecture.md](docs/00-system/manager-architecture.md) and [docs/01-product/roadmap.md](docs/01-product/roadmap.md).
The current independent-product baseline, including optional Private Butler inbox/result integration
and the single/multi-project management direction, is
[docs/01-product/product-baseline-v0.1.0.md](docs/01-product/product-baseline-v0.1.0.md).

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

1. **Conversation-first, not command-first** — tell it in one sentence what you want to build;
   a deterministic intent map resolves the profile, then one guided confirmation deploys the
   project (modules, routing, red-line stubs, environment, git) in one session.
2. **Deterministic gates, not prompt rules** — structure and drift checks are scripts. Red lines
   and pitfalls stay **resident and visible every round**; they never disappear into an archive.
3. **Three-layer record model** — one-line ledger + module state cards + full archive. History is
   addressable but never preloaded into normal work.
4. **Hard-budget context compiler** — zero-history startup, field/span retrieval, delta-only
   continuation, and a deterministic 1,800-token target / 2,500-token ceiling.
5. **Env-aware and git-ready** — recommends UV for multi-project Python work, reuses your existing
   Python or auto-installs one, creates a project `.venv`, then `git init`s and prints the commit
   command. No UV is still fine: standard `python -m venv` is the fallback.

## Features

- **Lossless guided adoption** — give it a local folder or a GitHub URL. Empty folder → scaffold
  a new project. Existing code → a read-only assessment first: the user chooses per workflow to
  keep the old authority, map it into the manager, or make the selected manager layer active.
  Baseline hashes, local backups, and receipts protect existing management files; business code is
  never touched.
- **Pre-install compatibility gate** — a read-only match score pauses on low match or an existing
  similar management system, then offers explicit choices: full takeover, scoped takeover,
  keep-and-map, defer, or abandon.
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
- **Twenty-five deterministic tools** — build the distributable zip, install skills (with `--doctor`
  self-check), one-click install, roll up rounds, hydrate docs (keyword + reserved semantic
  backend), check drift, sync payload copies, generate `llms.txt`, a typed authority-artifact
  store, a deterministic context compiler, a behavior-evaluation harness, labeled-analysis
  validation/scoring, an isolated provider registry with local fallback, an analysis
  orchestrator, an analysis-evaluation gate, a cross-artifact consistency check, an
  analysis-to-authority-artifact generator, a task graph dispatcher, a receipt loop, an
  experience-candidate loop, an end-to-end MVP walkthrough, and a working pitfalls→red-lines distillation
  (other directions stubbed).
- **Portable agent skills** — `$vibe-coding-install` (explicit-only) installs/updates reusable
  `SKILL.md` files in a user-selected shared or agent skills directory. Codex, Doubao, Harness,
  and compatible agents can use the same payload; `agents/openai.yaml` is only a Codex adapter.

## Quick start

### 1. Install from the repo (primary)

```bash
# 1. Get the kit
git clone <your-repo-url> vibecoding_manager
cd vibecoding_manager

# 2. One-click install (skills + self-check; add `--target <folder>` to scaffold a project)
install.bat            # Windows
./install.sh           # macOS / Linux
```

### 2. Install by message (archived)

The published GitHub `v0.1.0` release zip is retired. If you want the one-message flow, build the zip
yourself with `python tools/build_dist.py --verify` (writes `dist/vibecoding-manager-<version>.zip`
plus `.sha256` and a manifest), host it where you control it, then send that URL in a message. Verify
the `.sha256` companion before install; an update backs up existing skills and restores them if
verification fails. See [docs/03-reference/release-sources.md](docs/03-reference/release-sources.md).

### 3. Use it

Open your project folder (empty or existing), start a new conversation, and invoke:

```text
$vibe-coding-manager
```

Empty folder → describe what you want in one sentence; the manager resolves the profile, restates
it, and scaffolds. Existing code or a GitHub URL → it first produces a read-only workflow
assessment. You select `keep`, `map`, or `managed` for each workflow before anything is written.

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
    [--intent "one-sentence description"] [--dry-run] \
    [--module "name=keywords"] [--code "name=dir"] \
    [--profile saas|c-end|vector-db|cli-tool|content-site|ecommerce|admin-dashboard|bot|path/to/custom.toml] \
    [--dimension "deploy=saas" --dimension "data=vector-db"] \
    [--python auto|system|install|<path>] [--env auto|shared|isolated|reuse|skip] \
    [--skills-dir PATH] [--skill-location auto|project|global|skip] [--discover-skills] \
    [--force] [--no-venv] [--no-install-skill]
```

| Tool | Purpose |
| --- | --- |
| `tools/install_skills.py` | Install skills into `--skills-dir`, `VIBECODING_SKILLS_HOME`, or Codex fallback; `--discover` lists candidates read-only; `--doctor` self-checks the kit |
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
| `tools/artifact_store.py` | Typed authority-artifact store: content-addressed writes, revisioning, idempotency, integrity/reference validation |
| `tools/context_compiler.py` | Deterministic context compiler: L0/L1 views per phase, hard-budget degradation, delta continuation |
| `tools/behavior_harness.py` | Behavior-evaluation harness for the local core (store + compiler, plus analysis-label scoring) |
| `tools/analysis_labels.py` | Validate and score labeled analysis against ground-truth fixtures |
| `tools/analysis_provider.py` | Provider registry + config + deterministic local fallback (no core import) |
| `tools/analysis.py` | Analysis orchestrator: intent -> labeled `analysis` authority artifact (idempotent, degradable) |
| `tools/analysis_eval.py` | Score a provider against sentence-level gold fixtures (bge-m3 semantic default, optional char-bigram) and gate promotion by an aggregate F1 threshold (default 0.25) |
| `tools/artifact_consistency.py` | Cross-artifact consistency check: missing acceptance, state-without-receipt, supersedes gaps, accepted-but-superseded |
| `tools/artifact_generate.py` | Turn a labeled analysis artifact into draft product/decision authority artifacts |
| `tools/task_graph.py` | P4 task graph: dependency readiness, acceptance validation, and next-task dispatch |
| `tools/receipt_loop.py` | P5 loop: checks -> verdict -> receipts artifact -> task status -> project-state sync |
| `tools/experience_loop.py` | P6 loop: failed/blocked receipts -> draft `[AI-DRAFT]` experience candidates + shadow red-line evaluation |
| `tools/mvp_walkthrough.py` | P8 end-to-end MVP: analysis -> artifacts -> dispatch -> receipt -> reflection with budget gate |

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
├── VERSION                     # single source of the kit version (0.1.0)
├── CHANGELOG.md                # one-line round ledger
├── AGENTS.md                   # startup contract for this repo itself
├── llms.txt                    # machine-readable doc index (generated)
├── docs/
│   ├── 00-system/              # global architecture, boundaries, red lines
│   ├── 01-product/             # product contracts and roadmap
│   ├── 02-technical/           # runtime contracts and technical truth
│   ├── 03-reference/           # research, competitors, tutorials, environments
│   └── 04-workflow/             # NOW, ledger, methodology, archive
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
and the install skill bundles both skills (so `$vibe-coding-install` can install/update from any
Agent). Sources are the repo copies; payloads must stay identical — `tools/check_drift.py` gates
the 4 sync pairs plus the single-sourced version, and `tools/sync_copies.py` propagates source →
payload in one command:

```bash
python tools/sync_copies.py            # propagate (edit a source, then run this)
python tools/check_drift.py            # verify gates are green before committing
```

## Docs

- [docs/iteration-methodology.md](docs/iteration-methodology.md) — seven core principles, the
  five-layer doc system, two workflows, the three-layer record model, goal-locking, output rules,
  token-saving design, and a migration guide (minimal set → standard set → full set).
- [docs/02-technical/distillation.md](docs/02-technical/distillation.md) — the self-iteration distillation loop (four lift
  directions; the pitfalls direction is implemented).
- [docs/02-technical/provider-boundary.md](docs/02-technical/provider-boundary.md) — where a model backend may appear, how it
  is selected, degraded, idempotent, and gated by the analysis F1 threshold.

## License

MIT © 2026 Tomhands
