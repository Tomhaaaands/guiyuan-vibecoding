---
name: guiyuan-vibecoding
description: Explicit-only skill (implicit auto-selection disabled). Invoke with $guiyuan-vibecoding to put any coding project — an existing script, plugin, page, or app — under local iteration management, or to scaffold a brand-new project in an empty folder. Guides target, state detection, environment preflight with upfront install disclosure, management shell, git/GitHub, and a plain-language closing report.
---

# Guiyuan Vibecoding (guided)

One skill, one conversation: whatever the user brings — a script, a plugin, a page, a full app,
or nothing but an empty folder — the outcome is the same: a locally managed project with the
iteration loop (AGENTS startup contract, changelog/archive/NOW, deterministic gates). The
generator is only the empty-folder path; **managing what already exists is the core.**

Conversation-first: speak the user's language and keep it plain. Zero-base users (e.g. just
started with Doubao / Workbuddy) may not know git, Python, Node, or `.venv` — never assume they
do. Explain anything they will need to understand, in one plain sentence.

## Universal request protocol (every user request)

Before answering or changing anything, use this compact sequence for new requirements, optimizations,
and questions alike:

1. **Semantic understanding** — classify the request, restate the goal, scope, constraints, and unknowns.
2. **Solution** — give the recommended approach, alternatives, and material trade-offs.
3. **Plan** — list the smallest executable steps, acceptance evidence, and any user decision gate.

Show a concise summary of the reasoning, never hidden chain-of-thought. For a question that needs no
file change, the plan can simply be “answer with evidence and a verification path”. Do not execute a
material or destructive action until its required user gate is satisfied.

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

- **Empty folder** (or only `.git`) → **scaffold path**. Ask one plain sentence: "What do you
  want to build?" Resolve it with `--intent "<description>"` against `profiles/intent-map.toml`;
  do not present a project-type menu. When confidence is high, restate the resolved profile in
  one sentence and proceed. When medium/low, ask one open clarifying question before choosing.
  Preset modules and dimensions come from the resolved profile. For an explicit topology, scaffold
  supports `python-service`, `web-app`, `monorepo`, `cli`, or `composite`, with `small|medium|large`
  scale and repeatable capability overlays (`rag`, `vector-db`, `worker`, `auth`, `admin`,
  `payments`, `content-pipeline`, `local-deploy`). The generated project records its resolved
  layout in `.guiyuan-vibecoding/project-manifest.toml` and its source in `template.lock.toml`.
- **Folder has code** → **assess path first**. Run the read-only assessment (fingerprints:
  `manifest.json` → plugin; `package.json` deps → page/app; `pyproject.toml`/`requirements.txt`
  → app/script; `index.html` → static page; a single root script file → script). It must not write
  files, install dependencies, change Git, or install Skills. Let the user choose each workflow:
  `keep` (old remains authoritative), `map` (old is indexed), or `managed` (only then add a layer).
  The same read-only pass also detects known management overlays and computes the match score used
  by the Stage 2 gate.
- **Markdown-managed / no Skill** → if `AGENTS.md`, `NOW.md`, `CHANGELOG.md`, and
  `docs/04-workflow/` already exist, treat the Markdown workflow as the user's existing manager.
  Do not force-install a Skill or rewrite those files; continue through the same `keep`, `map`, or
  `managed` adoption gate.

## Stage 2 · Confirm the gradual adoption plan

For an existing project, save `--mode assess --json` output outside the target folder. Read the
compatibility gate and pause before any adoption write:

- If match is low, present these choices and wait for one:
  1. **full-takeover** — take over all management workflows and archive legacy management
     overlays under `.guiyuan-vibecoding/pre-adoption/`; business code is still untouched.
  2. **takeover** — take over all management workflows without restructuring.
  3. **defer** — leave old content unchanged and record the intent for a later iteration.
  4. **abandon** — do not use Guiyuan Vibecoding in this project.
