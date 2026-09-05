#!/usr/bin/env python3
"""Put any coding project under local iteration management (manager-first).

Two entry paths, one outcome — a managed project with the iteration loop
(AGENTS startup contract / changelog + archive + NOW / deterministic gates):

  * scaffold:  empty folder -> generate the full skeleton (README, AGENTS.md,
               docs tree, tooling, .venv, git). The generator is the empty-folder
               default, not the core.
  * assess:    folder already has code -> inspect its workflow without writing
               (pass --intent after the user describes the product; add
               --environment-scan for the authorized whole-machine read-only check)
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
      [--intent "one-sentence project description"] [--environment-scan] \
      [--migration-plan PATH] [--migration-confirm] [--migrate-code] \
      [--python auto|system|install|<path>] [--env auto|shared|isolated|reuse|skip] \
      [--deps auto|commands|skip] [--github <repo-url>] [--push] \
      [--skills-dir PATH] [--skill-location auto|project|global|skip] \
      [--discover-skills] [--dry-run] [--force] [--no-venv] [--no-install-skill]

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
  uv:   create the env with uv; auto-install uv when missing and --deps auto
  shared: project .venv with --system-site-packages (sees the base Python's packages)
  isolated: clean project-local .venv (--no-venv equals skip; legacy create/uv map to isolated/auto)
  reuse: only reuse an existing .venv, never create
  skip: do nothing

Dependency disclosure (--deps, default auto) — always decided with the user BEFORE running:
  auto: run the installs (venv for Python projects, npm install for Node projects)
  commands: only print the exact commands; never run them
  skip: no dependency handling at all

Skill install (--skill-location, default auto):
  auto: project-local `.guiyuan-vibecoding/skills/` unless `--skills-dir` or
        VIBECODING_SKILLS_HOME is set
  project: always install close-loop into `.guiyuan-vibecoding/skills/`
  global: install close-loop into an explicit `--skills-dir` or VIBECODING_SKILLS_HOME
  skip: no skill copy (legacy --no-install-skill alias)

GitHub (--github <url>): set the origin remote (never overwrites an existing origin).
--push: attempt `git push -u origin HEAD` (user must already be authenticated).

For an existing project, `auto` is intentionally read-only and prints an assessment.  Save
`--mode assess --json` output outside the project, then pass it back to `--mode adopt` with
the workflow choices the user confirmed. Adopt never silently overwrites business code, installs
dependencies, initializes Git, or installs global Skills. Confirmed full takeover may rewrite only
explicit path references from its migration plan.
Global Skills are never written without an explicit user-chosen path.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
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
# Internal payloads deliberately do not use the discoverable SKILL.md filename.  The Agent
# should expose one public entry point; bootstrap materializes the project-local close-loop
# skill only after the project has opted into it.
SKILL_ASSETS = SKILL_ROOT / "assets" / "internal" / "iteration-close-loop"
FRONTEND_SKELETONS = {
    "web": SKILL_ROOT / "assets" / "frontend" / "web",
    "admin": SKILL_ROOT / "assets" / "frontend" / "admin",
}
PROFILES_DIR = SKILL_ROOT / "profiles"
INTENT_MAP = PROFILES_DIR / "intent-map.toml"
TOPOLOGIES_DIR = PROFILES_DIR / "topologies"
SCALES_DIR = PROFILES_DIR / "scales"
CAPABILITIES_DIR = PROFILES_DIR / "capabilities"
VIBECODING_SKILLS_HOME = "VIBECODING_SKILLS_HOME"
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
    "md-managed": "Markdown-managed project (no installed Skill)",
}
ENV_TEMPLATES = {
    "script": ["API_KEY=", "BASE_URL="],
    "plugin": ["API_KEY=", "BASE_URL="],
    "page": ["NEXT_PUBLIC_API_BASE_URL=", "API_KEY="],
    "app": ["DATABASE_URL=", "SECRET_KEY=", "API_KEY=", "PORT=8000"],
    "generic": ["SECRET_KEY=", "API_KEY="],
}

# The project template carries this helper so scaffold/adopt work without importing
# VCM's repository-internal package. Load it without mutating ``sys.path``.
ensure_gitignore = None
_gi_path = ASSETS / "tools" / "gitignore_profiles.py"
if _gi_path.is_file():
    _gi_spec = importlib.util.spec_from_file_location("_guiyuan_gitignore_profiles", _gi_path)
    if _gi_spec and _gi_spec.loader:
        _gi_mod = importlib.util.module_from_spec(_gi_spec)
        _gi_spec.loader.exec_module(_gi_mod)
        ensure_gitignore = _gi_mod.ensure

# Existing projects are never converted in one step.  These groups are the only
# management surfaces Guiyuan Vibecoding can own; source code is deliberately
# not part of the map.
WORKFLOWS = ("startup", "state", "ledger", "methodology", "tooling")
ADOPTION_DIR = ".guiyuan-vibecoding"
# ``defer`` remains a CLI compatibility alias; the user-facing name is progressive adoption.
COMPAT_POLICIES = ("full-takeover", "takeover", "progressive", "defer", "abandon")
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
        "id": "guiyuan-vibecoding",
        "label": "Guiyuan Vibecoding workflow",
        "markers": (".guiyuan-vibecoding/", ".vibecoding-manager/", "docs/04-workflow/", "AGENTS_WORKFLOW.md"),
    },
    {
        "id": "agent-rules",
        "label": "Agent rule file",
        "markers": ("AGENTS.md",),
    },
    {
        "id": "iteration-ledger",
        "label": "Iteration ledger / roadmap docs",
        "markers": ("CHANGELOG.md", "docs/01-product/roadmap.md"),
    },
)

# These are intentionally recommendations, not decisions.  The conversation layer must
# collect the product intent first and present these candidates for the user to choose.
INTENT_TEMPLATE_HINTS = {
    "script": [
        {"template": "cli", "capabilities": [], "reason": "单一命令行/本地工具边界清晰"},
        {"template": "python-service", "capabilities": [], "reason": "后续可能演进为可复用 Python 服务"},
    ],
    "cli-tool": [
        {"template": "cli", "capabilities": [], "reason": "命令行入口与测试目录分离"},
        {"template": "python-service", "capabilities": ["worker"], "reason": "需要后台任务或长流程时可扩展"},
    ],
    "plugin": [
        {"template": "web-app", "capabilities": [], "reason": "前端/扩展界面与测试分层"},
        {"template": "monorepo", "capabilities": [], "reason": "扩展、共享包和测试需要并列管理"},
    ],
    "page": [
        {"template": "web-app", "capabilities": [], "reason": "网页、组件、工具库与测试分层"},
        {"template": "web-app", "capabilities": ["content-pipeline"], "reason": "内容发布或文案流水线可选"},
    ],
    "content-site": [
        {"template": "web-app", "capabilities": ["content-pipeline"], "reason": "内容生产与网页呈现分开"},
        {"template": "monorepo", "capabilities": ["content-pipeline"], "reason": "站点、内容工具和共享包并列"},
    ],
    "saas": [
        {"template": "composite", "capabilities": ["auth", "admin"], "reason": "网页、API 与管理面板需要独立边界"},
        {"template": "monorepo", "capabilities": ["auth", "admin", "worker"], "reason": "多应用和异步任务并行演进"},
    ],
    "admin-dashboard": [
        {"template": "web-app", "capabilities": ["auth", "admin"], "reason": "后台界面、权限与测试分层"},
        {"template": "composite", "capabilities": ["auth", "admin"], "reason": "同时拥有独立 API 或任务服务时可选"},
    ],
    "ecommerce": [
        {"template": "composite", "capabilities": ["auth", "payments", "worker"], "reason": "前台、订单/支付 API 与异步任务隔离"},
        {"template": "monorepo", "capabilities": ["auth", "payments", "worker"], "reason": "多端和共享领域包需要并列管理"},
    ],
    "c-end": [
        {"template": "composite", "capabilities": ["auth", "worker"], "reason": "用户端、API 与后台任务分开"},
        {"template": "web-app", "capabilities": ["auth"], "reason": "先做单体用户端时边界更轻"},
    ],
    "vector-db": [
        {"template": "python-service", "capabilities": ["rag", "vector-db"], "reason": "检索、知识处理与 API 以 Python 为主"},
        {"template": "composite", "capabilities": ["rag", "vector-db", "worker"], "reason": "同时需要网页、API 和异步索引任务"},
    ],
    "bot": [
        {"template": "python-service", "capabilities": ["worker"], "reason": "消息接入与后台任务分离"},
        {"template": "composite", "capabilities": ["worker", "auth"], "reason": "需要控制台或多渠道接入时可选"},
    ],
    "default": [
        {"template": "python-service", "capabilities": [], "reason": "通用服务型起点"},
        {"template": "web-app", "capabilities": [], "reason": "通用网页型起点"},
        {"template": "composite", "capabilities": [], "reason": "同时存在前端与服务端时可选"},
    ],
}

AGENT_COMMANDS = (
    ("Codex", "codex"), ("Claude Code", "claude"), ("Cursor", "cursor"),
    ("Windsurf", "windsurf"), ("Aider", "aider"), ("Gemini CLI", "gemini"),
    ("Cline", "cline"), ("OpenCode", "opencode"),
)

MIGRATION_EXCLUDE_PARTS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".next", "dist", "build", "target", "vendor",
    ".guiyuan-vibecoding", ".codex",
}
MIGRATION_EXCLUDE_CASEFOLD = {part.casefold() for part in MIGRATION_EXCLUDE_PARTS}
DATA_DIR_NAMES = {
    "data", "database", "db", "storage", "uploads", "upload", "content", "knowledge",
    "vector", "vectors", "media", "fixtures", "exports", "migrations", "datasets",
}
DATA_FILE_SUFFIXES = {
    ".db", ".sqlite", ".sqlite3", ".jsonl", ".csv", ".tsv", ".parquet", ".feather",
    ".pkl", ".pickle", ".npy", ".npz",
}
TEXT_PATH_SUFFIXES = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".json", ".toml", ".yaml",
    ".yml", ".ini", ".cfg", ".conf", ".env", ".md", ".html", ".css", ".scss", ".sh",
    ".bat", ".cmd", ".ps1", ".txt",
}
CODE_ROOT_ALIASES = {
    "apps": "apps", "app": "app", "src": "src", "packages": "packages",
    "components": "components", "lib": "lib", "workers": "workers", "worker": "workers",
    "tests": "tests", "configs": "configs", "config": "configs", "scripts": "scripts",
    "apps": "apps",
}
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
    result = {
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
    return result


def _functional_module_catalog() -> list[dict]:
    """Return VCM's human-facing functional module catalog.

    The source document is optional in an installed standalone Skill.  Keep a small
    fallback so the intake report still explains the manager's own module boundaries.
    """
    source = SKILL_ROOT.parents[1] / "docs" / "00-system" / "functional-module-directory.md"
    if source.is_file():
        text = source.read_text(encoding="utf-8")
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
        if match:
            try:
                value = json.loads(match.group(1))
                modules = value.get("functionalModules")
                if isinstance(modules, list):
                    return [m for m in modules if isinstance(m, dict)]
            except json.JSONDecodeError:
                pass
    return [
        {"id": "intake", "name": "项目接入与生命周期", "plain": "把新项目或旧项目接入归园流程", "entry": "skills/guiyuan-vibecoding/scripts/bootstrap.py"},
        {"id": "analysis", "name": "需求接收与分析", "plain": "把想法整理成可确认的事实与选择", "entry": "tools/analysis.py"},
        {"id": "planning", "name": "规划与任务编排", "plain": "按依赖选出下一件能做的事", "entry": "tools/task_graph.py"},
        {"id": "execution", "name": "执行、验证与交付", "plain": "做完就测试并留下回执", "entry": "tools/receipt_loop.py"},
    ]


def _project_structure(root: Path) -> dict:
    """Summarize the visible root without reading business source contents."""
    ignored = {".git", ".venv", "venv", "node_modules", "__pycache__", ".next", "dist", "build"}
    entries: list[dict] = []
    try:
        children = sorted((p for p in root.iterdir() if p.name not in ignored), key=lambda p: (p.is_file(), p.name.casefold()))
    except OSError:
        children = []
    for path in children[:40]:
        entries.append({"name": path.name, "kind": "file" if path.is_file() else "directory"})
    return {"entries": entries, "truncated": len(children) > len(entries)}


def _iter_project_files(root: Path):
    """Yield project files without following symlinked directories or cache trees."""
    for base, dirs, files in os.walk(root, topdown=True, followlinks=False):
        base_path = Path(base)
        dirs[:] = [name for name in dirs if name.casefold() not in MIGRATION_EXCLUDE_CASEFOLD]
        for name in files:
            path = base_path / name
            if path.is_symlink() or any(part.casefold() in MIGRATION_EXCLUDE_CASEFOLD for part in path.relative_to(root).parts):
                continue
            yield path


def _path_stats(path: Path, root: Path) -> dict:
    """Collect bounded, content-free stats for one data candidate."""
    files = 0
    total_bytes = 0
    latest_ns = 0
    if path.is_file():
        candidates = [path]
    elif path.is_dir():
        candidates = []
        for item in _iter_project_files(path):
            candidates.append(item)
    else:
        candidates = []
    for item in candidates:
        try:
            stat = item.stat()
        except OSError:
            continue
        files += 1
        total_bytes += stat.st_size
        latest_ns = max(latest_ns, stat.st_mtime_ns)
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.name
    return {
        "path": rel,
        "kind": "file" if path.is_file() else "directory",
        "files": files,
        "bytes": total_bytes,
        "latest_mtime_ns": latest_ns,
    }


def _data_inventory(root: Path) -> dict:
    """Find likely user data without reading its contents."""
    candidates: list[Path] = []
    try:
        children = list(root.iterdir())
    except OSError:
        children = []
    for child in children:
        if child.name.casefold() in MIGRATION_EXCLUDE_CASEFOLD:
            continue
        lower = child.name.casefold()
        if child.is_dir() and lower in DATA_DIR_NAMES:
            if lower == "data":
                nested = [p for p in child.iterdir() if p.name.casefold() in DATA_DIR_NAMES]
                candidates.extend(nested or [child])
            else:
                candidates.append(child)
        elif child.is_file() and child.suffix.casefold() in DATA_FILE_SUFFIXES:
            candidates.append(child)
    seen: set[str] = set()
    entries: list[dict] = []
    for candidate in sorted(candidates, key=lambda p: p.as_posix().casefold()):
        key = candidate.as_posix().casefold()
        if key in seen:
            continue
        seen.add(key)
        entries.append(_path_stats(candidate, root))
    digest_input = "\n".join(
        f"{item['path']}|{item['kind']}|{item['files']}|{item['bytes']}|{item['latest_mtime_ns']}"
        for item in entries
    )
    total_files = sum(item["files"] for item in entries)
    total_bytes = sum(item["bytes"] for item in entries)
    return {
        "entries": entries,
        "count": len(entries),
        "files": total_files,
        "bytes": total_bytes,
        "digest": hashlib.sha256(digest_input.encode("utf-8")).hexdigest(),
        "read_only": True,
    }


def _project_size(root: Path, data: dict | None = None) -> dict:
    """Classify project scale using transparent file/byte thresholds.

    Small: <= 1,000 files and <= 100 MiB; medium: <= 10,000 files and <= 2 GiB;
    anything larger is large. Caches and generated dependencies are excluded.
    """
    file_count = 0
    total_bytes = 0
    code_files = 0
    capped = False
    code_suffixes = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cs", ".cpp", ".c", ".h", ".html", ".css"}
    for path in _iter_project_files(root):
        try:
            total_bytes += path.stat().st_size
        except OSError:
            continue
        file_count += 1
        code_files += int(path.suffix.casefold() in code_suffixes)
        if file_count >= 100_000:
            capped = True
            break
    if capped or file_count > 10_000 or total_bytes > 2 * 1024 * 1024 * 1024:
        level = "large"
    elif file_count > 1_000 or total_bytes > 100 * 1024 * 1024:
        level = "medium"
    else:
        level = "small"
    data = data or _data_inventory(root)
    return {
        "level": level,
        "files": file_count,
        "bytes": total_bytes,
        "code_files": code_files,
        "data_files": data.get("files", 0),
        "data_bytes": data.get("bytes", 0),
        "scan_capped": capped,
        "thresholds": {
            "small_max_files": 1000,
            "small_max_bytes": 100 * 1024 * 1024,
            "medium_max_files": 10000,
            "medium_max_bytes": 2 * 1024 * 1024 * 1024,
        },
    }


def _human_bytes(value: int | float) -> str:
    """Format a byte count for the human intake report."""
    number = float(value or 0)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if number < 1024 or unit == "TiB":
            return f"{number:.1f} {unit}" if unit != "B" else f"{int(number)} B"
        number /= 1024
    return "0 B"


def _directory_groups(directories: list[str]) -> dict[str, list[str]]:
    """Group candidate physical directories by the human-facing functional area."""
    groups: dict[str, list[str]] = {
        "应用与服务": [], "数据与知识": [], "任务与集成": [],
        "测试与质量": [], "配置与脚本": [], "文档与管理": [], "其他": [],
    }
    for raw in directories:
        value = str(raw)
        lower = value.casefold()
        if lower == "tests" or lower.startswith("tests/") or "test" in lower:
            bucket = "测试与质量"
        elif lower.startswith(("data", "db", "knowledge", "vector")):
            bucket = "数据与知识"
        elif lower.startswith(("worker", "workers", "jobs", "queue", "integrations")):
            bucket = "任务与集成"
        elif lower.startswith(("config", "configs", "scripts", "tools")):
            bucket = "配置与脚本"
        elif lower.startswith(("docs", ".guiyuan", ".codex")):
            bucket = "文档与管理"
        elif lower.startswith(("src", "app", "apps", "packages", "components", "lib")):
            bucket = "应用与服务"
        else:
            bucket = "其他"
        groups[bucket].append(value)
    return {name: values for name, values in groups.items() if values}


def _template_recommendations(intent: str | None, detected: dict) -> dict:
    """Build user-visible candidates; never select a template or write files."""
    plan = _resolve_intent(intent, None) if intent else {
        "profile": None, "confidence": "unknown", "score": 0, "signals": [], "description": ""
    }
    profile = plan.get("profile") or "default"
    candidates = []
    for item in INTENT_TEMPLATE_HINTS.get(profile, INTENT_TEMPLATE_HINTS["default"]):
        try:
            spec = _load_template_spec(item["template"], "medium", item.get("capabilities", []))
            dirs = spec.get("dirs", [])
        except (OSError, ValueError, tomllib.TOMLDecodeError):
            dirs = []
        candidates.append({
            "template": item["template"],
            "capabilities": list(item.get("capabilities", [])),
            "reason": item["reason"],
            "directories": dirs,
            "directory_groups": _directory_groups(dirs),
        })
    return {
        "requested_intent": intent or "",
        "candidate_profile": plan.get("profile"),
        "confidence": plan.get("confidence", "unknown"),
        "signals": plan.get("signals", []),
        "candidates": candidates,
        "decision_required": True,
        "detected_project": detected.get("label", "未知项目"),
    }


def _assessment(root: Path, detected: dict, declared_systems: list[str] | None = None,
                intent: str | None = None, environment: dict | None = None,
                project_name: str | None = None) -> dict:
    groups = _managed_candidates(root)
    data_inventory = _data_inventory(root)
    project_size = _project_size(root, data_inventory)
    known_systems = _detect_known_systems(root)
    declared = _declared_systems(declared_systems or [])
    result = {
        "schema_version": 2,
        "target": str(root),
        "project_name": project_name or root.name,
        "assessed_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "detected": detected,
        "project_structure": _project_structure(root),
        "template_recommendations": _template_recommendations(intent, detected),
        "functional_modules": _functional_module_catalog(),
        "project_size": project_size,
        "data_inventory": data_inventory,
        "intent": intent or "",
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
    if environment is not None:
        result["environment"] = environment
    return result


def _print_assessment(data: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    detected = data["detected"]
    recommendations = data["template_recommendations"]
    print("== 项目接入只读评估 ==")
    print(f"  项目：{data.get('project_name', '')}")
    print(f"  位置：{data.get('target', '')}")
    print(f"  当前目录可能像：{detected['label']}")
    intent = data.get("intent", "").strip()
    if intent:
        print(f"  你的产品描述：{intent}")
    else:
        print("  尚未收到产品描述：请先说明想做什么，VCM 不会替你决定模板。")
    overview = "、".join(
        item["name"] for item in data.get("project_structure", {}).get("entries", [])[:16]
    )
    print("  现有目录概览：" + (overview or "空目录"))
    if data.get("project_structure", {}).get("truncated"):
        print("  （目录较多，仅展示前 16 项）")
    size = data.get("project_size", {})
    size_label = {"small": "小", "medium": "中", "large": "大"}.get(size.get("level"), "未知")
    print(f"  项目体量：{size_label}（约 {size.get('files', 0)} 个文件，{_human_bytes(size.get('bytes', 0))}）")
    inventory = data.get("data_inventory", {})
    print(f"  已有数据：{inventory.get('count', 0)} 个候选目录或文件，总大小 {_human_bytes(inventory.get('bytes', 0))}")
    print("  根据描述可考虑以下模板（仅供选择，不会自动套用）：")
    if not intent:
        print("    - 请先补充产品描述，再生成模板与目录建议。")
    else:
        for index, candidate in enumerate(recommendations.get("candidates", []), 1):
            caps = "、".join(candidate["capabilities"]) or "无额外能力层"
            print(f"    {index}. {candidate['template']}（{candidate['reason']}；能力：{caps}）")
            print("       建议功能目录：")
            for group, dirs in candidate.get("directory_groups", {}).items():
                print(f"         - {group}：{'、'.join(dirs)}")
    if data.get("known_systems") or data.get("declared_systems"):
        print("  检测到已有管理约定：接管前请决定是否保留、映射或归档。")
    print("  接管选择：")
    print("    1. 完全接管：按你确认的模板建立管理结构，旧管理层归档；业务数据迁移另行确认。")
    print("    2. 部分接管：只接管管理流程，不重构现有目录和业务代码。")
    print("    3. 渐进接管：本轮继续老流程，从新需求开始并行记录。")
    print("    4. 放弃接管：当前项目暂不使用 Guiyuan Vibecoding。")
    if size.get("level") == "large":
        print("  当前项目体量较大，不建议完全接管；建议部分接管或渐进接管。")
    elif size.get("level") in {"small", "medium"}:
        print("  当前项目体量适合考虑完全接管，但仍需确认模板和迁移计划。")
    if data.get("environment"):
        _print_environment_inventory(data["environment"])
        print("  全机环境已完成只读盘点；安装、切换 Python/Node、安装 UV 均尚未执行。")
    else:
        print("  当前阶段仅查看项目目录；全机环境盘点需用户明确授权后再执行。")
    print("  VCM 功能模块目录：" + "、".join(m.get("name", "") for m in data.get("functional_modules", [])))
    print("  未写入项目文件、未安装依赖、未修改 Git 或 Skill。")
    print("  下一步：确认模板/目录与接管方式后，再进行环境选择和执行。")


def _print_scaffold_candidates(root: Path, name: str, intent: str) -> None:
    """Show scaffold candidates without materializing a project."""
    recommendations = _template_recommendations(intent, {
        "label": DETECT_LABELS["generic"],
    })
    print("== 新项目模板建议（只读） ==")
    print(f"  项目：{name}")
    print(f"  位置：{root}")
    print(f"  产品描述：{intent}")
    print("  以下都是候选方案，请选择一个模板/能力后再执行 scaffold：")
    for index, candidate in enumerate(recommendations["candidates"], 1):
        caps = "、".join(candidate["capabilities"]) or "无额外能力层"
        print(f"    {index}. {candidate['template']}（{candidate['reason']}；能力：{caps}）")
        print("       建议功能目录：")
        for group, dirs in candidate.get("directory_groups", {}).items():
            print(f"         - {group}：{'、'.join(dirs)}")
    print("  未写入任何文件；确认后请显式传入 --template 或 --profile。")


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
    if compat_policy in {"progressive", "defer", "abandon"} or system_policy == "abandon":
        return
    if compat_policy == "full-takeover" and system_policy == "keep-map":
        raise ValueError("full-takeover conflicts with keep-map; choose auto-takeover for existing systems or takeover for scoped adoption")
    if compat.get("level") == "low" and not compat_policy:
        raise ValueError("compatibility gate: choose --compat-policy full-takeover|takeover|progressive|abandon")
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
    expected_data = data.get("data_inventory", {}).get("digest")
    if expected_data and _data_inventory_digest(root) != expected_data:
        raise ValueError("data inventory changed; rerun --mode assess before applying")


def _data_inventory_digest(root: Path) -> str:
    return _data_inventory(root).get("digest", "")


def _validate_external_plan_path(path: Path, root: Path) -> None:
    """Migration plans live outside the project so they cannot be adopted accidentally."""
    try:
        path.relative_to(root)
    except ValueError:
        return
    raise ValueError("--migration-plan must point outside the project directory")


def _path_text_references(root: Path, source: str, target: str) -> list[dict]:
    """Find deterministic text references to one planned path move."""
    source_forms = {source.replace("/", "\\"), source}
    if source.startswith("./"):
        source_forms.update({source[2:], source[2:].replace("/", "\\")})
    found: list[dict] = []
    for path in _iter_project_files(root):
        if path.suffix.casefold() not in TEXT_PATH_SUFFIXES:
            continue
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        matches = []
        for value in source_forms:
            if not value:
                continue
            if "/" in value or "\\" in value:
                if value in text:
                    matches.append(value)
            else:
                # A bare directory name is only safe when used as a quoted config/path value;
                # prose and identifiers remain manual-review territory.
                if re.search(rf"(['\"]){re.escape(value)}\1", text):
                    matches.append(value)
        if not matches:
            continue
        value = max(matches, key=len)
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        # References inside the item being moved are not stable source-code dependencies;
        # after the move their relative path would no longer exist at ``rel``.
        source_prefix = source.rstrip("/") + "/"
        if rel == source or rel.startswith(source_prefix):
            continue
        found.append({
            "file": rel,
            "match": value,
            "replacement": target.replace("/", "\\") if "\\" in value else target,
            "count": len(re.findall(rf"(['\"]){re.escape(value)}\1", text)) if "/" not in value and "\\" not in value else text.count(value),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    return found


def _build_migration_plan(root: Path, assessment: dict, template_spec: dict,
                          migrate_code: bool = False) -> dict:
    """Create a read-only, explicit source-to-target migration plan."""
    if not template_spec:
        raise ValueError("full-takeover requires an explicitly confirmed --template")
    entries = assessment.get("data_inventory", {}).get("entries", [])
    template_dirs = {str(value).replace("\\", "/").strip("/") for value in template_spec.get("dirs", [])}
    has_data_root = any(value == "data" or value.startswith("data/") for value in template_dirs)
    mappings: list[dict] = []
    unmapped: list[dict] = []
    for entry in entries:
        source = str(entry.get("path", "")).replace("\\", "/")
        source_name = Path(source).name
        lower = source_name.casefold()
        target: str | None = None
        if lower in {"knowledge", "knowledges"} and "data/knowledge" in template_dirs:
            target = "data/knowledge"
        elif lower in {"vector", "vectors"} and "data/vector" in template_dirs:
            target = "data/vector"
        elif lower in {"content", "contents"} and "data/content" in template_dirs:
            target = "data/content"
        elif has_data_root and (lower in {"database", "db", "storage", "uploads", "upload"} or Path(source_name).suffix.casefold() in DATA_FILE_SUFFIXES):
            target = f"data/legacy/{source_name}"
        if target and source.casefold() != target.casefold():
            destination = root / target
            if destination.exists():
                unmapped.append({"source": source, "reason": "target_exists", "target": target})
                continue
            refs = _path_text_references(root, source, target)
            mappings.append({
                "source": source,
                "target": target,
                "kind": entry.get("kind", "directory"),
                "files": entry.get("files", 0),
                "bytes": entry.get("bytes", 0),
                "references": refs,
            })
        else:
            unmapped.append({"source": source, "reason": "not_safely_mapped"})

    if migrate_code:
        # Code relocation is opt-in. Only exact, well-known roots are considered.
        for source_name, target_name in CODE_ROOT_ALIASES.items():
            if source_name == target_name:
                continue
            source_path = root / source_name
            target_path = root / target_name
            if source_path.exists() and source_path != target_path and not target_path.exists():
                mappings.append({
                    "source": source_name, "target": target_name,
                    "kind": "directory", "files": 0, "bytes": 0,
                    "references": _path_text_references(root, source_name, target_name),
                    "category": "code",
                })

    return {
        "schema_version": 1,
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "project": str(root),
        "template": {
            "id": template_spec.get("id"), "version": template_spec.get("version"),
            "topology": template_spec.get("topology"), "scale": template_spec.get("scale"),
            "capabilities": list(template_spec.get("capabilities", [])),
        },
        "project_size": assessment.get("project_size", {}),
        "data_baseline": assessment.get("data_inventory", {}).get("digest", ""),
        "mappings": mappings,
        "unmapped": unmapped,
        "manual_review": [ref for item in mappings for ref in item.get("references", [])],
        "migrate_code": bool(migrate_code),
        "business_code_overwritten": False,
        "takeover_marker": f"{ADOPTION_DIR}/takeover.json",
    }


def _write_migration_plan(path: Path, plan: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _load_migration_plan(path: Path, root: Path) -> dict:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid migration plan: {path} ({exc})") from exc
    if plan.get("schema_version") != 1 or plan.get("project") != str(root):
        raise ValueError("migration plan does not belong to this project")
    return plan


def _verify_migration_plan(plan: dict, root: Path, assessment: dict, template_spec: dict) -> None:
    if plan.get("data_baseline") != assessment.get("data_inventory", {}).get("digest", ""):
        raise ValueError("data inventory changed; rerun --mode assess and create a new migration plan")
    expected = {
        "id": template_spec.get("id"), "version": template_spec.get("version"),
        "topology": template_spec.get("topology"), "scale": template_spec.get("scale"),
        "capabilities": list(template_spec.get("capabilities", [])),
    }
    if plan.get("template") != expected:
        raise ValueError("template selection changed; create a new migration plan")
    for item in plan.get("mappings", []):
        source = root / item["source"]
        target = root / item["target"]
        if not source.exists():
            raise ValueError(f"migration source is missing: {item['source']}")
        if target.exists():
            raise ValueError(f"migration target already exists: {item['target']}")
        for ref in item.get("references", []):
            ref_path = root / ref["file"]
            if not ref_path.is_file() or _sha256(ref_path) != ref.get("sha256"):
                raise ValueError(f"path reference changed: {ref['file']}; rebuild migration plan")


def _execute_migration(plan: dict, root: Path) -> dict:
    """Apply a migration plan with reversible moves and text backups."""
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = root / ADOPTION_DIR / "migration-backups" / stamp
    moved: list[dict] = []
    rewritten: list[dict] = []
    created_dirs: list[str] = []
    try:
        for item in plan.get("mappings", []):
            source = root / item["source"]
            target = root / item["target"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            moved.append({"source": item["source"], "target": item["target"]})
        for item in plan.get("mappings", []):
            for ref in item.get("references", []):
                path = root / ref["file"]
                raw = path.read_bytes()
                if hashlib.sha256(raw).hexdigest() != ref.get("sha256"):
                    raise ValueError(f"path reference changed during migration: {ref['file']}")
                backup = backup_root / ref["file"]
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup)
                old = ref["match"]
                new = ref["replacement"]
                text = raw.decode("utf-8")
                if "/" not in old and "\\" not in old:
                    text = re.sub(rf"(['\"]){re.escape(old)}\1", lambda match: f"{match.group(1)}{new}{match.group(1)}", text)
                else:
                    text = text.replace(old, new)
                path.write_text(text, encoding="utf-8")
                rewritten.append({"file": ref["file"], "backup": backup.relative_to(root).as_posix(), "old": old, "new": new})
        receipt = {
            "schema_version": 1, "created_at": stamp, "project": str(root),
            "plan_path": plan.get("plan_path", ""),
            "moved": moved, "rewritten": rewritten, "created_dirs": created_dirs,
            "backup_root": backup_root.relative_to(root).as_posix(),
        }
        receipt_path = root / ADOPTION_DIR / "receipts" / f"migration-{stamp}.json"
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"receipt": receipt_path.relative_to(root).as_posix(), **receipt}
    except Exception:
        for item in reversed(rewritten):
            path = root / item["file"]
            backup = root / item["backup"]
            if backup.is_file():
                shutil.copy2(backup, path)
        for item in reversed(moved):
            source = root / item["source"]
            target = root / item["target"]
            if target.exists() and not source.exists():
                source.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(source))
        raise


def _rollback_migration(receipt: dict, root: Path) -> None:
    """Undo a completed migration receipt in reverse order."""
    for item in reversed(receipt.get("rewritten", [])):
        path = root / item["file"]
        backup = root / item["backup"]
        if backup.is_file():
            shutil.copy2(backup, path)
    for item in reversed(receipt.get("moved", [])):
        source = root / item["source"]
        target = root / item["target"]
        if target.exists() and not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(source))


def _write_takeover_marker(root: Path, plan: dict, migration: dict, template_spec: dict) -> Path:
    state_dir = root / ADOPTION_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    marker = state_dir / "takeover.json"
    payload = {
        "mode": "full-takeover", "status": "complete",
        "template_id": template_spec.get("id"), "template_version": template_spec.get("version"),
        "topology": template_spec.get("topology"), "scale": template_spec.get("scale"),
        "capabilities": list(template_spec.get("capabilities", [])),
        "migration_plan": str(plan.get("plan_path", "")),
        "migration_receipt": str(migration.get("receipt", "")),
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "business_code_overwritten": False,
    }
    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    human = state_dir / "FULL_TAKEOVER.md"
    human.write_text(
        "# Full takeover\n\nThis project completed Guiyuan Vibecoding full takeover.\n"
        "Business code was not overwritten. See `takeover.json` and the migration receipt for evidence.\n",
        encoding="utf-8",
    )
    return marker


def _adoption_receipt(root: Path, assessment: dict, choices: dict[str, str], backups: list[dict],
                      copied: list[str], policies: dict | None = None, moved: list[dict] | None = None,
                      migration: dict | None = None, takeover_marker: str | None = None) -> Path:
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
        "migration": migration or {},
        "takeover_marker": takeover_marker,
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
            "Backups and receipt: `.guiyuan-vibecoding/backups/` + `.guiyuan-vibecoding/adoption.json`.",
        ]
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return moved


def _apply_adoption(root: Path, name: str, assessment: dict, choices: dict[str, str],
                    policies: dict | None = None, full_takeover: bool = False,
                    migration: dict | None = None, takeover_marker: str | None = None,
                    verify_baseline: bool = True) -> tuple[list[str], Path]:
    """Copy only explicitly managed workflow files, restoring backups on failure."""
    if verify_baseline:
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
        receipt = _adoption_receipt(root, assessment, choices, backups, copied, policies, moved, migration, takeover_marker)
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
               compat_policy: str | None = None, system_policy: str | None = None,
               install_hook: bool = True, template_spec: dict | None = None,
               migration_plan_path: Path | None = None, migration_confirm: bool = False,
               migrate_code: bool = False, force: bool = False) -> None:
    if assessment_path is None:
        raise ValueError("adopt requires --assessment <json from --mode assess>")
    assessment = _load_assessment(assessment_path, root)
    _validate_gate(assessment, compat_policy, system_policy)
    if compat_policy in {"progressive", "defer", "abandon"}:
        if compat_policy in {"progressive", "defer"}:
            decision = _write_deferred_decision(root, assessment, compat_policy)
            print(f"\nProgressive adoption recorded: {root}")
            print(f"  legacy workflow remains authoritative; decision saved at {decision.relative_to(root).as_posix()}")
        else:
            print(f"\nAdoption abandoned: {root} (Guiyuan Vibecoding will not be used in this project)")
        return
    if system_policy == "abandon":
        print(f"\nAdoption abandoned: {root} (Guiyuan Vibecoding will not be used in this project)")
        return

    full_takeover = compat_policy == "full-takeover"
    plan: dict | None = None
    if full_takeover:
        if not template_spec:
            raise ValueError("full-takeover requires an explicitly confirmed --template")
        if migration_plan_path is None:
            raise ValueError("full-takeover requires --migration-plan outside the project")
        _validate_external_plan_path(migration_plan_path, root)
        if not migration_confirm:
            plan = _build_migration_plan(root, assessment, template_spec, migrate_code=migrate_code)
            plan["plan_path"] = str(migration_plan_path)
            _write_migration_plan(migration_plan_path, plan)
            print(f"\n迁移计划已生成（尚未执行）：{migration_plan_path}")
            print(f"  数据候选：{len(plan.get('mappings', []))} 项可迁移，{len(plan.get('unmapped', []))} 项保留原位/待人工复核")
            print("  未移动数据、未修改路径、未应用管理层；请审核计划后再次传入 --migration-confirm。")
            return
        plan = _load_migration_plan(migration_plan_path, root)
        _verify_migration_plan(plan, root, assessment, template_spec)

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
    migration_receipt: dict | None = None
    _verify_assessment(assessment, root)
    if full_takeover and plan is not None:
        migration_receipt = _execute_migration(plan, root)
    try:
        if full_takeover and template_spec:
            _apply_template_layout(root, template_spec)
        copied, receipt = _apply_adoption(
            root,
            name,
            assessment,
            choices,
            policies=policies,
            full_takeover=full_takeover,
            migration=migration_receipt,
            takeover_marker=f"{ADOPTION_DIR}/takeover.json" if full_takeover else None,
            verify_baseline=False if full_takeover else True,
        )
        marker = None
        if full_takeover and plan is not None and migration_receipt is not None:
            marker = _write_takeover_marker(root, plan, migration_receipt, template_spec or {})
    except Exception:
        if migration_receipt is not None:
            _rollback_migration(migration_receipt, root)
        raise
    print(f"\nLossless adoption complete: {root}")
    print("  workflows: " + ", ".join(f"{key}={value}" for key, value in choices.items()))
    print(f"  copied {len(copied)} explicitly managed file(s); business code was not overwritten")
    if compat_policy == "full-takeover":
        print("  full takeover: legacy management overlays archived under .guiyuan-vibecoding/pre-adoption/")
        print("  migration: data moved according to the confirmed plan; path references were updated where unambiguous")
        print("  marker: .guiyuan-vibecoding/takeover.json")
    print(f"  receipt: {receipt.relative_to(root).as_posix()}")
    hook_status = _install_project_hook(root) if install_hook else "skipped (--hook none)"
    print(f"  project hook: {hook_status}")


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
        product_docs = ("prd.md", "acceptance.md", "ux.md", "behavior.md")
        technical_docs = ("iteration.md",)
        for rel in (Path("docs/01-product") / m["name"], Path("docs/02-technical") / m["name"]):
            d = root / rel
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                created.append(rel.as_posix() + "/")
            names = product_docs if rel.parts[1] == "01-product" else technical_docs
            for filename in names:
                p = d / filename
                if not p.exists():
                    title = f"{m['name'].replace('-', ' ').title()} {p.stem.title()}"
                    p.write_text(f"# {title}\n\n> Placeholder: fill in for this project module.\n", encoding="utf-8")
                    created.append((rel / filename).as_posix())
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


def _has_uv() -> bool:
    ok, _ = _run_quiet(["uv", "--version"])
    return ok


def _install_uv() -> tuple[bool, str]:
    """Best-effort uv install for the auto-dependency path; never required."""
    if _has_uv():
        return True, "uv already installed"
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "uv"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode == 0 and _has_uv():
            return True, "uv installed via pip"
    except (OSError, subprocess.SubprocessError):
        pass
    if os.name == "nt":
        try:
            r = subprocess.run(
                ["winget", "install", "-e", "--id", "astral-sh.uv",
                 "--accept-source-agreements", "--accept-package-agreements"],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if r.returncode == 0 and _has_uv():
                return True, "uv installed via winget"
        except (OSError, subprocess.SubprocessError):
            pass
    return False, "uv install failed; python -m venv remains the fallback"


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


def _install_project_hook(root: Path) -> str:
    """Install the project-scoped Codex SessionStart hook (advisory, idempotent).

    This is the agent layer, not a Git hook: it only reads the project and injects
    a detection-based advisory on SessionStart. It is written after the confirmed
    adopt/scaffold write because it depends on tools/vcm_session_hook.py and must
    not create a dependency or Git side effect for the business code.
    """
    runner = root / "tools" / "vcm_session_hook.py"
    if not runner.is_file():
        src = ASSETS / "tools" / "vcm_session_hook.py"
        if not src.is_file():
            return "skip (runner not bundled)"
        runner.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, runner)
    codex = root / ".codex"
    codex.mkdir(parents=True, exist_ok=True)
    py = next(
        (p for p in (root / ".venv" / "Scripts" / "python.exe",
                     root / "venv" / "Scripts" / "python.exe")
         if p.is_file()),
        Path(sys.executable),
    )
    command = f'"{py}" "{runner.resolve()}"'
    hooks = {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear|compact",
                    "hooks": [
                        {"type": "command", "command": command, "timeout": 20},
                    ],
                }
            ]
        }
    }
    target = codex / "hooks.json"
    data = json.dumps(hooks, ensure_ascii=False, indent=2) + "\n"
    if target.is_file() and target.read_text(encoding="utf-8") == data:
        return "unchanged"
    target.write_text(data, encoding="utf-8")
    return f"installed ({target.relative_to(root).as_posix()})"


def _hook_methods_text() -> str:
    """Local common Agent hook setups, so the agent reads this instead of searching."""
    return (
        "Common Agent project-scoped hook setups (Guiyuan Vibecoding defaults to Codex):\n"
        "  Codex:       <project>/.codex/hooks.json  (SessionStart/PreToolUse/PostToolUse/PreCommit;\n"
        "               requires a trusted project + user-level [features].hooks)\n"
        "  Claude Code: <project>/.claude/settings.json  (PreToolUse/PostToolUse/Stop/SubagentStop)\n"
        "  Cursor:      <project>/.cursor/rules or .cursorrules  (rules, not lifecycle events)\n"
        "  Git:         <project>/.git/hooks/pre-commit  (commit gate; hard)\n"
        "  VCM default: Codex SessionStart advisory (soft). Strict blocking uses a PreToolUse/commit hook.\n"
        "Full local reference: docs/02-technical/agent-hook-methods.md"
    )


def _known_skill_roots() -> list[tuple[str, Path]]:
    """Known candidates for read-only discovery. Never a complete registry."""
    candidates: list[tuple[str, Path]] = []
    codex_env = os.environ.get("CODEX_HOME")
    codex = Path(codex_env).expanduser() / "skills" if codex_env else Path.home() / ".codex" / "skills"
    candidates.append(("Codex", codex))
    candidates.append(("Claude Code", Path.home() / ".claude" / "skills"))
    candidates.append(("Cursor", Path.home() / ".cursor" / "skills"))
    return candidates


def _resolve_skills_root(skills_dir: str | None) -> Path | None:
    if skills_dir:
        return Path(skills_dir).expanduser().resolve()
    env = os.environ.get(VIBECODING_SKILLS_HOME)
    if env:
        return Path(env).expanduser().resolve()
    return None


def _discover_skill_roots() -> None:
    print("== known agent skill roots (read-only, not exhaustive) ==")
    found = False
    for label, root in _known_skill_roots():
        status = "exists" if root.exists() else "not found"
        print(f"  {label}: {root} ({status})")
        found = found or root.exists()
    if not found:
        print("  none found; use --skills-dir <path> for an explicit global directory")
    else:
        print("  confirm one path with --skills-dir <path> before writing")


def _copy_close_loop_skill(dest: Path, force: bool) -> Path | None:
    if dest.exists() and not force:
        return None
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(SKILL_ASSETS, dest)
    template = dest / "SKILL.md.template"
    if template.is_file():
        template.replace(dest / "SKILL.md")
    return dest


def _handle_close_loop_install(root: Path, skills_dir: str | None,
                               location: str, force: bool) -> tuple[Path | None, str]:
    if location == "skip":
        return None, "skipped"
    if location == "global":
        # The public distribution intentionally has one discoverable Skill. Keep the explicit
        # legacy option as a compatibility input, but materialize the close-loop payload locally
        # instead of recreating a second global discovery entry.
        location = "project"
    explicit_root = _resolve_skills_root(skills_dir)
    if location == "auto" and explicit_root:
        location = "project"
    dest = _copy_close_loop_skill(root / ADOPTION_DIR / "skills" / "guiyuan-iteration-close-loop", force)
    return dest, "project-local skills dir: .guiyuan-vibecoding/skills (public global entry remains singular)"


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


def _load_intent_map() -> dict:
    try:
        return _load_toml(INTENT_MAP)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _normalize_intent(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold())


def _resolve_intent(text: str | None, explicit_profile: str | None) -> dict:
    """Deterministically map a free-text description to one built-in profile."""
    if explicit_profile:
        return {
            "profile": explicit_profile,
            "source": "explicit",
            "signals": [],
            "score": 100,
            "confidence": "high",
            "description": text or "",
        }
    normalized = _normalize_intent(text or "")
    best_profile = "default"
    best_score = 0
    second_score = 0
    best_signals: list[str] = []
    for profile, spec in _load_intent_map().get("profile", {}).items():
        profile_score = 0
        hits: list[str] = []
        for raw_signal in spec.get("signals", []) or []:
            signal = raw_signal.strip().casefold()
            if signal and signal in normalized:
                hits.append(raw_signal.strip())
                profile_score += max(3, len(signal))
        if profile_score > best_score:
            second_score = best_score
            best_profile = profile
            best_score = profile_score
            best_signals = hits
        elif profile_score > second_score:
            second_score = profile_score
    confidence = (
        "high"
        if best_score >= 6 or (best_score >= 3 and second_score == 0)
        else "medium" if best_score >= 3 else "low"
    )
    return {
        "profile": best_profile,
        "source": "intent-map",
        "signals": best_signals,
        "score": best_score,
        "confidence": confidence,
        "description": text or "",
    }


def _write_intent_plan(root: Path, plan: dict) -> Path:
    state_dir = root / ADOPTION_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "description_hash": hashlib.sha256(plan.get("description", "").encode("utf-8")).hexdigest()[:16],
        **plan,
    }
    path = state_dir / "scaffold-plan.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


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


def _load_template_spec(template: str | None, scale: str | None, capabilities: list[str]) -> dict:
    """Load a composable topology/scale/capability specification for scaffold mode."""
    if not template or template == "default":
        return {}
    path = TOPOLOGIES_DIR / f"{template}.toml"
    if not path.exists() and Path(template).suffix == ".toml":
        path = Path(template)
    if not path.exists():
        raise ValueError(f"template not found: {template}")
    with path.open("rb") as fh:
        topology = tomllib.load(fh)
    chosen_scale = scale or "medium"
    scale_path = SCALES_DIR / f"{chosen_scale}.toml"
    if not scale_path.exists():
        raise ValueError(f"scale not found: {chosen_scale}")
    with scale_path.open("rb") as fh:
        scale_spec = tomllib.load(fh)
    if chosen_scale not in {p.stem for p in SCALES_DIR.glob("*.toml")}:
        raise ValueError(f"scale not found: {chosen_scale}")
    add_dirs = list(topology.get("core_dirs", [])) + list(scale_spec.get("add_dirs", []))
    optional_dirs = list(topology.get("optional_dirs", [])) + list(scale_spec.get("optional_dirs", []))
    profile: dict = {"docs_stubs": [], "red_lines": [], "constraints": [], "gitignore_add": []}
    selected_caps: list[str] = []
    for capability in capabilities:
        cap_path = CAPABILITIES_DIR / f"{capability}.toml"
        if not cap_path.exists():
            raise ValueError(f"capability not found: {capability}")
        with cap_path.open("rb") as fh:
            cap = tomllib.load(fh)
        add_dirs.extend(cap.get("add_dirs", []))
        optional_dirs.extend(cap.get("optional_dirs", []))
        _merge_profile(profile, cap)
        selected_caps.append(capability)
    # De-duplicate while preserving declaration order.
    add_dirs = list(dict.fromkeys(str(p).replace("\\", "/") for p in add_dirs if p))
    optional_dirs = list(dict.fromkeys(str(p).replace("\\", "/") for p in optional_dirs if p and p not in add_dirs))
    return {
        "id": topology.get("id", template),
        "version": topology.get("version", "1.0.0"),
        "topology": topology.get("topology", template),
        "scale": chosen_scale,
        "runtime": topology.get("runtime", []),
        "surface": topology.get("surface", []),
        "capabilities": selected_caps,
        "dirs": add_dirs,
        "optional_dirs": optional_dirs,
        "paths": topology.get("paths", {}),
        "scale_description": scale_spec.get("description", ""),
        "profile": profile,
    }


def _toml_array(values: list[str]) -> str:
    return "[" + ", ".join(json.dumps(str(v), ensure_ascii=False) for v in values) + "]"


def _write_template_records(root: Path, spec: dict) -> list[str]:
    """Write the machine manifest and lock record for a generated topology."""
    state_dir = root / ADOPTION_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    state = "docs/04-workflow/NOW.md" if (root / "docs" / "04-workflow" / "NOW.md").is_file() else "NOW.md"
    ledger = "docs/04-workflow/changelog.md" if (root / "docs" / "04-workflow" / "changelog.md").is_file() else "CHANGELOG.md"
    required = list(dict.fromkeys([*spec.get("dirs", []), "docs"]))
    lines = [
        "# Generated by Guiyuan Vibecoding; edit paths when adopting a different layout.",
        f"template_id = {json.dumps(spec['id'])}",
        f"template_version = {json.dumps(spec['version'])}",
        f"topology = {json.dumps(spec['topology'])}",
        f"scale = {json.dumps(spec['scale'])}",
        f"runtime = {_toml_array(spec['runtime'])}",
        f"surface = {_toml_array(spec['surface'])}",
        f"capabilities = {_toml_array(spec['capabilities'])}",
        "",
        "[paths]",
        "human_docs = \"docs\"",
        "machine_state = \".guiyuan-vibecoding\"",
        "agent_rules = \"AGENTS.md\"",
        f"project_state = {json.dumps(state)}",
        f"changelog = {json.dumps(ledger)}",
        "",
        "[artifacts]",
        f"project_state = {json.dumps(state)}",
        f"product_state = {json.dumps(state)}",
        f"changelog = {json.dumps(ledger)}",
        "red_lines = \"docs/00-system/constitution/red-lines.md\"",
        "roadmap = \"docs/04-workflow/roadmap.md\"",
        "archive = \"docs/04-workflow/archive\"",
        "registry = \".guiyuan-vibecoding/registry\"",
        "anchors = \".guiyuan-vibecoding/anchors\"",
        "receipts = \".guiyuan-vibecoding/receipts\"",
        "doc_index = \".guiyuan-vibecoding/indexes/doc-tree.json\"",
        "",
        "[roots]",
        "human_docs = \"docs\"",
        "machine_state = \".guiyuan-vibecoding\"",
        "registry = \".guiyuan-vibecoding/registry\"",
        "anchors = \".guiyuan-vibecoding/anchors\"",
        "receipts = \".guiyuan-vibecoding/receipts\"",
        "indexes = \".guiyuan-vibecoding/indexes\"",
        "views = \".guiyuan-vibecoding/views\"",
        f"code = {_toml_array(spec.get('paths', {}).get('code', []))}",
        f"tests = {_toml_array(spec.get('paths', {}).get('tests', ['tests']))}",
        "",
        "[structure]",
        f"required = {_toml_array(required)}",
        f"optional = {_toml_array(spec.get('optional_dirs', []))}",
        "placeholder = \".gitkeep\"",
    ]
    created: list[str] = []
    manifest = state_dir / "project-manifest.toml"
    if not manifest.exists():
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
        created.append(str(manifest.relative_to(root)).replace("\\", "/"))
    lock = state_dir / "template.lock.toml"
    if not lock.exists():
        lock.write_text(
            "# Source template identity; project state is intentionally not locked here.\n"
            f"template_id = {json.dumps(spec['id'])}\n"
            f"template_version = {json.dumps(spec['version'])}\n"
            f"topology = {json.dumps(spec['topology'])}\n"
            f"scale = {json.dumps(spec['scale'])}\n",
            encoding="utf-8",
        )
        created.append(str(lock.relative_to(root)).replace("\\", "/"))
    return created


def _apply_template_layout(root: Path, spec: dict) -> list[str]:
    """Materialize topology directories and records without overwriting user files."""
    if not spec:
        return []
    created: list[str] = []
    for raw in spec.get("dirs", []):
        rel = Path(raw)
        directory = root / rel
        directory.mkdir(parents=True, exist_ok=True)
        marker = directory / ".gitkeep"
        if not any(directory.iterdir()):
            marker.write_text("", encoding="utf-8")
            created.append((rel / ".gitkeep").as_posix())
    usage = root / "docs" / "03-reference" / "template-usage.md"
    if not usage.exists():
        usage.parent.mkdir(parents=True, exist_ok=True)
        usage.write_text(
            "# Template usage\n\n"
            f"This project was generated from `{spec['id']}` (scale: `{spec['scale']}`).\n\n"
            "The machine-readable layout and artifact mapping live in "
            "`.guiyuan-vibecoding/project-manifest.toml`. Keep project progress in the "
            "mapped project-state, changelog, roadmap, receipts, and red-line artifacts; "
            "do not use this file as a progress ledger. The generated registry and doc-tree index "
            "support derived architecture/progress views; REQ/PLAN/QA/RELEASE confirmations are "
            "recorded with tools/anchor.py under `.guiyuan-vibecoding/anchors/`.\n",
            encoding="utf-8",
        )
        created.append("docs/03-reference/template-usage.md")
    created.extend(_write_template_records(root, spec))
    return created


def _ensure_machine_dirs(root: Path) -> list[str]:
    """Create the stable machine layer without imposing a code layout.

    These directories are deliberately boring: state is written by tools, while empty
    directories remain visible in Git through ``.gitkeep``.  The function is idempotent and
    never replaces user files.
    """
    created: list[str] = []
    for rel in (
        ".guiyuan-vibecoding/registry",
        ".guiyuan-vibecoding/state",
        ".guiyuan-vibecoding/state/tasks",
        ".guiyuan-vibecoding/anchors",
        ".guiyuan-vibecoding/receipts",
        ".guiyuan-vibecoding/indexes",
        ".guiyuan-vibecoding/views",
    ):
        directory = root / rel
        directory.mkdir(parents=True, exist_ok=True)
        if not any(directory.iterdir()):
            (directory / ".gitkeep").write_text("", encoding="utf-8")
            created.append(f"{rel}/.gitkeep")
    return created


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


def _apply_profile(target: Path, merged: dict, template_spec: dict | None = None) -> list[str]:
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
    spec = template_spec or {}
    if ensure_gitignore:
        had_gitignore = gi.exists()
        changed = ensure_gitignore(
            gi,
            topology=spec.get("topology"),
            scale=spec.get("scale"),
            capabilities=spec.get("capabilities", []),
            extra=merged.get("gitignore_add", []),
            replace=not gi.exists(),
        )
        if changed:
            created.append(".gitignore" if not had_gitignore else ".gitignore (profile overlay)")
    elif merged.get("gitignore_add") and gi.exists():
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

    # A project can already follow the VCM/Guiyuan Markdown workflow without
    # carrying an installed Skill. Treat it as managed documentation, not as
    # an empty or generic project, so the existing keep/map/managed gate applies.
    md_markers = (root / "AGENTS.md", root / "NOW.md", root / "CHANGELOG.md")
    if all(p.is_file() for p in md_markers) and (root / "docs" / "04-workflow").is_dir():
        return {"type": "md-managed", "runtime": "none", "label": DETECT_LABELS["md-managed"]}

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
    if runtime == "python" and not tools.get("uv"):
        print("  note: uv is recommended for Python projects (shared cache + managed Python); .venv still works without it")
    needed = {"python"} if runtime == "python" else {"node"} if runtime == "node" else set()
    missing = [k for k in sorted(needed) if not tools.get(k)]
    print("  needed for this project: " + (", ".join(sorted(needed)) or "none"))
    print("  missing: " + (", ".join(missing) or "none"))
    return missing


def _command_inventory(command: str, *args: str) -> dict:
    """Read one executable's version/path without installing or changing state."""
    path = shutil.which(command)
    ok, output = _run_quiet([command, *args])
    return {
        "command": command,
        "installed": bool(path or ok),
        "path": path or "",
        "version": output.splitlines()[0][:200] if ok and output else "",
    }


