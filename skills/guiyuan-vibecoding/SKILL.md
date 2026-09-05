---
name: guiyuan-vibecoding
description: Explicit-only Guiyuan Vibecoding entry point (implicit auto-selection disabled). Invoke with $guiyuan-vibecoding for project management, scaffolding, iteration close-out, or kit install/update/uninstall/self-check. The close-loop and install flows are internal modules routed through this skill, so only this public skill needs to be installed and discovered.
---

# Guiyuan Vibecoding (guided)

One skill, one conversation: whatever the user brings — a script, a plugin, a page, a full app,
or nothing but an empty folder — the outcome is the same: a locally managed project with the
iteration loop (AGENTS startup contract, changelog/archive/NOW, deterministic gates). The
generator is only the empty-folder path; **managing what already exists is the core.**

This is the only public Guiyuan Skill. Requests that used to target
`guiyuan-iteration-close-loop` or `guiyuan-vibecoding-install` are routed here explicitly; their
implementation payloads remain private so nested copies do not appear as duplicate Skills in an
Agent's discovery list.

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

Ask for the product intent before deciding whether the target should be scaffolded or adopted.
The project location and name are context defaults, not a separate confirmation ceremony:
mention them inline and let the user correct either one if needed. Do not infer a profile from
the folder before the user has described the product.

Reply (wording may vary, but must contain these items):

> I'm your project's local manager. I can take any coding project — a script, a plugin, a page,
> or a full app — and set up local management for it **without touching your code**. If you have
> an empty folder, I can also create the project for you.
> Please give me:
> 1. What do you want to build? (For example: "a WeChat mini-program that reminds me to drink water")
> 2. Project location and name are currently `<current folder>` / `<folder name>`; correct them only if needed.

If the user gives only “use the current folder/name”, ask the product question again. A missing
intent is a decision gate, not permission to choose `default` or another profile.

## Stage 1 · State detection

After the intent gate is answered, check the target:

- **Empty folder** (or only `.git`) → **scaffold path** after the intent gate. Resolve the user
  description with `--intent "<description>"` against `profiles/intent-map.toml`, but present the
  result as candidate templates and a proposed directory layout — never as an automatic choice.
  When medium/low, ask one open clarifying question before proposing candidates.
  Preset modules and dimensions come from the resolved profile. For an explicit topology, scaffold
  supports `python-service`, `web-app`, `monorepo`, `cli`, or `composite`, with `small|medium|large`
  scale and repeatable capability overlays (`rag`, `vector-db`, `worker`, `auth`, `admin`,
  `payments`, `content-pipeline`, `local-deploy`). The generated project records its resolved
  layout in `.guiyuan-vibecoding/project-manifest.toml` and its source in `template.lock.toml`.
- **Folder has code** → **assess path first**. Run the read-only assessment *with the user's intent*
  (fingerprints:
  `manifest.json` → plugin; `package.json` deps → page/app; `pyproject.toml`/`requirements.txt`
  → app/script; `index.html` → static page; a single root script file → script). It must not write
  files, install dependencies, change Git, or install Skills. Human output must show only the
  basic project facts, a likely project shape, candidate templates, and a functional-module
  directory; do not expose internal compatibility scores or tool-by-tool diagnostics. Let the user choose each workflow:
  `keep` (old remains authoritative), `map` (old is indexed), or `managed` (only then add a layer).
  The same read-only pass also detects known management overlays and computes the match score used
  by the Stage 2 gate.
  It also reports project size and likely data candidates. Small/medium projects may be suitable
  for full takeover; large projects should normally use partial or progressive adoption. This is a
  recommendation only, not an automatic decision.
- **Markdown-managed / no Skill** → if `AGENTS.md`, `NOW.md`, `CHANGELOG.md`, and
  `docs/04-workflow/` already exist, treat the Markdown workflow as the user's existing manager.
  Do not force-install a Skill or rewrite those files; continue through the same `keep`, `map`, or
  `managed` adoption gate.

## Stage 2 · Confirm the gradual adoption plan

For an existing project, save `--mode assess --intent "<description>" --json` output outside the
target folder. Pause before any adoption write and present four plain-language choices:

  1. **full-takeover** — use the user-confirmed template/layout, archive legacy management
     overlays under `.guiyuan-vibecoding/pre-adoption/`, generate an external migration plan,
     and migrate only after the user explicitly confirms that plan; never overwrite business code implicitly.
  2. **takeover** — take over management workflows without restructuring the existing code layout.
  3. **progressive adoption** — keep the old workflow authoritative for this iteration and start
     tracking new requirements in a parallel Guiyuan decision record.
  4. **abandon** — do not use Guiyuan Vibecoding in this project.

The CLI compatibility alias `defer` may still be accepted for old automation, but the user-facing
word is **progressive adoption**. If the user authorizes a machine inventory, run
`--mode assess --environment-scan` as a separate read-only step. It checks installed Agents,
shared Skill roots, available Python/Node environments, UV, and GitHub CLI metadata across the
computer; it never installs, switches, or edits anything.
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
control is needed. Missing choices are `keep`. Full takeover additionally requires an explicit
`--template` and external `--migration-plan`: the first run writes a read-only plan, while the
second run adds `--migration-confirm` to perform reversible data moves, conservative text-path
rewrites, template layout creation, and the `.guiyuan-vibecoding/takeover.json` completion marker.
Unknown data stays in place and ambiguous references are reported for manual review. The apply step
verifies hashes, backs up selected management files, and writes a receipt; it never silently
overwrites business code, installs dependencies, initializes Git, or changes global Skills.

## Stage 3 · Environment preflight & disclosure (before any install)

