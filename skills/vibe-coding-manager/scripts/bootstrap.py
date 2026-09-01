#!/usr/bin/env python3
"""Put any coding project under local iteration management (manager-first).

Two entry paths, one outcome — a managed project with the iteration loop
(AGENTS startup contract / changelog + archive + NOW / deterministic gates):

  * scaffold:  empty folder -> generate the full skeleton (README, AGENTS.md,
               docs tree, tooling, .venv, git). The generator is the empty-folder
               default, not the core.
  * assess:    folder already has code -> inspect its workflow without writing
               files, installing dependencies, or touching Git.
  * adopt:     apply only workflow groups the user explicitly chose after an
               assessment. Existing files are hashed, backed up, and never deleted.

Usage:
  python bootstrap.py [target] --name "project" \
      [--mode auto|assess|adopt|scaffold] [--assessment FILE] \
      [--workflow startup|state|ledger|methodology|tooling=keep|map|managed] \
      [--existing-system NAME] [--compat-policy POLICY] [--system-policy POLICY] \
      [--profile script|plugin|page|saas|c-end|vector-db|cli-tool|path/to.toml] \
      [--module "name=kw1,kw2"] [--code "name=dir"] [--template default] \
      [--python auto|system|install|<path>] [--env auto|shared|isolated|reuse|skip] \
      [--deps auto|commands|skip] [--github <repo-url>] [--push] \
      [--force] [--no-venv] [--no-install-skill]

Default module catalog (used by --template default or bare --module names):
  web=apps/web · api=apps/api · db=data/db · worker=workers · tests=tests

Python runtime (--python, default auto):
  auto: detect the user's existing Python (py launcher -> PATH python -> uv python find)
        and reuse it; fall back to the current interpreter only if none is found
  system: same detection but no fallback; error if none found
  install: auto-deploy (prefer `uv python install 3.12`, else non-interactive winget install)
  explicit path: use that interpreter

Dependency policy (--env, default auto):
  auto: reuse an existing .venv; else `uv venv` (shared dependency cache);
        else project-local `python -m venv`
  shared: project .venv with --system-site-packages (sees the base Python's packages)
  isolated: clean project-local .venv (--no-venv equals skip; legacy create/uv map to isolated/auto)
  reuse: only reuse an existing .venv, never create
  skip: do nothing

Dependency disclosure (--deps, default auto) — always decided with the user BEFORE running:
  auto: run the installs (venv for Python projects, npm install for Node projects)
  commands: only print the exact commands; never run them
  skip: no dependency handling at all

GitHub (--github <url>): set the origin remote (never overwrites an existing origin).
--push: attempt `git push -u origin HEAD` (user must already be authenticated).

For an existing project, `auto` is intentionally read-only and prints an assessment.  Save
`--mode assess --json` output outside the project, then pass it back to `--mode adopt` with
the workflow choices the user confirmed.  Adopt never installs dependencies, initializes Git,
changes business code, or installs global Skills.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS = SKILL_ROOT / "assets" / "project"
SKILL_ASSETS = SKILL_ROOT / "assets" / "skills" / "iteration-close-loop"
FRONTEND_SKELETONS = {
    "web": SKILL_ROOT / "assets" / "frontend" / "web",
    "admin": SKILL_ROOT / "assets" / "frontend" / "admin",
}
PROFILES_DIR = SKILL_ROOT / "profiles"
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")
LIST_KEYS = ("modules", "red_lines", "constraints", "docs_stubs", "gitignore_add")
DEFAULT_MODULES = {
    "web": {"kw": "frontend,web", "code": "apps/web"},
    "api": {"kw": "backend,api", "code": "apps/api"},
    "db": {"kw": "database,schema", "code": "data/db"},
    "worker": {"kw": "async,queue", "code": "workers"},
    "tests": {"kw": "tests", "code": "tests"},
    "docs": {"kw": "docs", "code": "docs"},
}
# Template files that belong to a fresh skeleton, not to an existing project.
ADOPT_SKIP_TOP = {"README.md", "pyproject.toml"}
# Fingerprint -> artifact preset used by adopt mode (and available to scaffold mode).
DETECT_PROFILE = {"script": "script", "plugin": "plugin", "page": "page"}
DETECT_LABELS = {
    "script": "script / small tool",
    "plugin": "browser extension / plugin",
    "page": "web page / frontend app",
    "app": "application",
    "generic": "generic project",
}
ENV_TEMPLATES = {
    "script": ["API_KEY=", "BASE_URL="],
    "plugin": ["API_KEY=", "BASE_URL="],
    "page": ["NEXT_PUBLIC_API_BASE_URL=", "API_KEY="],
    "app": ["DATABASE_URL=", "SECRET_KEY=", "API_KEY=", "PORT=8000"],
    "generic": ["SECRET_KEY=", "API_KEY="],
}

# Existing projects are never converted in one step.  These groups are the only
# management surfaces VibeCoding_Manager can own; source code is deliberately
# not part of the map.
WORKFLOWS = ("startup", "state", "ledger", "methodology", "tooling")
ADOPTION_DIR = ".vibecoding-manager"
COMPAT_POLICIES = ("full-takeover", "takeover", "defer", "abandon")
SYSTEM_POLICIES = ("keep-map", "auto-takeover", "abandon")
KNOWN_SYSTEM_DEFS = (
    {
        "id": "spec-kit",
        "label": "Spec Kit / specification workflow",
        "markers": ("specs/", "specs.md", "specify.md", "spec-kit/"),
    },
    {
        "id": "openspec",
        "label": "OpenSpec",
        "markers": (".openspec/", "openspec/", "specs/change/"),
    },
    {
        "id": "superpowers",
        "label": "Superpowers / Claude skill set",
        "markers": (".claude/skills/", "superpowers/"),
    },
    {
        "id": "claude-code",
        "label": "Claude Code conventions",
        "markers": ("CLAUDE.md", ".claude/"),
    },
    {
        "id": "cursor",
        "label": "Cursor rules",
        "markers": (".cursor/", ".cursorrules"),
    },
    {
        "id": "project-bootstrap",
        "label": "Legacy project-bootstrap / VibeCoding_Manager workflow",
        "markers": (".vibecoding-manager/", "docs/04-workflow/", "AGENTS_WORKFLOW.md"),
    },
    {
        "id": "agent-rules",
        "label": "Agent rule file",
        "markers": ("AGENTS.md",),
    },
    {
        "id": "iteration-ledger",
        "label": "Iteration ledger / roadmap docs",
        "markers": ("CHANGELOG.md", "docs/roadmap.md"),
    },
)
FULL_TAKEOVER_OVERLAYS = {
    "CLAUDE.md",
    "CHANGELOG.md",
    ".cursorrules",
    ".cursor",
    ".claude",
    ".openspec",
    "specs",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _workflow_for(rel: Path) -> str | None:
    """Return the management workflow that owns a template-relative file."""
    text = rel.as_posix()
    if text == "AGENTS.md":
        return "startup"
    if text in {"NOW.md", "docs/04-workflow/NOW.md"}:
        return "state"
    if text in {"CHANGELOG.md", "docs/04-workflow/changelog.md"} or text.startswith("docs/04-workflow/archive/"):
        return "ledger"
    if text in {
        "docs/04-workflow/AGENTS_WORKFLOW.md",
        "docs/04-workflow/iteration-methodology.md",
        "docs/04-workflow/review-checklist.md",
        "docs/04-workflow/roadmap.md",
    }:
        return "methodology"
    if text == ".gitignore" or text.startswith("tools/") or text.startswith("scripts/"):
        return "tooling"
    return None


def _managed_candidates(root: Path) -> dict[str, list[dict[str, str]]]:
    """Inventory only workflow files, never user source code or dependencies."""
    out: dict[str, list[dict[str, str]]] = {name: [] for name in WORKFLOWS}
    for src in ASSETS.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(ASSETS)
        workflow = _workflow_for(rel)
        target = root / rel
        if workflow and target.is_file():
            out[workflow].append({"path": rel.as_posix(), "sha256": _sha256(target)})
    return out


def _detect_known_systems(root: Path) -> list[dict]:
    """Find local project-management overlays without touching them."""
    systems = []
    for definition in KNOWN_SYSTEM_DEFS:
        hits = [marker for marker in definition["markers"] if (root / marker).exists()]
        if hits:
            systems.append({
                "id": definition["id"],
                "label": definition["label"],
                "markers": hits,
            })
    return systems


def _declared_systems(values: list[str]) -> list[dict]:
    """Normalize user-declared systems (e.g. Notion, Linear) for the gate."""
    systems = []
    seen: set[str] = set()
    for raw in values:
        label = raw.strip()
        if not label or label.casefold() in seen:
            continue
        seen.add(label.casefold())
        systems.append({
            "id": re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-") or "declared",
            "label": label,
            "source": "declared",
            "markers": [],
        })
    return systems


def _compat_assessment(root: Path, groups: dict[str, list[dict]], known_systems: list[dict], declared_systems: list[dict]) -> dict:
    """Deterministic match score for manager vs the project's current management process."""
    matched = [name for name in WORKFLOWS if groups[name]]
    score = max(0, min(100, 30 + 12 * len(matched) - 15 * (len(known_systems) + len(declared_systems))))
    level = "low" if score < 60 else "medium" if score < 80 else "high"
    risks = [f"missing {name} management workflow" for name in WORKFLOWS if not groups[name]]
    risks.extend(f"existing system '{system['label']}' may already own management authority"
                 for system in known_systems + declared_systems)
    return {
        "score": score,
        "level": level,
        "dimensions": [{"name": name, "matched_files": len(groups[name])} for name in WORKFLOWS],
        "risks": risks,
        "systems_required": bool(known_systems or declared_systems),
        "policies": {
            "compatibility": {
                "required": level == "low",
                "options": list(COMPAT_POLICIES),
                "recommended": "takeover",
            },
            "systems": {
                "required": bool(known_systems or declared_systems),
                "options": list(SYSTEM_POLICIES),
                "recommended": "keep-map",
            },
        },
    }