def _lines_from_command(command: list[str]) -> list[str]:
    ok, output = _run_quiet(command)
    if not ok or not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def _existing_paths(candidates: list[tuple[str, Path]]) -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    for label, path in candidates:
        if not str(path):
            continue
        try:
            resolved = str(path.expanduser().resolve())
        except OSError:
            resolved = str(path)
        key = resolved.casefold()
        if key in seen or not Path(resolved).exists():
            continue
        seen.add(key)
        found.append({"label": label, "path": resolved})
    return found


def _environment_inventory() -> dict:
    """Whole-machine metadata inventory for the post-intent, user-authorized preflight.

    This intentionally checks only executable metadata, known shared roots, and environment
    listings.  It does not read project source, install software, or alter PATH/configuration.
    """
    agents = []
    for label, command in AGENT_COMMANDS:
        item = _command_inventory(command, "--version")
        roots = []
        if label == "Codex":
            roots.extend([Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()])
        elif label == "Claude Code":
            roots.append(Path.home() / ".claude")
        elif label == "Cursor":
            roots.append(Path.home() / ".cursor")
        elif label == "Windsurf":
            roots.append(Path.home() / ".windsurf")
        item["roots"] = _existing_paths([(label, root) for root in roots])
        if item["installed"] or item["roots"]:
            agents.append({"name": label, **item})

    skill_candidates = list(_known_skill_roots())
    for env_name in (VIBECODING_SKILLS_HOME, "CODEX_HOME", "CLAUDE_HOME"):
        raw = os.environ.get(env_name)
        if raw:
            base = Path(raw).expanduser()
            skill_candidates.append((env_name, base / "skills" if env_name != VIBECODING_SKILLS_HOME else base))
    shared_skill_dirs = _existing_paths(skill_candidates)

    python_versions = _lines_from_command(["py", "-0p"])
    python_paths: list[str] = []
    for line in python_versions:
        candidate = line.split()[-1] if line.split() else ""
        if re.search(r"([A-Za-z]:\\|/).*(python|Python)(?:\.exe)?$", candidate):
            python_paths.append(candidate)
    python_path_lines = _lines_from_command(["where", "python"])
    python_paths.extend(python_path_lines)
    virtual_envs = _existing_paths([
        ("VIRTUAL_ENV", Path(os.environ["VIRTUAL_ENV"]))
        for _ in [0] if os.environ.get("VIRTUAL_ENV")
    ])
    python_commands = {
        "py": _command_inventory("py", "-3", "--version"),
        "python": _command_inventory("python", "--version"),
        "uv-python": _command_inventory("uv", "python", "find"),
    }
    uv_python_list = _lines_from_command(["uv", "python", "list"])

    node_paths = _lines_from_command(["where", "node"])
    node_commands = {
        "node": _command_inventory("node", "--version"),
        "npm": _command_inventory("npm", "--version"),
        "nvm": _command_inventory("nvm", "version"),
        "fnm": _command_inventory("fnm", "--version"),
    }
    shared_runtime_candidates = [
        ("Python virtualenvs", Path.home() / ".virtualenvs"),
        ("Conda environments", Path.home() / ".conda" / "envs"),
    ]
    for label, env_name, suffix in (
        ("Python user installs", "LOCALAPPDATA", Path("Programs") / "Python"),
        ("npm global", "APPDATA", Path("npm")),
        ("NVM", "NVM_HOME", Path()),
        ("FNM", "FNM_DIR", Path()),
    ):
        raw = os.environ.get(env_name)
        if raw:
            shared_runtime_candidates.append((label, Path(raw).expanduser() / suffix))
    shared_runtime_roots = _existing_paths(shared_runtime_candidates)
    return {
        "read_only": True,
        "agents": agents,
        "shared_skill_dirs": shared_skill_dirs,
        "python": {
            "commands": python_commands,
            "interpreters": list(dict.fromkeys(python_paths))[:20],
            "uv_python_list": uv_python_list[:20],
            "virtual_envs": virtual_envs,
        },
        "node": {"commands": node_commands, "install_paths": list(dict.fromkeys(node_paths))[:20]},
        "shared_runtime_roots": shared_runtime_roots,
        "uv": _command_inventory("uv", "--version"),
        "github_cli": _command_inventory("gh", "--version"),
    }


