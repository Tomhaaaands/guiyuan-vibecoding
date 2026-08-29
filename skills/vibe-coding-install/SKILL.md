---
name: vibe-coding-install
description: One-click installer for the VibeCoding_Manager kit (coding-project manager, repo project_bootstrap). Installs or updates the iteration-close-loop and project-bootstrap skills into $CODEX_HOME/skills, runs a self-check, and can scaffold an existing project folder. Explicit-only: invoke with $vibe-coding-install.
---

# VibeCoding Manager One-Click Install

Use when the user wants to install, update, self-check, or redeploy the VibeCoding_Manager kit skills,
or scaffold an existing project folder with the iteration system.

## Workflow

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
- Installation writes only to `$CODEX_HOME/skills`; scaffolding touches only the target folder.
- `--target` scaffolds via the installed project-bootstrap skill's `bootstrap.py`
  (pass-through: `--name/--profile/--module/--dimension/--python/--env/--no-venv`).