def _assessment(root: Path, detected: dict, declared_systems: list[str] | None = None) -> dict:
    groups = _managed_candidates(root)
    known_systems = _detect_known_systems(root)
    declared = _declared_systems(declared_systems or [])
    return {
        "schema_version": 2,
        "target": str(root),
        "assessed_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "detected": detected,
        "known_systems": known_systems,
        "declared_systems": declared,
        "compatibility": _compat_assessment(root, groups, known_systems, declared),
        "workflows": [
            {
                "name": name,
                "existing_files": groups[name],
                "recommended": "map" if groups[name] else "keep",
            }
            for name in WORKFLOWS
        ],
    }


def _print_assessment(data: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    detected = data["detected"]
    compat = data["compatibility"]
    print("== lossless adoption assessment ==")
    print(f"  detected: {detected['label']} (runtime: {detected['runtime']})")
    print(f"  match: {compat['score']}/100 ({compat['level']})")
    for dim in compat["dimensions"]:
        print(f"  - {dim['name']}: {dim['matched_files']} existing manager file(s)")
    for risk in compat["risks"]:
        print(f"  risk: {risk}")
    if data["known_systems"]:
        for system in data["known_systems"]:
            print(f"  detected system: {system['label']} ({', '.join(system['markers'])})")
    if data["declared_systems"]:
        for system in data["declared_systems"]:
            print(f"  declared system: {system['label']}")
    if compat["policies"]["compatibility"]["required"]:
        print("  [gate] low match: choose --compat-policy full-takeover|takeover|defer|abandon")
    if compat["policies"]["systems"]["required"]:
        print("  [gate] existing systems: choose --system-policy keep-map|auto-takeover|abandon")
    print("  no project files, dependencies, Git settings, or skills were changed.")
    print("  choose each workflow: keep (old remains authoritative), map (old is indexed), or managed.")
    for item in data["workflows"]:
        files = item["existing_files"]
        summary = ", ".join(row["path"] for row in files[:3]) or "none found"
        suffix = " …" if len(files) > 3 else ""
        print(f"  - {item['name']}: {len(files)} existing file(s), recommend {item['recommended']} ({summary}{suffix})")
    print("  next: save this JSON outside the project, then run --mode adopt --assessment <file> with the confirmed policies.")


def _load_assessment(path: Path, target: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid assessment file: {path} ({exc})") from exc
    if data.get("schema_version") != 2 or data.get("target") != str(target):
        raise ValueError("assessment does not belong to this project or was created by an older version; rerun --mode assess")
    return data


def _validate_gate(assessment: dict, compat_policy: str | None, system_policy: str | None) -> None:
    compat = assessment.get("compatibility", {})
    if compat_policy in {"defer", "abandon"} or system_policy == "abandon":
        return
    if compat_policy == "full-takeover" and system_policy == "keep-map":
        raise ValueError("full-takeover conflicts with keep-map; choose auto-takeover for existing systems or takeover for scoped adoption")
    if compat.get("level") == "low" and not compat_policy:
        raise ValueError("compatibility gate: low match; choose --compat-policy full-takeover|takeover|defer|abandon")
    if compat.get("systems_required") and not system_policy:
        raise ValueError("similar-system gate: existing systems found; choose --system-policy keep-map|auto-takeover|abandon")
    if compat_policy and compat_policy not in COMPAT_POLICIES:
        raise ValueError(f"--compat-policy must be one of {'|'.join(COMPAT_POLICIES)}")
    if system_policy and system_policy not in SYSTEM_POLICIES:
        raise ValueError(f"--system-policy must be one of {'|'.join(SYSTEM_POLICIES)}")


def _write_deferred_decision(root: Path, assessment: dict, policy: str) -> Path:
    state_dir = root / ADOPTION_DIR / "decisions"
    state_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "schema_version": 2,
        "created_at": stamp,
        "policy": policy,
        "assessment": assessment,
    }
    path = state_dir / f"{policy}-{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _workflow_choices(values: list[str]) -> dict[str, str]:
    choices = {name: "keep" for name in WORKFLOWS}
    for value in values:
        name, sep, mode = value.partition("=")
        if not sep or name not in choices or mode not in {"keep", "map", "managed"}:
            raise ValueError("--workflow must be one of startup|state|ledger|methodology|tooling=keep|map|managed")
        choices[name] = mode
    return choices


def _verify_assessment(data: dict, root: Path) -> None:
    """Block application when an assessed file changed before the user confirmed it."""
    for workflow in data.get("workflows", []):
        for item in workflow.get("existing_files", []):
            path = root / item["path"]
            expected = item["sha256"]
            if not path.is_file() or _sha256(path) != expected:
                raise ValueError(f"baseline changed: {item['path']}; rerun --mode assess before applying")


def _adoption_receipt(root: Path, assessment: dict, choices: dict[str, str], backups: list[dict],
                      copied: list[str], policies: dict | None = None, moved: list[dict] | None = None) -> Path:
    state_dir = root / ADOPTION_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt = {
        "schema_version": 2,
        "created_at": stamp,
        "assessment": assessment,
        "policies": policies or {},
        "workflows": choices,
        "backups": backups,
        "copied": copied,
        "legacy_overlays": moved or [],
    }
    manifest = state_dir / "adoption.json"
    manifest.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt_dir = state_dir / "receipts"
    receipt_dir.mkdir(exist_ok=True)
    path = receipt_dir / f"adoption-{stamp}.json"
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _archive_legacy_overlays(root: Path, assessment: dict, stamp: str) -> list[dict]:
    """Move known management overlays out of the project root during full takeover."""
    pre_root = root / ADOPTION_DIR / "pre-adoption" / stamp
    moved: list[dict] = []
    seen: set[str] = set()
    for system in assessment.get("known_systems", []):
        for marker in system.get("markers", []):
            rel = Path(marker.rstrip("/"))
            key = rel.as_posix()
            if key not in FULL_TAKEOVER_OVERLAYS or key in seen:
                continue
            src = root / rel
            if not src.exists():
                continue
            dst = pre_root / "legacy" / rel
            if dst.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved.append({"path": key, "moved_to": dst.relative_to(root).as_posix()})
            seen.add(key)
    if moved:
        manifest = pre_root / "README.md"
        lines = [
            "# Pre-adoption archive",
            "",
            "Legacy management overlays moved from the project root during full takeover.",
            "",
            "Moved:",
            *[f"- {m['path']} -> {m['moved_to']}" for m in moved],
            "",
            "Backups and receipt: `.vibecoding-manager/backups/` + `.vibecoding-manager/adoption.json`.",
        ]
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return moved


def _apply_adoption(root: Path, name: str, assessment: dict, choices: dict[str, str],
                    policies: dict | None = None, full_takeover: bool = False) -> tuple[list[str], Path]:
    """Copy only explicitly managed workflow files, restoring backups on failure."""
    _verify_assessment(assessment, root)
    managed = {name for name, mode in choices.items() if mode == "managed"}
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = root / ADOPTION_DIR / "backups" / stamp
    backups: list[dict] = []
    copied: list[str] = []
    moved: list[dict] = []
    try:
        for src in sorted(ASSETS.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(ASSETS)
            workflow = _workflow_for(rel)
            if workflow not in managed:
                continue
            dst = root / rel
            existed = dst.exists()
            if existed:
                backup = backup_root / rel
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, backup)
                backups.append({"path": rel.as_posix(), "backup": backup.relative_to(root).as_posix()})
            else:
                backups.append({"path": rel.as_posix(), "backup": None})
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(rel.as_posix())

        copied_paths = [root / rel for rel in copied]
        _replace_placeholders(root, name, scope=copied_paths)
        if full_takeover:
            moved = _archive_legacy_overlays(root, assessment, stamp)
        # Do not generate an archive, index, Git hook, environment file, or dependency
        # side effect during adoption.  Those are separate workflow decisions.
        receipt = _adoption_receipt(root, assessment, choices, backups, copied, policies, moved)
        return copied, receipt
    except Exception:
        for item in reversed(moved):
            dst = root / item["moved_to"]
            original = root / item["path"]
            if dst.exists() and not original.exists():
                shutil.move(str(dst), str(original))
        for item in reversed(backups):
            dst = root / item["path"]
            if item["backup"]:
                src = root / item["backup"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            elif dst.exists():
                dst.unlink()
        raise


def _run_adopt(root: Path, name: str, assessment_path: Path | None, workflows: list[str],
               compat_policy: str | None = None, system_policy: str | None = None) -> None:
    if assessment_path is None:
        raise ValueError("adopt requires --assessment <json from --mode assess>")
    assessment = _load_assessment(assessment_path, root)
    _validate_gate(assessment, compat_policy, system_policy)
    if compat_policy in {"defer", "abandon"}:
        if compat_policy == "defer":
            decision = _write_deferred_decision(root, assessment, compat_policy)
            print(f"\nAdoption deferred: {root}")
            print(f"  old content was not changed; future adoption decision saved at {decision.relative_to(root).as_posix()}")
        else:
            print(f"\nAdoption abandoned: {root} (VibeCoding_Manager will not be used in this project)")
        return
    if system_policy == "abandon":
        print(f"\nAdoption abandoned: {root} (VibeCoding_Manager will not be used in this project)")
        return

    choices = _workflow_choices(workflows)
    if not workflows:
        choices = {name: "keep" for name in WORKFLOWS}
        compat_adopt = compat_policy in {"full-takeover", "takeover"}
        systems_required = assessment.get("compatibility", {}).get("systems_required")
        for item in assessment.get("workflows", []):
            name = item["name"]
            has_existing = bool(item.get("existing_files"))
            if systems_required and has_existing:
                if system_policy == "keep-map":
                    choices[name] = "map"
                elif system_policy == "auto-takeover":
                    choices[name] = "managed"
            elif compat_adopt:
                choices[name] = "managed"
    policies = {"compatibility": compat_policy, "systems": system_policy}
    copied, receipt = _apply_adoption(
        root,
        name,
        assessment,
        choices,
        policies=policies,
        full_takeover=compat_policy == "full-takeover",
    )
    print(f"\nLossless adoption complete: {root}")
    print("  workflows: " + ", ".join(f"{key}={value}" for key, value in choices.items()))
    print(f"  copied {len(copied)} explicitly managed file(s); source code was not touched")
    if compat_policy == "full-takeover":
        print("  full takeover: legacy management overlays archived under .vibecoding-manager/pre-adoption/")
    print(f"  receipt: {receipt.relative_to(root).as_posix()}")


def _replace_placeholders(root: Path, name: str, scope: list[Path] | None = None) -> list[str]:
    """Replace system placeholders; by default over all .md/.toml under root."""
    today = dt.date.today()
    mapping = {
        "{{PROJECT_NAME}}": name,
        "{{YYYY-MM-DD}}": today.isoformat(),
        "{{MM-DD}}": today.strftime("%m-%d"),
    }
    if scope is None:
        paths = [p for p in list(root.rglob("*.md")) + list(root.rglob("*.toml"))]
    else:
        paths = [p for p in scope if p.is_file() and p.suffix in (".md", ".toml")]
    remaining: set[str] = set()
    for p in paths:
        text = p.read_text(encoding="utf-8")
        for k, v in mapping.items():
            text = text.replace(k, v)
        p.write_text(text, encoding="utf-8")
        remaining.update(PLACEHOLDER_RE.findall(text))
    return sorted(remaining)


def _write_r1_archive(root: Path, mode: str) -> Path:
    date = dt.date.today()
    arch_dir = root / "docs" / "04-workflow" / "archive"
    arch_dir.mkdir(parents=True, exist_ok=True)
    out = arch_dir / f"{date.isoformat()}-r1.md"
    if out.exists():
        return out
    if mode == "adopt":
        body = (
            f"# R1 · adopt ({date.isoformat()})\n\n"
            "## Background\n\n"
            "Existing project brought under the iteration-management loop "
            "(startup contract / ledger / archive / state cards / gates). "
            "Business code was not modified.\n\n"
            "## Verification\n\n"
            "- `tools/check_drift.py` passes; `llms.txt` generated.\n\n"
            "## Next\n\n"
            "- Trim AGENTS.md routing/constraints to this project; continue rounds with the five-step loop.\n"
        )
    else:
        body = (
            f"# R1 · init ({date.isoformat()})\n\n"
            "## Background\n\n"
            "One-click deployment of the iteration-management skeleton "
            "(startup contract / ledger / archive / state cards / tooling).\n\n"
            "## Verification\n\n"
            "- `tools/check_drift.py` passes; `llms.txt` generated.\n\n"
            "## Next\n\n"
            "- Fill in AGENTS.md technical constraints; continue rounds with the five-step loop.\n"
        )
    out.write_text(body, encoding="utf-8")
    return out


def _fill_routing_tables(root: Path, modules: list[dict]) -> None:
    """Replace the routing-table placeholder rows in AGENTS.md / AGENTS_WORKFLOW.md."""
    if not modules:
        return

    agents_rows = [
        f"| {m['kw']} | `docs/01-product/{m['name']}/` + `docs/02-technical/{m['name']}/` | {m['code']} |"
        for m in modules
    ]
    workflow_rows = [
        f"| {m['name']} | `01-product/{m['name']}/` → `02-technical/{m['name']}/iteration.md` | {m['code']} |"
        for m in modules
    ]

    def _replace_rows(path: Path, rows: list[str], drop_note: bool) -> None:
        lines = path.read_text(encoding="utf-8").splitlines()
        out: list[str] = []
        replaced = False
        for line in lines:
            if line.startswith("| {{") and ("MODULE" in line.upper() or "模块" in line):
                if not replaced:
                    out.extend(rows)
                    replaced = True
                continue
            if drop_note and ("按项目裁剪" in line or "Trim per project" in line):
                continue
            out.append(line)
        path.write_text("\n".join(out) + "\n", encoding="utf-8")

    _replace_rows(root / "AGENTS.md", agents_rows, drop_note=True)
    _replace_rows(root / "docs" / "04-workflow" / "AGENTS_WORKFLOW.md", workflow_rows, drop_note=False)


def _ensure_module_dirs(root: Path, modules: list[dict]) -> list[str]:
    created = []
    for m in modules:
        for rel in (Path("docs/01-product") / m["name"], Path("docs/02-technical") / m["name"]):
            d = root / rel
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                (d / ".gitkeep").write_text("", encoding="utf-8")
                created.append(rel.as_posix() + "/")
        if m["code"] and not (root / m["code"]).exists():
            d = root / m["code"]
            d.mkdir(parents=True, exist_ok=True)
            skeleton = FRONTEND_SKELETONS.get(m["name"])
            if skeleton and skeleton.exists():
                for f in skeleton.rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(skeleton)
                        dst = d / rel
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, dst)
                created.append(m["code"] + "/ (next.js + ts skeleton)")
            else:
                (d / ".gitkeep").write_text("", encoding="utf-8")
                created.append(m["code"] + "/")
    return created


def _run_quiet(cmd: list[str]) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        out = (r.stdout or r.stderr).strip()
        return r.returncode == 0, out
    except (OSError, subprocess.SubprocessError):
        return False, ""


def _gh_cmd() -> list[str]:
    """gh CLI: PATH lookup first, then the standard Windows install location."""
    exe = shutil.which("gh")
    if exe:
        return [exe]
    pf = os.environ.get("ProgramFiles")
    if pf:
        cand = Path(pf) / "GitHub CLI" / "gh.exe"
        if cand.is_file():
            return [str(cand)]
    return ["gh"]


def _py_version(exe: str) -> str:
    ok, out = _run_quiet([exe, "--version"])
    return out if ok else "unknown version"


def _find_python(mode: str) -> tuple[str | None, str]:
    """Resolve the user's Python: py launcher -> PATH python -> uv python find -> fallback."""
    ok, _ = _run_quiet(["py", "-3", "--version"])
    if ok:
        ok2, exe = _run_quiet(["py", "-3", "-c", "import sys; print(sys.executable)"])
        if ok2 and exe:
            return exe, "py launcher (user-installed)"
    p = shutil.which("python")
    if p:
        return p, "python on PATH"
    ok, exe = _run_quiet(["uv", "python", "find"])
    if ok and exe:
        return exe, "uv-managed Python"
    if mode == "system":
        return None, "no user Python detected"
    return sys.executable, "current interpreter (fallback; no standalone user Python found)"


def _install_python() -> tuple[str | None, str]:
    """Auto-deploy Python: prefer `uv python install`, else non-interactive winget."""
    ok, _ = _run_quiet(["uv", "--version"])
    if ok:
        r = subprocess.run(["uv", "python", "install", "3.12"], capture_output=True, text=True)
        if r.returncode == 0:
            ok2, exe = _run_quiet(["uv", "python", "find"])
            if ok2 and exe:
                return exe, "uv installed Python 3.12"
    ok, _ = _run_quiet(["winget", "--version"])
    if ok:
        r = subprocess.run(
            ["winget", "install", "-e", "--id", "Python.Python.3.12",
             "--accept-source-agreements", "--accept-package-agreements"],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            exe, source = _find_python("system")
            if exe:
                return exe, f"{source} (winget installed Python 3.12)"
    return None, "auto-install failed: no uv and no winget (install manually and rerun)"


def _handle_venv(root: Path, mode: str, python_exe: str) -> str:
    venv = root / ".venv"
    if venv.exists():
        return "reused"
    if mode == "reuse":
        return "missing"
    if mode == "skip":
        return "skipped"
    if mode == "shared":
        subprocess.run(
            [python_exe, "-m", "venv", "--system-site-packages", str(venv)],
            cwd=root, check=True,
        )
        return "created-shared"
    if mode in ("auto", "uv"):
        try:
            subprocess.run(["uv", "venv", str(venv)], cwd=root, check=True)
            return "created-uv"
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
    subprocess.run([python_exe, "-m", "venv", str(venv)], cwd=root, check=True)
    return "created"


def _git_init(root: Path) -> bool:
    if (root / ".git").exists():
        return False
    try:
        subprocess.run(["git", "init"], cwd=root, capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _install_precommit_gate(root: Path) -> None:
    """Copy the bundled pre-commit hook into .git/hooks (idempotent)."""
    src = ASSETS / "scripts" / "hooks" / "pre-commit"
    dst = root / ".git" / "hooks" / "pre-commit"
    if src.exists() and dst.parent.exists() and not dst.exists():
        shutil.copy2(src, dst)
        print(f"  pre-commit gate: installed ({dst.relative_to(root).as_posix()})")


def _install_skill(force: bool) -> Path | None:
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    dest = home / "skills" / "iteration-close-loop"
    if dest.exists() and not force:
        return None
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "agents").mkdir(exist_ok=True)
    shutil.copy2(SKILL_ASSETS / "SKILL.md", dest / "SKILL.md")
    shutil.copy2(SKILL_ASSETS / "agents" / "openai.yaml", dest / "agents" / "openai.yaml")
    return dest


def _parse_module(value: str) -> dict:
    name, _, kw = value.partition("=")
    name = name.strip()
    kw = kw.strip()
    catalog = DEFAULT_MODULES.get(name)
    return {
        "name": name,
        "kw": kw or (catalog["kw"] if catalog else name),
        "code": catalog["code"] if catalog else "",
    }


def _load_toml(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _merge_profile(merged: dict, part: dict) -> dict:
    for key in LIST_KEYS:
        merged.setdefault(key, [])
        merged[key].extend(part.get(key, []) or [])
    return merged


def _load_profile(profile: str | None, dimensions: list[str]) -> tuple[dict, str]:
    """Load a preset (or custom .toml path) + dimension overrides into one merged profile."""
    merged: dict = {}
    label = profile or "default"
    if profile and profile != "default":
        preset_path = PROFILES_DIR / "presets" / f"{profile}.toml"
        if not preset_path.exists() and Path(profile).suffix == ".toml":
            preset_path = Path(profile)
        if preset_path.exists():
            preset = _load_toml(preset_path)
            for dim, val in preset.get("dimensions", {}).items():
                dim_path = PROFILES_DIR / "dimensions" / dim / f"{val}.toml"
                if dim_path.exists():
                    _merge_profile(merged, _load_toml(dim_path))
            _merge_profile(merged, preset)
        else:
            print(f"warning: profile not found: {profile} (continuing with defaults)")
            label = "default"
    for d in dimensions:
        key, _, val = d.partition("=")
        dim_path = PROFILES_DIR / "dimensions" / key.strip() / f"{val.strip()}.toml"
        if dim_path.exists():
            _merge_profile(merged, _load_toml(dim_path))
            label = "+".join(filter(None, [label if label != "default" else "", key.strip() + "=" + val.strip()]))
        else:
            print(f"warning: dimension option not found: {d}")
    return merged, label


def _inject_constraints(agents_path: Path, constraints: list[str]) -> None:
    lines = agents_path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    inserted = False
    for line in lines:
        out.append(line)
        if not inserted and line.startswith("## 3.") and ("Technical" in line or "技术" in line):
            for c in constraints:
                out.append(f"- {c}")
            inserted = True
    agents_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _apply_profile(target: Path, merged: dict) -> list[str]:
    """Inject profile content: constraints, red-line stub, doc stubs, gitignore additions."""
    created: list[str] = []
    if merged.get("constraints"):
        _inject_constraints(target / "AGENTS.md", merged["constraints"])
    if merged.get("red_lines"):
        red = target / "docs" / "00-system" / "constitution" / "red-lines.md"
        red.parent.mkdir(parents=True, exist_ok=True)
        if not red.exists():
            red.write_text(
                "# Red Lines (project)\n\n"
                "> Irreversible constraints from incidents; never bypass. "
                "Add new red lines here, never archive them.\n\n",
                encoding="utf-8",
            )
        body = "\n".join(f"- {x}" for x in merged["red_lines"]) + "\n"
        red.write_text(red.read_text(encoding="utf-8") + body, encoding="utf-8")
        created.append(red.relative_to(target).as_posix())
    for stub in merged.get("docs_stubs", []):
        p = target / "docs" / stub
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            title = Path(stub).stem.replace("-", " ").title()
            p.write_text(f"# {title}\n\n> Placeholder — fill in per the project profile.\n", encoding="utf-8")
            created.append(stub)
    gi = target / ".gitignore"
    if merged.get("gitignore_add") and gi.exists():
        existing = gi.read_text(encoding="utf-8")
        add = [x for x in merged["gitignore_add"] if x not in existing]
        if add:
            gi.write_text(existing.rstrip() + "\n" + "\n".join(add) + "\n", encoding="utf-8")
    return created


def _has_content(root: Path) -> bool:
    try:
        return any(p.name != ".git" for p in root.iterdir())
    except OSError:
        return False


def _read_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def detect_project_type(root: Path) -> dict:
    """Fingerprint an existing folder into script / plugin / page / app / generic."""
    manifest = root / "manifest.json"
    pkg = root / "package.json"
    pyproject = root / "pyproject.toml"
    reqs = root / "requirements.txt"
    index_html = root / "index.html"

    if manifest.is_file() and "manifest_version" in _read_json(manifest):
        return {"type": "plugin", "runtime": "node", "label": DETECT_LABELS["plugin"]}
    if pkg.is_file():
        data = _read_json(pkg)
        deps = " ".join(
            list((data.get("dependencies") or {}).keys())
            + list((data.get("devDependencies") or {}).keys())
        )
        if any(k in deps for k in ("next", "react", "vue", "svelte", "vite", "angular")):
            return {"type": "page", "runtime": "node", "label": DETECT_LABELS["page"]}
        return {"type": "app", "runtime": "node", "label": DETECT_LABELS["app"]}
    if pyproject.is_file() or reqs.is_file():
        py_files = [p for p in root.glob("*.py")]
        structured = (root / "src").is_dir() or (root / "apps").is_dir() or (root / "packages").is_dir()
        if len(py_files) == 1 and not structured:
            return {"type": "script", "runtime": "python", "label": DETECT_LABELS["script"]}
        return {"type": "app", "runtime": "python", "label": DETECT_LABELS["app"]}
    if index_html.is_file():
        return {"type": "page", "runtime": "static", "label": DETECT_LABELS["page"]}

    root_files = [p for p in root.iterdir() if p.is_file()]
    scripts = [p for p in root_files if p.suffix in (".py", ".js", ".mjs", ".ts", ".sh", ".ps1")]
    if len(scripts) == 1 and not any(p.is_dir() for p in root.iterdir() if p.name != ".git"):
        s = scripts[0]
        runtime = "python" if s.suffix == ".py" else "node"
        return {"type": "script", "runtime": runtime, "label": DETECT_LABELS["script"]}
    return {"type": "generic", "runtime": "none", "label": DETECT_LABELS["generic"]}


def _env_preflight(runtime: str) -> list[str]:
    """Read-only environment check; prints what is found and what this project needs."""
    def probe(name: str, *args: str) -> str | None:
        ok, out = _run_quiet([name, *args])
        return out if ok else None

    tools = {
        "git": probe("git", "--version"),
        "python": probe("py", "-3", "--version") or probe("python", "--version"),
        "node": probe("node", "--version"),
        "uv": probe("uv", "--version"),
        "gh": _run_quiet(_gh_cmd() + ["--version"])[1] or None,
    }
    print("== environment preflight (read-only) ==")
    for k, v in tools.items():
        print(f"  {k}: {v or 'missing'}")
    needed = {"python"} if runtime == "python" else {"node"} if runtime == "node" else set()
    missing = [k for k in sorted(needed) if not tools.get(k)]
    print("  needed for this project: " + (", ".join(sorted(needed)) or "none"))
    print("  missing: " + (", ".join(missing) or "none"))
    return missing


def _npm_install(root: Path) -> str:
    pkg = root / "package.json"
    if not pkg.is_file():
        return "skipped (no package.json at root)"
    if (root / "node_modules").exists():
        return "skipped (node_modules already present)"
    try:
        r = subprocess.run(["npm", "install"], cwd=root, capture_output=True, text=True)
        if r.returncode == 0:
            return "installed"
        return "failed: " + ((r.stderr or r.stdout).strip()[-180:] or "npm unavailable")
    except OSError:
        return "failed: npm unavailable"


def _write_env_example(root: Path, ptype: str, merged: dict) -> str:
    dst = root / ".env.example"
    if dst.exists():
        return "exists"
    lines = ["# Copy to .env and fill in real values (.env is gitignored).", ""]
    for key in ENV_TEMPLATES.get(ptype, ENV_TEMPLATES["generic"]):
        lines.append(f"{key}")
    joined = "\n".join(lines)
    module_names = " ".join(m.get("name", "") for m in merged.get("modules", []))
    if "DATABASE_URL" not in joined and any(k in module_names for k in ("db", "database")):
        lines.append("DATABASE_URL=")
    dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "created"


def _github_remote(root: Path, url: str) -> str:
    if not url:
        return "none requested"
    try:
        r = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, capture_output=True, text=True)
        if r.returncode == 0:
            return f"origin already set: {r.stdout.strip()}"
        r2 = subprocess.run(["git", "remote", "add", "origin", url], cwd=root, capture_output=True, text=True)
        if r2.returncode == 0:
            return f"origin -> {url}"
        return "failed to add remote: " + ((r2.stderr or r2.stdout).strip()[-150:])
    except OSError:
        return "git unavailable"


def _ensure_git_identity(root: Path) -> bool:
    """Repo-local identity for the initial commit: existing config, else gh profile."""
    try:
        n = subprocess.run(["git", "config", "user.name"], cwd=root, capture_output=True, text=True)
        e = subprocess.run(["git", "config", "user.email"], cwd=root, capture_output=True, text=True)
        if n.returncode == 0 and n.stdout.strip() and e.returncode == 0 and e.stdout.strip():
            return True
        name_r = subprocess.run(_gh_cmd() + ["api", "user", "--jq", ".name"], capture_output=True, text=True, timeout=20)
        login_r = subprocess.run(_gh_cmd() + ["api", "user", "--jq", ".login"], capture_output=True, text=True, timeout=20)
        email_r = subprocess.run(_gh_cmd() + ["api", "user", "--jq", ".email"], capture_output=True, text=True, timeout=20)
        if login_r.returncode == 0 and login_r.stdout.strip():
            name = name_r.stdout.strip() or login_r.stdout.strip()
            email = email_r.stdout.strip()
            if not email:
                id_r = subprocess.run(_gh_cmd() + ["api", "user", "--jq", ".id"], capture_output=True, text=True, timeout=20)
                email = f"{id_r.stdout.strip()}+{login_r.stdout.strip()}@users.noreply.github.com"
            subprocess.run(["git", "config", "user.name", name], cwd=root, capture_output=True)
            subprocess.run(["git", "config", "user.email", email], cwd=root, capture_output=True)
            return True
    except (OSError, subprocess.SubprocessError):
        pass
    return False


def _git_push(root: Path) -> str:
    """Push HEAD; on a fresh repo, create the initial commit first (repo-local identity)."""
    try:
        r = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            add = subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True, text=True)
            if add.returncode != 0:
                return "push failed: git add -A failed - " + ((add.stderr or add.stdout).strip()[-150:])
            _ensure_git_identity(root)
            cm = subprocess.run(["git", "commit", "-m", "chore: init"], cwd=root, capture_output=True, text=True)
            if cm.returncode != 0:
                return "push failed: initial commit failed (set git user.name/user.email) - " + ((cm.stderr or cm.stdout).strip()[-150:])
        p = subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=root, capture_output=True, text=True)
        if p.returncode == 0:
            return "pushed (origin HEAD, initial commit auto-created)"
        return "push failed (authenticate first): " + ((p.stderr or p.stdout).strip()[-150:])
    except OSError:
        return "git unavailable"