After the user has selected a candidate template, takeover mode, and authorized the inventory,
run the read-only preflight and show what's found (git / python / node / gh plus the whole-machine
inventory). UV is an optional
Python accelerator; if it is missing, say "UV makes Python environments faster and shares the
cache across projects; I recommend installing it" before asking for permission. Explain `.venv`
in one plain sentence. Then offer three choices:

1. **Auto-install (recommended)** — I install uv when useful, then Python/`.venv`/npm as needed
   (`--deps auto`);
2. **Commands only** — I print the exact commands and you run them later (`--deps commands`);
3. **Skip** — I only add the management layer, no installs (`--deps skip`).

Never install anything before this choice is made.

## Stage 4 · Execute

### Internal lifecycle routes

VCM keeps one discoverable Skill but separates implementation by responsibility. The workflow
router is the only orchestration layer; modules exchange artifact references and the stable `v1`
result envelope (`module_id`, `status`, `artifacts`, `evidence`, `blockers`, `next_action`).

| User request | Internal route | Responsibility |
| --- | --- | --- |
| install, update, doctor, preflight | `vcm_install` | lifecycle install, update and project hook |
| uninstall | `vcm_uninstall` | remove only manifest-owned VCM content |
| requirement, PRD, scope, acceptance | `vcm_requirement` | human + machine requirement analysis and artifacts |
| task breakdown, dependencies, next step, context | `vcm_planning` | dependency graph, readiness and context compilation |
| continue, repair, end-to-end execution | `vcm_workflow` | resume the nine-state machine and coordinate receipts |
| test, check, QA, regression | `vcm_qa` | unit/behavior/drift/package/architecture gates |
| commit, push, tag, GitHub Release | `vcm_release` | local dry-run preparation and release receipts |
| artifact/manifest/registry/anchor/budget primitives | `vcm_core` | shared authority and context primitives |

Requirement and planning are separate gates: a plan cannot invent missing acceptance or inputs.
Workflow cannot bypass requirement, planning, QA, or release gates. VCM deliberately has no design
route; a future `guiyuan-design` may consume the requirement-pack and plan through this seam and
return design assets or code suggestions, while VCM only validates the stable protocol.

- **Install/update/uninstall/self-check** — when the user asks to install, update, preflight,
  doctor, or uninstall Guiyuan, use the repository/package installer flow. Do not ask the user
  to install a second Skill or expose an `install` Skill entry.
- **Iteration close-out** — when the user asks to close or record a round, run the close-loop
  workflow described below. A project-local `guiyuan-iteration-close-loop/SKILL.md` is materialized
  only when the project chooses that workflow; it is not a global discovery entry.

```bash
python <skill path>/scripts/bootstrap.py <folder> --name <project> --mode auto|assess|adopt|scaffold \
    [--intent "one-sentence description"] [--environment-scan] \
    [--existing-system NAME] [--compat-policy full-takeover|takeover|progressive|abandon] \
    [--system-policy keep-map|auto-takeover|abandon] \
    [--migration-plan PATH] [--migration-confirm] [--migrate-code] \
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

- assess: existing code defaults here; pass the user's intent, optionally add
  `--environment-scan` only after explicit authorization, and save `--json` output outside the
  target project;
- adopt: requires a fresh assessment plus confirmed workflow choices; it owns only `managed`
  workflow files and creates a local backup before replacing one;
- scaffold: artifact choice maps to `--profile script|plugin|page`; explicit topology templates
  select the physical code layout while profiles/overlays add constraints and document stubs;
- scaffold with `--intent`: semantic resolver produces candidate profiles/templates for user
  confirmation; no `--profile`/`--template` means the command prints candidates and exits without
  writing. After the user chooses, pass the chosen option explicitly (use `--dry-run` to inspect
  the final proposed plan before writing).
- scaffold also creates the topology-independent `.guiyuan-vibecoding/` machine layer and
  regenerates its registry/doc-tree index. Record user decisions at the REQ, PLAN, QA and RELEASE
  gates with `tools/anchor.py`; anchors preserve hashes and consent but do not replace human docs.
- close-loop route: default is project-local `.guiyuan-vibecoding/skills/`; the legacy global
  location option is retained as a compatibility alias but never creates a second discoverable
  Skill. `--discover-skills` lists known candidate roots read-only.
- GitHub: if the user gave a repo URL or wants one, set origin with `--github <url>`, and push
  (`--push`) only after they have authenticated (`gh auth login` or git credentials) and confirmed.

The script: intent gate -> state detection -> read-only assessment -> confirmed, scoped adoption **or** full
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
> Next: 记得在新对话中 `@guiyuan-vibecoding`，进行一次初始化，再开始第一个真实任务。Changelog、
> archive 和 gates 只适用于用户选择的 workflow 层。

At a milestone boundary, inspect a receipt with `tools/workflow_optimize.py`. Present at most
three evidence-backed suggestions as one optional bundle. The user may accept a subset or dismiss
a candidate; never apply a suggestion automatically or repeat a dismissed one.

## Rules

- Stage 0 intent gate always precedes everything; Stage 1 state detection decides assess vs scaffold;
- Deploy only user-confirmed modules; never guess names/keywords/code dirs;
- Project type is resolved from free text + `profiles/intent-map.toml` only as a recommendation; never
  show a preset menu or silently choose a profile/topology for the user.
- Business code is never overwritten; existing management files change only after a confirmed
  `managed` selection and a baseline-hash check;
- When the gate requires a decision, stop until the user chooses; `progressive`/`defer` and `abandon` mean no
  project management files are written;
- No installs before the Stage 3 disclosure choice; explain every install in plain language;
- Never write global Skills without an explicit user-chosen path; project-local is the fallback.
- The closing report must list unresolved items and ask for explicit user decisions (for example,
  preserved legacy management directories or similar systems) before claiming completion.
- After the closing report, stop asking business details and guide to a new conversation.
