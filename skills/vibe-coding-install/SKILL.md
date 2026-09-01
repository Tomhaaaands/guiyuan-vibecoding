---
name: vibe-coding-install
description: One-click installer for the VibeCoding_Manager kit (coding-project manager, repo vibecoding_manager). Distributed as a single zip and installed by sending an agent a "技能地址" message; also installs/updates the iteration-close-loop and vibe-coding-manager skills into $CODEX_HOME/skills, runs a self-check, and can scaffold an existing project folder. Explicit-only: invoke with $vibe-coding-install.
---

# VibeCoding Manager · 安装与更新

Primary install is a one-message, one-zip flow (Quark-style). Use this skill for install, update,
self-check, or redeploy of the VibeCoding_Manager kit skills, or to scaffold an existing project
folder with the iteration system.

## Primary install — install by message (推荐)

The kit ships as one self-contained zip: `vibecoding-manager-<version>.zip`. The user installs it
by sending the agent a single message, e.g.:

```
请安装 VibeCoding_Manager Skill
技能地址：https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip
```

The agent receiving the message must:

1. Download the zip from the 技能地址, verify its published `.sha256` companion file, and extract it.
2. Confirm the zip root contains exactly three skill directories:
   `iteration-close-loop/`, `vibe-coding-manager/`, `vibe-coding-install/`.
3. Back up any existing same-named directories, then copy the three directories into the **current agent's global skills directory**
   (install 到全局 skills 目录，确保所有项目可用；不要装到项目级或临时目录).
4. Verify: each skill has `SKILL.md` + `agents/openai.yaml`; the bundled
   `vibe-coding-install/VERSION` matches the kit version printed in the zip name.
5. Report the installed version and that the kit is ready
   (a new project conversation can invoke `$vibe-coding-manager`).

GitHub is the authoritative source. If the user cannot reach GitHub, use the Gitee mirror:
`https://gitee.com/tomhands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip`.
The mirror must host the exact same zip and `.sha256`; never skip checksum verification.

**Update**: resend the same message with the newer zip URL — verify the checksum, back up the
three old directories, replace them, then re-verify. If verification fails, restore the backup.

**No account authorization is needed** (unlike Quark); the "并授权账号" clause is not part of the
VibeCoding_Manager install message.

## Secondary install — from a copy of the repo / inside Codex

Use when the user wants to install, update, self-check, or redeploy the skills from the repo, or
scaffold an existing project folder with the iteration system.

1. Confirm what the user wants:
   - install / update skills only, or
   - also scaffold a target project folder (ask for the folder; default: current directory).
2. Run the bundled installer (deterministic — do not re-type its steps):
   - `python <this skill dir>/scripts/install.py` — install/update skills + doctor;
   - add `--target <folder>` to also scaffold that project;
   - add `--force` to overwrite existing skill copies; `--no-doctor` skips the self-check.
3. Report the outcome: which skills were installed/updated, doctor result, and (when scaffolded)
   the project path plus next step — open a NEW conversation in that project.

## Rules

- Explicit-only: never auto-trigger on ordinary tasks; run only when invoked via `$vibe-coding-install`.
- Primary zip install writes only into the current agent's global skills directory; scaffolding
  touches only the target folder.
- `--target` manages that folder via the installed vibe-coding-manager skill's `bootstrap.py`
  (pass-through: `--name/--profile/--module/--dimension/--python/--env/--no-venv/--mode/--assessment/--workflow/--existing-system/--compat-policy/--system-policy/--deps/--github/--push`).
- Build the distributable zip with `python tools/build_dist.py --verify` in the repo.
