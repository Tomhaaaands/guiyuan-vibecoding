---
name: vibe-coding-manager
description: Explicit-only skill (implicit auto-selection disabled). Invoke with $vibe-coding-manager to put any coding project — an existing script, plugin, page, or app — under local iteration management, or to scaffold a brand-new project in an empty folder. Guides target, state detection, environment preflight with upfront install disclosure, management shell, git/GitHub, and a plain-language closing report.
---

# Web Coding Manager (guided)

One skill, one conversation: whatever the user brings — a script, a plugin, a page, a full app,
or nothing but an empty folder — the outcome is the same: a locally managed project with the
iteration loop (AGENTS startup contract, changelog/archive/NOW, deterministic gates). The
generator is only the empty-folder path; **managing what already exists is the core.**

Conversation-first: speak the user's language and keep it plain. Zero-base users (e.g. just
started with Doubao / Workbuddy) may not know git, Python, Node, or `.venv` — never assume they
do. Explain anything they will need to understand, in one plain sentence.

## Stage 0 · Opening (always first)

Reply (wording may vary, but must contain these items):

> I'm your project's local manager. I can take any coding project — a script, a plugin, a page,
> or a full app — and set up local management for it **without touching your code**. If you have
> an empty folder, I can also create the project for you.
> Please give me:
> 1. Project location: a local folder, or a GitHub repository URL (default: current directory)
> 2. Project name (default: the folder name)

## Stage 1 · State detection

Check the target before asking anything else:

- **Empty folder** (or only `.git`) → **scaffold path**. First ask what they want to build:
  - script / plugin / page (map to `--profile script|plugin|page`)
  - full app → keep the existing questions: project type presets (saas / c-end / vector-db /
    cli-tool / custom dimensions) and modules (web / api / db / worker / tests, or the default
    template web+api+db+worker+tests)
- **Folder has code** → **assess path first**. Run the read-only assessment (fingerprints:
  `manifest.json` → plugin; `package.json` deps → page/app; `pyproject.toml`/`requirements.txt`
  → app/script; `index.html` → static page; a single root script file → script). It must not write
  files, install dependencies, change Git, or install Skills. Let the user choose each workflow:
  `keep` (old remains authoritative), `map` (old is indexed), or `managed` (only then add a layer).

## Stage 2 · Confirm the gradual adoption plan

For an existing project, save `--mode assess --json` output outside the target folder. Ask for
the user's choices for `startup`, `state`, `ledger`, `methodology`, and `tooling`, then run
`--mode adopt --assessment <json>` with `--workflow <name>=keep|map|managed`. Missing choices are
`keep`. The apply step verifies hashes, backs up selected management files, and writes a receipt;
it never modifies business code, installs dependencies, initializes Git, or changes global Skills.

## Stage 3 · Environment preflight & disclosure (before any install)

Run the read-only preflight and show what's found (git / python / node / uv / gh), then state in
plain language exactly what this project needs installed and why — e.g. ".venv is an isolated
environment that belongs only to this project and won't change anything else on your computer."
Then offer three choices:

1. **Auto-install (recommended)** — I run the installs now (`--deps auto`);
2. **Commands only** — I print the exact commands and you run them later (`--deps commands`);
3. **Skip** — I only add the management layer, no installs (`--deps skip`).

Never install anything before this choice is made.

## Stage 4 · Execute

```bash
python <skill path>/scripts/bootstrap.py <folder> --name <project> --mode auto|assess|adopt|scaffold \
    [--profile script|plugin|page|saas|c-end|vector-db|cli-tool|path/to.toml] \
    [--module web --module api ...] [--code "name=dir"] [--template default] \
    [--dimension "key=value"] [--python auto|system|install|<path>] \
    [--env auto|shared|isolated|reuse|skip] [--deps auto|commands|skip] \
    [--assessment <json>] [--workflow startup=keep|map|managed ...] \
    [--github <repo-url>] [--push]
```

- assess: existing code defaults here; use `--json` and save the output outside the target project;
- adopt: requires a fresh assessment plus confirmed workflow choices; it owns only `managed`
  workflow files and creates a local backup before replacing one;
- scaffold: artifact choice maps to `--profile script|plugin|page`; full app uses modules/presets;
- GitHub: if the user gave a repo URL or wants one, set origin with `--github <url>`, and push
  (`--push`) only after they have authenticated (`gh auth login` or git credentials) and confirmed.

The script: state detection -> read-only assessment -> confirmed, scoped adoption **or** full
scaffold -> dependency handling per the disclosure choice -> Git/GitHub only when requested ->
plain-language report. Scaffold retains the original full setup path.

## Stage 5 · Verify

For a selected tooling workflow, run `tools/check_drift.py`; hard markers must be 0. For a mapped
or kept workflow, report it without forcing the template over it.

## Stage 6 · Closing and gradual improvement

> Done ✅ Your project is under local management.
> - Detected: <type> — existing workflow choices were respected / skeleton created (scaffold)
> - Installed: ... (or: commands are printed above / nothing installed)
> - Git/GitHub: ...
> Next: open a new conversation here and start your first real task. Changelog, archive, and gates
> apply only to workflow layers the user selected.

At a milestone boundary, inspect a receipt with `tools/workflow_optimize.py`. Present at most
three evidence-backed suggestions as one optional bundle. The user may accept a subset or dismiss
a candidate; never apply a suggestion automatically or repeat a dismissed one.

## Rules

- Stage 0 always precedes everything; Stage 1 state detection decides assess vs scaffold;
- Deploy only user-confirmed modules; never guess names/keywords/code dirs;
- Business code is never overwritten; existing management files change only after a confirmed
  `managed` selection and a baseline-hash check;
- No installs before the Stage 3 disclosure choice; explain every install in plain language;
- After the closing report, stop asking business details and guide to a new conversation.
