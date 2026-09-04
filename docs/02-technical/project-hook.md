# Project-Scoped Agent Hook

## Purpose

Guiyuan Vibecoding can install a **project-scoped** Codex `SessionStart` hook that makes its
discipline visible without turning every session into a hard gate. The hook is advisory and
non-blocking: on session start it detects the project's state and injects a short directive into
the agent's developer context. It never writes to the project and never auto-takeover.

## Scope

The hook lives at `<project>/.codex/hooks.json` and only loads for a **trusted** project. It does not
affect user-level or global sessions, chat-only sessions, or projects without a project-level
`.codex/` layer. Codex requires the user-level `[features].hooks` (older `codex_hooks`) feature to be
enabled; that flag is user-scope and is intentionally not changed by this repo. When a project is
marked untrusted, Codex skips project-local hooks and rules while still loading user/system config.

For the exact setup of Codex, Claude Code, Cursor, and Git hooks, read the local reference
[agent-hook-methods.md](agent-hook-methods.md) instead of searching the web.

## Files

| File | Role |
| --- | --- |
| `tools/vcm_session_hook.py` | Portable stdlib runner; detects state and emits `SessionStart.additionalContext`. |
| `.codex/hooks.json` | Generated per project, wired to the runner via an absolute interpreter plus runner path. |
| `tools/install_project_hook.py` | Internal installer for an arbitrary project root. |
| `bootstrap.py::_install_project_hook` | Auto-installs the hook on adopt/scaffold. |

## States

`managed`: `.guiyuan-vibecoding/` present, so the project is formally adopted; the hook points at the
startup contract and the project gates.

`vcm-shaped`: the project carries the methodology skeleton (`AGENTS.md`/`NOW.md`/`CHANGELOG.md`/
`docs/04-workflow/`) but not `.guiyuan-vibecoding/`, so it is dogfooding rather than adopted.

`coding`: relevant dependency/source markers exist; the hook suggests an explicit assess-then-adopt
path without writing anything.

`ambiguous`: the folder is empty or notes-only; the hook asks the user to declare intent
(inspiration/notes vs coding project) and does not auto-takeover.

## Hard vs soft

The default is **soft/advisory** because a `SessionStart` hook only adds context; it cannot deny a
tool call. A strict deny-style gate would use a tool-use or commit hook and must be enabled
explicitly. This repo does not enable strict mode by default.

## Verify

```bash
python tools/install_project_hook.py <project-root>   # write/refresh .codex/hooks.json
python <project-root>/tools/vcm_session_hook.py --state
```

`selfqa.py` treats an absent project hook as a warning, not a failure, so an existing managed project
is not blocked until it opts in.

## Caveats

The hook command is pinned to the interpreter that ran the installer (or the project `.venv`). Re-run
`install_project_hook.py` after moving the project or changing the interpreter. The hook still
requires the project to be trusted by Codex and the user-level hook feature to be enabled.
