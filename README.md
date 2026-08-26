# _bootstrap

> Turn an empty folder into a production-ready single-agent project in one guided conversation.
> 一键把空文件夹搭建成可直接投产的单 Agent 工程（引导式问答 + 迭代闭环）。

_bootstrap_ is an open-source **iteration-management bootstrap kit for AI-driven development**.
It packages a battle-tested methodology (born from the Creator OS project, rounds R102–R109)
into installable skills, a reusable project template, and deterministic tooling — so any new
project starts with the same discipline: single source of truth, traceable rounds, and gates
that live in scripts instead of prompts.

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

# 2. Install the skills for Codex (or Claude Code's skills dir, adjust if needed)
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
    [--module "名称=关键词1,关键词2"] [--code "名称=代码目录"] \
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
| github/spec-kit (131k★) | Constitution + specify/plan/tasks/converge | We keep red lines & pitfalls resident and visible per round |
| Fission-AI/OpenSpec (66k★) | propose → apply → archive change folders | Same loop, plus a three-layer record model (ledger / state card / archive) and deterministic gates |
| obra/superpowers (278k★) | Skills loaded on demand | Same progressive-disclosure idea; ours ships a guided bootstrap + project skeleton |

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

---

## 中文简介

_bootstrap_ 是一套面向 AI 主导开发的**迭代管理引导套件**：把"空文件夹 → 可投产单 Agent 工程"
变成一次引导式对话。核心三件：

1. **引导式部署**（`$project-bootstrap`，显式触发）：问项目名/文件夹 → 选业务模块或默认模板 →
   复用你已有的 Python（没有则自动装）→ 依赖能共用就共用、不能就项目内建 `.venv` → 生成
   README/AGENTS/docs 骨架/工具链/.gitignore → git init，可直接提交；
2. **迭代闭环**（`iteration-close-loop`）：每轮一行台账 + 档案分卷 + NOW 状态卡 + 文档同步 +
   漂移检查，红线/坑位常驻可见；
3. **省 token 设计**：AGENTS.md 只做启动契约+索引，其余按需检索（hydrate / llms.txt），
   一次性技能全部显式触发，不参与自动匹配。

使用：克隆本仓库 → `python tools/install_skills.py` → 新项目第一条对话输入 `$project-bootstrap`。