def _write_minimal_readme(root: Path, name: str) -> Path | None:
    dst = root / "README.md"
    if dst.exists():
        return None
    dst.write_text(
        f"# {name}\n\n"
        "> Managed with the VibeCoding_Manager iteration loop "
        "(changelog / archive / NOW / gates). See `docs/04-workflow/`.\n",
        encoding="utf-8",
    )
    return dst


def _effective_runtime(profile: str | None, dimensions: list[str], detected: dict, mode: str) -> str:
    """Decide the runtime: adopt trusts the fingerprint; scaffold reads profile/dimensions."""
    if mode == "adopt":
        return detected["runtime"]
    runtime_dims = [d.split("=", 1)[1] for d in dimensions if d.startswith("runtime=")]
    if runtime_dims:
        return runtime_dims[0]
    if profile and profile != "default":
        p = PROFILES_DIR / "presets" / f"{profile}.toml"
        if not p.exists() and Path(profile).suffix == ".toml":
            p = Path(profile)
        if p.exists():
            try:
                dim = _load_toml(p).get("dimensions", {}).get("runtime")
                if dim:
                    return dim
            except Exception:
                pass
    return "python"


def main() -> None:
    ap = argparse.ArgumentParser(description="Put any coding project under local iteration management")
    ap.add_argument("target", nargs="?", default=".", help="target directory (default: current)")
    ap.add_argument("--name", default=None, help="project name (default: target dir name)")
    ap.add_argument("--mode", choices=["auto", "assess", "adopt", "scaffold"], default="auto",
                    help="auto: empty folder -> scaffold, code present -> read-only assess (default)")
    ap.add_argument("--assessment", default=None,
                    help="JSON emitted by --mode assess; required before --mode adopt")
    ap.add_argument("--workflow", action="append", default=[], metavar="name=keep|map|managed",
                    help="adoption choice (repeatable): startup/state/ledger/methodology/tooling")
    ap.add_argument("--existing-system", action="append", default=[], metavar="NAME",
                    help="similar project-management system declared by the user (assess; repeatable)")
    ap.add_argument("--compat-policy", choices=list(COMPAT_POLICIES), default=None,
                    help="low-match decision: full-takeover|takeover|defer|abandon")
    ap.add_argument("--system-policy", choices=list(SYSTEM_POLICIES), default=None,
                    help="similar-system decision: keep-map|auto-takeover|abandon")
    ap.add_argument("--json", action="store_true", help="print assessment JSON (assess mode only)")
    ap.add_argument("--force", action="store_true", help="overwrite existing management files")
    ap.add_argument("--no-install-skill", action="store_true", help="skip iteration-close-loop install")
    ap.add_argument("--module", action="append", default=[], metavar="name=kw1,kw2",
                    help="business modules (scaffold only; repeatable)")
    ap.add_argument("--code", action="append", default=[], metavar="name=dir",
                    help="module code dir (scaffold only, repeatable)")
    ap.add_argument("--template", choices=["default"], default=None,
                    help="default template: web + api + db + worker + tests (scaffold only)")
    ap.add_argument("--python", default="auto", metavar="auto|system|install|<path>",
                    help="Python runtime: auto=detect user's existing (default); system=no fallback; "
                         "install=auto-deploy (uv/winget); or an explicit interpreter path")
    ap.add_argument("--env", choices=["auto", "shared", "isolated", "reuse", "skip", "create", "uv"],
                    default="auto",
                    help="dependency policy: auto=reuse existing/uv venv/project-local (default); "
                         "shared=--system-site-packages; isolated=clean local .venv; reuse=existing only; "
                         "skip=none (legacy create/uv mapped)")
    ap.add_argument("--deps", choices=["auto", "commands", "skip"], default="auto",
                    help="dependency installs: auto=run them (default); commands=print only; skip=none")
    ap.add_argument("--profile", default=None,
                    help="project-type preset: script|plugin|page|default|saas|c-end|vector-db|cli-tool, "
                         "or a custom .toml path")
    ap.add_argument("--dimension", action="append", default=[], metavar="key=value",
                    help="dimension override (repeatable): deploy/data/runtime/surface")
    ap.add_argument("--github", default=None, help="GitHub repo URL to set as origin")
    ap.add_argument("--push", action="store_true", help="attempt initial push after git init/remote")
    ap.add_argument("--no-venv", action="store_true", help="alias for --env skip")
    args = ap.parse_args()

    target = Path(args.target).resolve()
    name = args.name or target.name
    if args.mode == "assess" and not target.is_dir():
        ap.error("assess requires an existing project directory")
    target.mkdir(parents=True, exist_ok=True)

    mode = args.mode
    if mode == "auto":
        mode = "assess" if _has_content(target) else "scaffold"
    detected = {"type": "generic", "runtime": "none", "label": DETECT_LABELS["generic"]}
    if mode in {"assess", "adopt"}:
        detected = detect_project_type(target)
    if mode == "assess":
        _print_assessment(_assessment(target, detected, args.existing_system), args.json)
        return
    if mode == "adopt":
        try:
            _run_adopt(
                target,
                name,
                Path(args.assessment).resolve() if args.assessment else None,
                args.workflow,
                args.compat_policy,
                args.system_policy,
            )
        except ValueError as exc:
            ap.error(str(exc))
        return

    # --- copy management files -------------------------------------------
    copied, skipped = [], []
    for src in sorted(ASSETS.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(ASSETS)
        if mode == "adopt" and rel.parts[0] in ADOPT_SKIP_TOP:
            continue
        dst = target / rel
        if dst.exists() and not args.force:
            skipped.append(rel.as_posix())
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst)
    if mode == "adopt":
        readme = _write_minimal_readme(target, name)
        if readme:
            copied.append(readme)

    # --- scaffold-only module handling -----------------------------------
    modules: list[dict] = []
    if mode == "scaffold":
        names = list(args.module)
        if args.template == "default":
            for key in ("web", "api", "db", "worker", "tests"):
                if not any(n.partition("=")[0].strip() == key for n in names):
                    names.append(key)
        modules = [_parse_module(m) for m in names]
        code_map = {}
        for c in args.code:
            k, _, v = c.partition("=")
            code_map[k.strip()] = v.strip()
        for m in modules:
            m["code"] = code_map.get(m["name"], m["code"])

    # --- profile + dimensions --------------------------------------------
    profile = args.profile
    dimensions = list(args.dimension)
    if mode == "adopt":
        profile = profile or DETECT_PROFILE.get(detected["type"])
        if detected["runtime"] in ("python", "node"):
            preset_path = PROFILES_DIR / "presets" / f"{profile}.toml" if profile else None
            preset_dims: dict = {}
            if preset_path and preset_path.exists():
                preset_dims = _load_toml(preset_path).get("dimensions", {})
            if preset_dims.get("runtime") != detected["runtime"]:
                dimensions.append(f"runtime={detected['runtime']}")
    merged, profile_label = _load_profile(profile, dimensions)
    if mode == "scaffold":
        for pm in merged.get("modules", []):
            modules.append({
                "name": pm["name"],
                "kw": pm.get("keywords", pm["name"]),
                "code": pm.get("code", ""),
            })
    profile_created = _apply_profile(target, merged)

    if mode == "scaffold":
        _fill_routing_tables(target, modules)
    remaining = _replace_placeholders(target, name, scope=(copied if mode == "adopt" else None))
    arch = _write_r1_archive(target, mode)
    if mode == "scaffold":
        created_dirs = _ensure_module_dirs(target, modules)
    else:
        created_dirs = []
    env_status = _write_env_example(target, detected["type"] if mode == "adopt" else (profile or "generic"), merged)

    gen = target / "tools" / "gen_llms_txt.py"
    if gen.exists():
        subprocess.run([sys.executable, str(gen)], cwd=target, check=True)

    # --- environment preflight + dependency handling ----------------------
    runtime = _effective_runtime(profile, dimensions, detected, mode)
    _env_preflight(runtime)

    python_exe, py_source, py_version = None, "-", "-"
    venv_status = "not-needed (node project)"
    npm_status = "skipped (--deps not auto)"
    install_commands: list[str] = []
    if runtime == "node":
        if args.deps == "auto":
            npm_status = _npm_install(target)
        elif args.deps == "commands":
            npm_status = "commands-only"
            install_commands.append("npm install")
        else:
            npm_status = "skipped"
    elif runtime in ("static", "none"):
        venv_status = "not-needed (no runtime dependencies detected)"
        npm_status = "skipped"
    else:
        env_mode = "skip" if args.no_venv else {"create": "isolated", "uv": "auto"}.get(args.env, args.env)
        if args.deps == "skip":
            venv_status = "skipped (--deps skip)"
        else:
            if args.python in ("auto", "system"):
                py_mode = args.python if args.deps == "auto" else "system"
                python_exe, py_source = _find_python(py_mode)
            elif args.python == "install" and args.deps == "auto":
                python_exe, py_source = _install_python()
            else:
                python_exe, py_source = args.python, "user-specified path"
            py_version = _py_version(python_exe) if python_exe else "-"
            if args.deps == "commands":
                venv_status = "commands-only"
                if python_exe:
                    install_commands.append(f"{python_exe} -m venv .venv")
                else:
                    install_commands.append("install Python 3.12 (uv python install 3.12 or winget), then python -m venv .venv")
            elif python_exe is not None and env_mode != "skip":
                try:
                    venv_status = _handle_venv(target, env_mode, python_exe)
                except (subprocess.CalledProcessError, OSError):
                    venv_status = "failed"
            elif python_exe is None:
                venv_status = "no-python"
    if install_commands:
        print("== install commands (you run these) ==")
        for c in install_commands:
            print(f"  $ {c}")

    # --- git / GitHub -----------------------------------------------------
    git_inited = _git_init(target)
    if git_inited:
        _install_precommit_gate(target)
    github_status = _github_remote(target, args.github or "")
    push_status = _git_push(target) if (args.github and args.push) else "not requested"

    installed = None
    if not args.no_install_skill:
        installed = _install_skill(args.force)

    # --- report -----------------------------------------------------------
    print(f"\n{'Adoption' if mode == 'adopt' else 'Deployment'} complete: {target}")
    print(f"  mode: {mode} (detected {detected['label']})" if mode == "adopt" else f"  mode: {mode}")
    print(f"  copied {len(copied)} files, skipped {len(skipped)} existing")
    if merged:
        print(f"  profile: {profile_label} (+{len(merged.get('modules', []))} modules, "
              f"+{len(merged.get('constraints', []))} constraints, "
              f"+{len(merged.get('red_lines', []))} red lines)")
        if profile_created:
            print(f"  profile files: {'、'.join(profile_created)}")
    if created_dirs:
        print(f"  module placeholder dirs: {'、'.join(created_dirs)}")
    print(f"  init archive: {arch.relative_to(target).as_posix()}")
    print(f"  .env.example: {env_status}")
    status_text = {
        "reused": "existing, reused",
        "created": "created (local Python)",
        "created-uv": "created (uv venv)",
        "created-shared": "created (shared system packages)",
        "missing": "no existing env and policy is reuse-only; not created",
        "skipped": "skipped (--env skip)",
        "failed": "creation failed (run manually: python -m venv .venv)",
        "no-python": "no Python found; env not created",
        "commands-only": "not run (--deps commands; commands printed above)",
        "not-needed (node project)": "not needed (node project)",
    }
    print(f"  Python: {py_version} ({py_source})")
    if python_exe:
        print(f"    path: {python_exe}")
    print(f"  .venv: {status_text.get(venv_status, venv_status)}")
    if runtime == "node":
        print(f"  npm install: {npm_status}")
    if venv_status == "no-python":
        print("  hint: rerun with --deps auto --python install to auto-deploy (uv python install / winget Python 3.12)")
    if git_inited:
        print("  git: initialized")
    elif (target / ".git").exists():
        print("  git: already a repository")
    else:
        print("  git: unavailable or skipped")
    print(f"  github: {github_status}")
    if args.github and args.push:
        print(f"  push: {push_status}")
    print("  commit: git add -A && git commit -m \"chore: init\"")
    if installed:
        print(f"  installed skill: {installed}")
    else:
        print("  iteration-close-loop already present, not reinstalled")
    if remaining:
        print("  remaining placeholders: " + "、".join(remaining))
    else:
        print("  all placeholders replaced")
    if mode == "adopt":
        print("  next: business code untouched; open a new conversation and start your first real task.")
    else:
        print("  next: fill AGENTS.md technical constraints; run tools/check_drift.py to verify")


if __name__ == "__main__":
    main()
