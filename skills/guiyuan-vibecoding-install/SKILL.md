---
name: guiyuan-vibecoding-install
description: Legacy compatibility installer documentation for the Guiyuan Vibecoding kit. The public entry point is now $guiyuan-vibecoding; install/update/uninstall/self-check are routed through that Skill and this source directory is not installed as a discoverable Skill.
---

# Guiyuan Vibecoding · 安装与更新（内部兼容文档）

> This directory is retained as repository-side compatibility material. New distributions expose
> only `guiyuan-vibecoding`; the lifecycle flow is routed from that public Skill.

Install, update, self-check, or redeploy the Guiyuan Vibecoding kit skills, or scaffold an existing
project folder with the iteration system. The published GitHub `v0.1.2` release includes the
installable zip; the convenience path is repo clone + `install.bat`/`install.sh`.

## Universal request protocol

For every requirement, optimization, or question—including install, update, preflight, and
uninstall—respond in this order: **semantic understanding -> recommended solution -> executable
plan**. Show only a concise, auditable summary; never expose hidden chain-of-thought. Destructive
uninstall is the default once the request is explicit, but it still removes only Guiyuan-owned
components and must report what was preserved.

## Installation

### From the repo (recommended)

```bash
git clone <your-repo-url> vibecoding_manager
cd vibecoding_manager
install.bat            # Windows
./install.sh           # macOS / Linux
```

### By message (self-hosted zip)

Build the zip with `python tools/build_dist.py --verify` (writes `dist/guiyuan-vibecoding-<version>.zip`
plus `.sha256` and a manifest), host it where you control it, then send a message:

```
请安装 Guiyuan Vibecoding Skill
技能地址：<URL of a separately hosted guiyuan-vibecoding-<version>.zip>
校验地址：<URL of the matching .sha256 sidecar>
```

The agent receiving the message must:

1. Download the zip from the 技能地址, verify its published `.sha256` companion file, and extract it.
2. Confirm the zip root contains exactly one public skill directory: `guiyuan-vibecoding/`.
3. Back up the existing `guiyuan-vibecoding/` directory, then copy the public skill into the
   **user-selected shared or agent skills directory**. Do not create global install or close-loop
   entries; those flows are routed internally by the public Skill.
   The directory may be used by Codex, Doubao, Harness, or another compatible agent.
4. Verify the public `SKILL.md`, optional `agents/openai.yaml` adapter, bundled
   `guiyuan-vibecoding/VERSION`, and internal close-loop template under `assets/internal/`.
5. Report the installed version, doctor result, and every unresolved item. If legacy directories
   or similar/other Skills were preserved, ask the user explicitly whether they want Guiyuan to
   handle them; never silently mark those items resolved. Remind the user: **记得在新对话中
   `@guiyuan-vibecoding`，进行一次初始化**。

Every hosted zip must carry a matching sidecar `.sha256`; never skip checksum verification. The
archive cannot contain its own whole-archive hash because adding that file would change the hash.
Publish the zip and its sidecar (and optionally the generated `.manifest.json`) together at the
same host. If the URL fails or returns a mismatched checksum, restore the backup. Gitee raw returned
`Access denied` in a browser test and is not an install source.

**Update**: resend the same message with the newer zip URL — verify the checksum, back up the old
public directory, replace it, then re-verify. If verification fails, restore the backup.

**No account authorization is needed** (unlike Quark); the "并授权账号" clause is not part of the
Guiyuan Vibecoding install message.

## Preflight, update, and uninstall

Run a read-only inventory before install/update when the target may contain an older kit:

```bash
python <this skill dir>/scripts/install.py --preflight [--skills-dir PATH]
```

The preflight reports current/legacy Guiyuan skills, an install manifest, and other Skills without
touching them. Similar Skills or products are always left in place and must be discussed with the
user; VCM never removes an unrelated Skill.

Uninstall has a safe default and needs no second confirmation:

```bash
python <this skill dir>/scripts/install.py --uninstall [--skills-dir PATH]
```

The same flow can be invoked in the Agent dialog with “卸载 Guiyuan Vibecoding” or an explicit
`$guiyuan-vibecoding-install` uninstall request; run the read-only preflight first, then execute
the removal without a second confirmation.

It removes only Guiyuan-owned Skill directories and manifest entries. It does not remove user data,
plugins, project files, Markdown project-management documents, or Butler MCP/configuration. If no
Guiyuan MCP registration exists, it performs no MCP operation. User-modified Guiyuan files are kept
and reported rather than deleted.

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
3. Report the outcome: which skills were installed/updated, doctor result, and every unresolved
   item. Ask explicitly about preserved legacy directories or similar/other Skills. When scaffolded,
   remind the user: **记得在新对话中 `@guiyuan-vibecoding`，进行一次初始化**。

## Rules

- Explicit-only: never auto-trigger on ordinary tasks; run only when invoked via `$guiyuan-vibecoding-install`.
- Primary zip install writes only into the user-selected skills directory; if the agent
  cannot resolve one, ask the user to choose: read-only discovery, an explicit shared directory,
  or project-local installation under `.guiyuan-vibecoding/skills/`. Scaffolding touches only the
  target folder.
- `--target` manages that folder via the installed guiyuan-vibecoding skill's `bootstrap.py`
  (pass-through also includes `--migration-plan/--migration-confirm/--migrate-code` for the
  two-phase full-takeover migration gate).
- Build the distributable zip with `python tools/build_dist.py --verify` in the repo.
