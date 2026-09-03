# Common Agent Hook Methods

VibeCoding_Manager defaults to a **project-scoped Codex `SessionStart` advisory hook**. This file is
the local reference for the common Agent hook setups, so the installing agent can read the exact
method from disk instead of searching the web each time.

## Shared constraints

Project-scoped hooks only load for a **trusted** project. They do not affect user/global config,
chat-only sessions, or other projects. To set a strict (deny) gate, use a tool-use or commit hook
and enable it explicitly; a `SessionStart` hook can only add context.

## Codex

File: `<project>/.codex/hooks.json` (or inline `[hooks]` in `.codex/config.toml`). The project must be
trusted and the user-level `[features].hooks` (older `codex_hooks`) flag enabled.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {"type": "command", "command": "\"python\" \"tools/vcm_session_hook.py\"", "timeout": 20}
        ]
      }
    ]
  }
}
```

Events: `SessionStart`, `PreToolUse`, `PostToolUse`, `PermissionRequest`, `PreCommit`, `Stop`.
`SessionStart` returns `hookSpecificOutput.additionalContext`; tool-use and commit hooks can return a
`decision` to allow/deny.

## Claude Code

File: `<project>/.claude/settings.json` with a `hooks` table, plus optional rules in
`<project>/.claude/rules` or `CLAUDE.md`. Events include `PreToolUse`, `PostToolUse`, `Stop`,
`SubagentStop`. A hook returns `{hookSpecificOutput: {decision: "approve"|"block"}}` for tool-use events.

## Cursor

File: `<project>/.cursor/rules` or `<project>/.cursorrules` (rules only, not lifecycle events). Useful
for project conventions, not for blocking tool calls.

## Git (hard gate)

File: `<project>/.git/hooks/pre-commit`. This blocks bad commits regardless of the agent. VCM also
installs this during scaffold so the project gates run before commit.

## VCM default (soft)

`SessionStart` advisory that detects `managed` / `vcm-shaped` / `coding` / `ambiguous` and asks for
intent on empty folders. Changing this to a strict deny gate is a deliberate product choice, not the
default.