- If the project has an existing similar system, also ask whether it is external (Notion, Linear,
  Trello, etc.) when no local marker is visible, then present:
  1. **keep-map** — keep the old system authoritative and map it for retrieval.
  2. **auto-takeover** — attempt a scoped takeover with backups and a receipt.
  3. **abandon** — do not use Guiyuan Vibecoding in this project.

Pass the confirmed decisions with `--compat-policy` and `--system-policy`. Then ask for the user's
choices for `startup`, `state`, `ledger`, `methodology`, and `tooling`, or let the policy set them.
If both gates apply, keep the choices consistent: `full-takeover` cannot be combined with
`keep-map`.
Run `--mode adopt --assessment <json>` with `--workflow <name>=keep|map|managed` when fine-grained
control is needed. Missing choices are `keep`. The apply step verifies hashes, backs up selected
management files, and writes a receipt; it never modifies business code, installs dependencies,
initializes Git, or changes global Skills.

## Stage 3 · Environment preflight & disclosure (before any install)

Run the read-only preflight and show what's found (git / python / node / gh). UV is an optional
Python accelerator; if it is missing, say "UV makes Python environments faster and shares the
cache across projects; I recommend installing it" before asking for permission. Explain `.venv`
in one plain sentence. Then offer three choices:

1. **Auto-install (recommended)** — I install uv when useful, then Python/`.venv`/npm as needed
   (`--deps auto`);
2. **Commands only** — I print the exact commands and you run them later (`--deps commands`);
3. **Skip** — I only add the management layer, no installs (`--deps skip`).

Never install anything before this choice is made.

## Stage 4 · Execute

```bash
python <skill path>/scripts/bootstrap.py <folder> --name <project> --mode auto|assess|adopt|scaffold \
    [--intent "one-sentence description"] \
    [--existing-system NAME] [--compat-policy full-takeover|takeover|defer|abandon] \
    [--system-policy keep-map|auto-takeover|abandon] \
    [--profile script|plugin|page|saas|c-end|vector-db|cli-tool|content-site|ecommerce|admin-dashboard|bot|path/to.toml] \
    [--module web --module api ...] [--code "name=dir"] \
    [--template default|python-service|web-app|monorepo|cli|composite] \
    [--scale small|medium|large] [--capability rag --capability worker] \
    [--dimension "key=value"] [--python auto|system|install|<path>] \
    [--env auto|shared|isolated|reuse|skip] [--deps auto|commands|skip] \
    [--skills-dir PATH] [--skill-location auto|project|global|skip] \
    [--discover-skills] [--dry-run] \
    [--assessment <json>] [--workflow startup=keep|map|managed ...] \
    [--github <repo-url>] [--push]
```

- assess: existing code defaults here; use `--json` and save the output outside the target project;
- adopt: requires a fresh assessment plus confirmed workflow choices; it owns only `managed`
  workflow files and creates a local backup before replacing one;
- scaffold: artifact choice maps to `--profile script|plugin|page`; explicit topology templates
  select the physical code layout while profiles/overlays add constraints and document stubs;
- scaffold with `--intent`: semantic resolver picks the profile deterministically; use
  `--dry-run` to inspect the resolved plan before writing.
- scaffold also creates the topology-independent `.guiyuan-vibecoding/` machine layer and
  regenerates its registry/doc-tree index. Record user decisions at the REQ, PLAN, QA and RELEASE
  gates with `tools/anchor.py`; anchors preserve hashes and consent but do not replace human docs.
- close-loop skill: default is project-local `.guiyuan-vibecoding/skills/`; install to a global
  or shared directory only after the user selects `--skills-dir` or `VIBECODING_SKILLS_HOME`.
  `--discover-skills` lists known candidate roots read-only.
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
- Project type is resolved from free text + `profiles/intent-map.toml`; never show a preset menu.
- Business code is never overwritten; existing management files change only after a confirmed
  `managed` selection and a baseline-hash check;
- When the gate requires a decision, stop until the user chooses; `defer` and `abandon` mean no
  project management files are written;
- No installs before the Stage 3 disclosure choice; explain every install in plain language;
- Never write global Skills without an explicit user-chosen path; project-local is the fallback.
- After the closing report, stop asking business details and guide to a new conversation.
