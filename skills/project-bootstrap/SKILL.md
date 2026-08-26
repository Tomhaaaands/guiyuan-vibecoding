---
name: project-bootstrap
description: Explicit-only skill (implicit auto-selection disabled). Invoke with $project-bootstrap to run guided conversational bootstrap that turns an empty folder into a production-ready single-agent project, asking for folder and project name, offering default business modules or a recommended template, then generating README, AGENTS.md, docs skeleton, tooling, .venv and git, and auto-installing iteration-close-loop when missing.
---

# Project Bootstrap (guided)

This skill runs a guided Q&A flow. Once activated (only via explicit `$project-bootstrap`;
`allow_implicit_invocation=false`), no matter what the user's first message is, always start with
Stage 0 and do nothing else.

## Stage 0 · Opening (always first)

Reply (wording may vary, but must contain these three items):

> I'm your one-click project scaffolding assistant. I can turn an empty folder into a
> production-ready single-agent project.
> Please give me:
> 1. A project folder (default: current directory)
> 2. A project name

## Stage 1 · Choices

After the user replies, list default modules:

> Default modules (pick any, comma-separated):
> - web: frontend pages
> - api: backend endpoints
> - db: database
> - worker: async tasks/queue
> - tests: testing
> Or reply "default template" and I'll generate the recommended set
> (web + api + db + worker + tests, recommended).

Users may also describe custom modules (name/keywords/code dir) — record as-is, don't guess.

Then confirm the runtime (auto if unanswered):

> Python runtime (prefer reusing your existing one):
> - Auto (recommended): detect your installed Python (py launcher / PATH / uv) and reuse it
> - Install for me: auto-deploy when none found (uv python install or winget)
> - Specific path: give me the interpreter path
>
> Dependency policy:
> - Auto (recommended): reuse existing .venv; else create with uv (shared cache);
>   else project-local .venv
> - Share system packages: project .venv sees your Python's installed packages
> - Reuse only / Skip

## Stage 2 · Execute

```bash
python <skill path>/scripts/bootstrap.py <folder> --name <project> \
    [--template default | --module web --module api ...] [--code "name=dir"] \
    [--python auto|system|install|<path>] [--env auto|shared|isolated|reuse|skip]
```

- "default template" -> `--template default`;
- named modules -> `--module web` etc. (catalog supplies keywords & code dir);
- custom modules -> `--module "name=kw1,kw2" --code "name=dir"`;
- env choice -> `--python` / `--env` per the user's answer;
- non-empty target with AGENTS.md -> confirm `--force` first;
- no info at all -> current dir + dir name + default template.

The script: copies the skeleton (README / AGENTS.md / docs / tools / .gitignore) -> fills routing
tables -> replaces system placeholders -> creates module placeholder dirs -> writes the R1 archive ->
generates llms.txt -> resolves the Python runtime (reuses the user's by default) -> handles .venv
per policy -> git init -> installs iteration-close-loop if missing.

## Stage 3 · Verify

Run `tools/check_drift.py` in the target; hard markers must be 0; list remaining `{{placeholders}}`.

## Stage 4 · Closing (always say)

> Deployment complete ✅
> Generated the full skeleton: README, AGENTS.md startup contract, docs tree, ledger/archive/state
> cards, tooling, .venv, git repo (commit with: git add -A && git commit -m "chore: init").
> Open a new conversation and describe what you want to build, or which module to start with.

Add "Remaining placeholders: ..." if any.

## Rules

- Stage 0 always precedes everything; even a non-empty dir goes through the opening, with overwrite
  confirmation deferred to Stage 2;
- Deploy only user-confirmed modules; never guess names/keywords/code dirs;
- Idempotent: never overwrite existing files unless `--force`;
- After deployment, stop asking business details and guide to a new conversation (Stage 4).
