---
name: vibe-coding-install
description: One-click installer for the VibeCoding_Manager kit (coding-project manager, repo vibecoding_manager). Installs/updates the iteration-close-loop and vibe-coding-manager skills into the current agent's global skills directory or an explicit --skills-dir, runs a self-check, and can scaffold an existing project folder. The published GitHub release zip is retired; install from the repo or a user-hosted zip. Explicit-only: invoke with $vibe-coding-install.
---

# VibeCoding Manager · 安装与更新

Install, update, self-check, or redeploy the VibeCoding_Manager kit skills, or scaffold an existing
project folder with the iteration system. The published GitHub `v0.1.0` release zip is retired
(archived); the convenience path is repo clone + `install.bat`/`install.sh`.

## Installation

### From the repo (recommended)

```bash
git clone <your-repo-url> vibecoding_manager
cd vibecoding_manager
install.bat            # Windows
./install.sh           # macOS / Linux
```

### By message (self-hosted zip)

Build the zip with `python tools/build_dist.py --verify` (writes `dist/vibecoding-manager-<version>.zip`
plus `.sha256` and a manifest), host it where you control it, then send a message:

```
请安装 VibeCoding_Manager Skill
技能地址：<URL of a separately hosted vibecoding-manager-<version>.zip>
```

The agent receiving the message must:

1. Download the zip from the 技能地址, verify its published `.sha256` companion file, and extract it.
2. Confirm the zip root contains exactly three skill directories:
   `iteration-close-loop/`, `vibe-coding-manager/`, `vibe-coding-install/`.
3. Back up any existing same-named directories, then copy the three directories into the **current agent's global skills directory**
   (install 到全局 skills 目录，确保所有项目可用；不要装到项目级或临时目录).
4. Verify: each skill has `SKILL.md`; `agents/openai.yaml` is an optional Codex adapter. Check
   the bundled `vibe-coding-install/VERSION` matches the kit version printed in the zip name.
5. Report the installed version and that the kit is ready
   (a new project conversation can invoke `$vibe-coding-manager`).

Every hosted zip must carry a matching `.sha256`; never skip checksum verification. If the URL fails or
returns a mismatched checksum, restore the backup. Gitee raw returned `Access denied` in a browser test
and is not an install source.

**Update**: resend the same message with the newer zip URL — verify the checksum, back up the
three old directories, replace them, then re-verify. If verification fails, restore the backup.

**No account authorization is needed** (unlike Quark); the "并授权账号" clause is not part of the
VibeCoding_Manager install message.

## Secondary install — from a copy of the repo

Use when the user wants to install, update, self-check, or redeploy the skills from the repo, or
scaffold an existing project folder with the iteration system.

1. Confirm what the user wants:
   - install / update skills only, or
   - also scaffold a target project folder (ask for the folder; default: current directory).
2. Run the bundled installer (deterministic — do not re-type its steps):
   - `python <this skill dir>/scripts/install.py [--skills-dir <path>]` — install/update skills + doctor;
   - `python <this skill dir>/scripts/install.py --discover` — list known agent skill roots
     read-only before choosing one;
   - add `--target <folder>` to also scaffold that project;
   - add `--force` to overwrite existing skill copies; `--no-doctor` skips the self-check.
3. Report the outcome: which skills were installed/updated, doctor result, and (when scaffolded)
   the project path plus next step — open a NEW conversation in that project.

## Rules

- Explicit-only: never auto-trigger on ordinary tasks; run only when invoked via `$vibe-coding-install`.
- Primary zip install writes only into the current agent's global skills directory; if the agent
  cannot resolve one, ask the user to choose: read-only discovery, an explicit shared directory,
  or project-local installation under `.vibecoding-manager/skills/`. Scaffolding touches only the
  target folder.
- `--target` manages that folder via the installed vibe-coding-manager skill's `bootstrap.py`
  (pass-through: `--name/--intent/--profile/--module/--dimension/--python/--env/--no-venv/--mode/--assessment/--workflow/--existing-system/--compat-policy/--system-policy/--deps/--github/--push/--skills-dir/--skill-location`).
- Build the distributable zip with `python tools/build_dist.py --verify` in the repo.