def _print_environment_inventory(inventory: dict) -> None:
    """Human summary for the authorized inventory; avoid dumping internal probe details."""
    print("== 全机环境只读盘点 ==")
    agent_names = [item["name"] for item in inventory.get("agents", [])]
    print("  Agent：" + ("、".join(agent_names) if agent_names else "未发现已知命令/目录"))
    skill_dirs = inventory.get("shared_skill_dirs", [])
    print("  共享 Skill 目录：" + ("、".join(item["path"] for item in skill_dirs) if skill_dirs else "未发现"))
    python = inventory.get("python", {})
    interpreters = python.get("interpreters", [])
    print("  Python：" + ("、".join(interpreters[:8]) if interpreters else "未发现独立解释器"))
    if python.get("uv_python_list"):
        print("  UV 管理的 Python：" + "、".join(python["uv_python_list"][:8]))
    node_paths = inventory.get("node", {}).get("install_paths", [])
    print("  Node：" + ("、".join(node_paths[:8]) if node_paths else "未发现 PATH 中的 node"))
    uv = inventory.get("uv", {})
    gh = inventory.get("github_cli", {})
    print(f"  UV：{uv.get('version') or ('已安装' if uv.get('installed') else '未安装')}")
    print(f"  GitHub CLI：{gh.get('version') or ('已安装' if gh.get('installed') else '未安装')}")
    print("  以上仅为只读检查；尚未安装、切换或修改任何环境。")


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
        "> Managed with the Guiyuan Vibecoding iteration loop "
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
    ap.add_argument("--migration-plan", default=None,
                    help="external JSON migration plan for full-takeover (plan only unless confirmed)")
    ap.add_argument("--migration-confirm", action="store_true",
                    help="after reviewing --migration-plan, apply the reversible migration")
    ap.add_argument("--migrate-code", action="store_true",
                    help="include only exact known code-root aliases in a full-takeover plan")
    ap.add_argument("--workflow", action="append", default=[], metavar="name=keep|map|managed",
                    help="adoption choice (repeatable): startup/state/ledger/methodology/tooling")
    ap.add_argument("--existing-system", action="append", default=[], metavar="NAME",
                    help="similar project-management system declared by the user (assess; repeatable)")
    ap.add_argument("--compat-policy", choices=list(COMPAT_POLICIES), default=None,
                    help="low-match decision: full-takeover|takeover|defer|abandon")
    ap.add_argument("--system-policy", choices=list(SYSTEM_POLICIES), default=None,
                    help="similar-system decision: keep-map|auto-takeover|abandon")
    ap.add_argument("--json", action="store_true", help="print assessment JSON (assess mode only)")
    ap.add_argument("--environment-scan", action="store_true",
                    help="after user authorization, inspect whole-machine agent/runtime metadata read-only")
    ap.add_argument("--force", action="store_true", help="overwrite existing management files")
    ap.add_argument("--intent", default=None,
                    help="one-sentence project description used by scaffold intent resolution")
    ap.add_argument("--dry-run", action="store_true",
                    help="resolve scaffold intent/profile and print the plan without writing")
    ap.add_argument("--skills-dir", default=None,
                    help="explicit global skills root; writes only when the user chose it")
    ap.add_argument("--skill-location", choices=["auto", "project", "global", "skip"], default="auto",
                    help="auto=project unless --skills-dir/VIBECODING_SKILLS_HOME; "
                         "project=.guiyuan-vibecoding/skills; global=legacy alias for project; skip=none")
    ap.add_argument("--discover-skills", action="store_true",
                    help="list known agent skill roots read-only and exit")
    ap.add_argument("--no-install-skill", action="store_true", help="alias for --skill-location skip")
    ap.add_argument("--hook", choices=["advisory", "none"], default="advisory",
                    help="project-scoped agent hook: advisory=install SessionStart reminder (default); "
                         "none=skip")
    ap.add_argument("--hook-methods", action="store_true",
                    help="print local common Agent hook setup methods and exit")
    ap.add_argument("--module", action="append", default=[], metavar="name=kw1,kw2",
                    help="business modules (scaffold only; repeatable)")
    ap.add_argument("--code", action="append", default=[], metavar="name=dir",
                    help="module code dir (scaffold only, repeatable)")
    ap.add_argument("--template", default=None,
                    help="template: default|python-service|web-app|monorepo|cli|composite, or a custom topology TOML")
    ap.add_argument("--scale", choices=["small", "medium", "large"], default=None,
                    help="template scale (default: medium for an explicit topology)")
    ap.add_argument("--capability", action="append", default=[],
                    help="composable capability overlay (repeatable): rag|vector-db|worker|auth|admin|payments|content-pipeline|local-deploy")
    ap.add_argument("--python", default="auto", metavar="auto|system|install|<path>",
                    help="Python runtime: auto=detect user's existing (default); system=no fallback; "
                         "install=auto-deploy (uv/winget); or an explicit interpreter path")
    ap.add_argument("--env", choices=["auto", "shared", "isolated", "reuse", "skip", "create", "uv"],
                    default="auto",
                    help="dependency policy: auto=reuse existing/uv venv/project-local (default); "
                         "uv=prefer uv and guide its install; shared=--system-site-packages; "
                         "isolated=clean local .venv; reuse=existing only; skip=none "
                         "(legacy create/uv mapped)")
    ap.add_argument("--deps", choices=["auto", "commands", "skip"], default="auto",
                    help="dependency installs: auto=run them (default); commands=print only; skip=none")
    ap.add_argument("--profile", default=None,
                    help="project-type preset: script|plugin|page|default|saas|c-end|vector-db|"
                         "cli-tool|content-site|ecommerce|admin-dashboard|bot, or a custom .toml path")
    ap.add_argument("--dimension", action="append", default=[], metavar="key=value",
                    help="dimension override (repeatable): deploy/data/runtime/surface")
    ap.add_argument("--github", default=None, help="GitHub repo URL to set as origin")
    ap.add_argument("--push", action="store_true", help="attempt initial push after git init/remote")
    ap.add_argument("--no-venv", action="store_true", help="alias for --env skip")
    args = ap.parse_args()

    if args.hook_methods:
        print(_hook_methods_text())
        return

    if args.discover_skills:
        _discover_skill_roots()
        return
    if args.dry_run:
        plan = _resolve_intent(args.intent, args.profile)
        if args.template:
            try:
                spec = _load_template_spec(args.template, args.scale, args.capability)
            except ValueError as exc:
                ap.error(str(exc))
            plan["template"] = {
                "id": spec.get("id"), "topology": spec.get("topology"),
                "scale": spec.get("scale"), "runtime": spec.get("runtime", []),
                "surface": spec.get("surface", []), "capabilities": spec.get("capabilities", []),
                "directories": spec.get("dirs", []),
            }
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    target = Path(args.target).resolve()
    name = args.name or target.name
    if args.mode == "assess" and not target.is_dir():
        ap.error("assess requires an existing project directory")
    target.mkdir(parents=True, exist_ok=True)

    mode = args.mode
    if mode == "auto":
        if _has_content(target):
            mode = "assess"
        elif not args.intent:
            # The conversation must ask what the user wants before a scaffold can be chosen.
            print("== 初始化启动中... ==")
            print("Hi，我是你的 AI 项目经理，可以创建新项目或接管已有项目。")
            print(f"项目位置：{target}")
            print(f"项目名称：{name}")
            print("请先告诉我，你想做一个什么样的产品？例如：想做一个喝水微信小程序，提醒我每天喝水。")
            print("当前未写入任何文件；收到产品描述后再生成模板建议。")
            return
        else:
            mode = "scaffold"
    detected = {"type": "generic", "runtime": "none", "label": DETECT_LABELS["generic"]}
    if mode in {"assess", "adopt"}:
        detected = detect_project_type(target)
    if mode == "assess":
        environment = _environment_inventory() if args.environment_scan else None
        _print_assessment(
            _assessment(target, detected, args.existing_system, args.intent, environment, name),
            args.json,
        )
        return
    if mode == "adopt":
        if args.environment_scan:
            _print_environment_inventory(_environment_inventory())
        try:
            adopt_template = None
            if args.template:
                adopt_template = _load_template_spec(args.template, args.scale, args.capability)
            _run_adopt(
                target,
                name,
                Path(args.assessment).resolve() if args.assessment else None,
                args.workflow,
                args.compat_policy,
                args.system_policy,
                install_hook=args.hook == "advisory",
                template_spec=adopt_template,
                migration_plan_path=Path(args.migration_plan).resolve() if args.migration_plan else None,
                migration_confirm=args.migration_confirm,
                migrate_code=args.migrate_code,
                force=args.force,
            )
        except ValueError as exc:
            ap.error(str(exc))
        return

    if mode == "scaffold" and not args.profile and not args.template:
        if not args.intent:
            print("== 初始化启动中... ==")
            print(f"项目位置：{target}")
            print(f"项目名称：{name}")
            print("请先告诉我，你想做一个什么样的产品；VCM 不会用默认模板替你决定。")
        else:
            _print_scaffold_candidates(target, name, args.intent)
        return

    intent_plan = None
    if mode == "scaffold":
        intent_plan = _resolve_intent(args.intent, args.profile)

    template_spec = {}
    if mode == "scaffold" and args.template:
        try:
            template_spec = _load_template_spec(args.template, args.scale, args.capability)
        except ValueError as exc:
            ap.error(str(exc))

    # --- copy management files -------------------------------------------
    if args.environment_scan:
        _print_environment_inventory(_environment_inventory())
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
    if mode == "scaffold" and not profile and intent_plan:
        profile = intent_plan["profile"]
    dimensions = list(args.dimension)
    # A topology owns its physical layout.  Do not inject surface dimensions here because
    # those dimensions also create legacy module paths such as apps/web.
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
        if intent_plan and args.intent:
            intent_path = _write_intent_plan(target, intent_plan)
            print(f"  intent plan: {intent_path.relative_to(target).as_posix()} "
                  f"-> {intent_plan['profile']} ({intent_plan['confidence']})")
    if template_spec:
        _merge_profile(merged, template_spec.get("profile", {}))
    profile_created = _apply_profile(target, merged, template_spec)

    if mode == "scaffold":
        _fill_routing_tables(target, modules)
    remaining = _replace_placeholders(target, name, scope=(copied if mode == "adopt" else None))
    arch = _write_r1_archive(target, mode)
    if mode == "scaffold":
        created_dirs = _ensure_module_dirs(target, modules)
    else:
        created_dirs = []
    template_created = _apply_template_layout(target, template_spec) if mode == "scaffold" else []
    machine_created: list[str] = []
    if mode == "scaffold":
        # The machine layer is shared by every topology, including the legacy default.
        machine_created = _ensure_machine_dirs(target)
        if not template_spec:
            # Keep ``--template default`` compatible while still giving new projects a
            # manifest that adapters can use when their physical layout changes.
            default_spec = {
                "id": "default", "version": "1.0.0", "topology": "default",
                "scale": args.scale or "medium", "runtime": [], "surface": [],
                "capabilities": [], "dirs": [], "paths": {},
            }
            template_created.extend(_write_template_records(target, default_spec))
        registry_tool = target / "tools" / "project_registry.py"
        if registry_tool.is_file():
            try:
                subprocess.run(
                    [sys.executable, str(registry_tool), "--root", str(target), "--write"],
                    cwd=target,
                    check=True,
                )
                template_created.extend([
                    ".guiyuan-vibecoding/registry/artifacts.toml",
                    ".guiyuan-vibecoding/registry/modules.toml",
                    ".guiyuan-vibecoding/indexes/doc-tree.json",
                ])
            except (OSError, subprocess.CalledProcessError) as exc:
                print(f"  project registry: failed ({exc}); rerun python tools/project_registry.py --write")
    if template_created:
        print("  template layout: " + ", ".join(template_created))
    if machine_created:
        print("  machine state: " + ", ".join(machine_created))
    env_status = _write_env_example(target, detected["type"] if mode == "adopt" else (profile or "generic"), merged)

    gen = target / "tools" / "gen_llms_txt.py"
    if gen.exists():
        subprocess.run([sys.executable, str(gen)], cwd=target, check=True)

    # The project home is a derived, static view.  Generate it during every
    # bootstrap so a freshly adopted/scaffolded project can be opened directly
    # as ``status.html``; no 8010 listener is needed.
    home = target / "tools" / "render_project_home.py"
    if home.is_file():
        try:
            subprocess.run([sys.executable, str(home)], cwd=target, check=True)
            print("  static project home: generated (status.html)")
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"  static project home: failed ({exc}); rerun python tools/render_project_home.py")

    # --- environment preflight + dependency handling ----------------------
    runtime = (
        template_spec["runtime"][0]
        if template_spec and len(template_spec.get("runtime", [])) == 1
        else _effective_runtime(profile, dimensions, detected, mode)
    )
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
                    if runtime == "python" and not _has_uv():
                        install_commands.append(
                            f"uv is recommended: {python_exe} -m pip install --user uv"
                        )
                    install_commands.append(
                        "uv venv .venv" if runtime == "python" else f"{python_exe} -m venv .venv"
                    )
                else:
                    install_commands.append("install Python 3.12 (uv python install 3.12 or winget), then python -m venv .venv")
            elif python_exe is not None and env_mode != "skip":
                try:
                    uv_note = ""
                    if env_mode in ("auto", "uv") and args.deps == "auto":
                        uv_ready, uv_note = _install_uv()
                        if not uv_ready:
                            uv_note += " (python -m venv fallback)"
                    venv_status = _handle_venv(target, env_mode, python_exe)
                    if uv_note:
                        print(f"  uv: {uv_note}")
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

    skill_location = "skip" if args.no_install_skill else args.skill_location
    skill_dest, skill_note = _handle_close_loop_install(
        target,
        args.skills_dir,
        skill_location,
        args.force,
    )
    hook_status = _install_project_hook(target) if args.hook == "advisory" else "skipped (--hook none)"

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
    print(f"  project hook: {hook_status}")
    print("  hook reminder: 项目级 hook 默认开启，作为 SessionStart 软约束（提醒 VCM 纪律、识别空文件夹意图）。")
    print("                 无需再搜索：常用 Agent hook 设置方法见 docs/02-technical/agent-hook-methods.md，"
          "或运行 bootstrap.py --hook-methods 打开本地清单。")
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
    if skill_dest:
        try:
            shown = skill_dest.relative_to(target)
        except ValueError:
            shown = skill_dest
        print(f"  close-loop skill: {shown} ({skill_note})")
    elif skill_note == "skipped":
        print("  close-loop skill: skipped")
    else:
        print("  close-loop skill: already present, not reinstalled")
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
