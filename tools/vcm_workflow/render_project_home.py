#!/usr/bin/env python3
"""Render the installed project-home template into a static ``status.html``.

The project repository remains the only source of truth. This tool reads Markdown,
configuration and read-only Git metadata, serialises the derived ``PROJECT`` object into
the visual template, and writes one browser-openable HTML file. No HTTP server or port is
required.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from project_manifest import artifact_path
except ImportError:  # supports importlib-based tests and direct copied assets
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from project_manifest import artifact_path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
WORKFLOW_LAYERS = ("startup", "state", "ledger", "methodology", "tooling")
SKIP_DIRS = {
    ".git", ".venv", "__pycache__", ".next", ".codex", ".qa", ".guiyuan-vibecoding",
    ".sync_temp_dir", ".tmp", "node_modules", "dist", "build", "target", "vendor",
    ".preview", "coverage", "assets",
}
CODE_EXTENSIONS = {".py", ".js", ".mjs", ".ts", ".tsx", ".css", ".html", ".json", ".toml", ".yml", ".yaml", ".bat", ".sh", ".ps1"}
KNOWN_DIR_HINT = {
    "apps": "可执行应用/服务模块", "src": "产品源代码", "packages": "可复用包", "workers": "后台 worker",
    "tools": "确定性管理/巡检工具", "scripts": "本地钩子/脚本", "docs": "项目文档", "templates": "项目骨架/模板", "tests": "自动化测试",
}
KNOWN_FILE_HINT = {
    "README.md": "项目说明与快速上手", "AGENTS.md": "Agent 启动约定与项目边界", "NOW.md": "当前焦点、阻塞与下一步",
    "CHANGELOG.md": "迭代变更台账", "VERSION": "项目版本号", "pyproject.toml": "Python 项目元数据与依赖", "package.json": "Node 项目元数据与脚本",
}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.is_file() else ""
    except (OSError, UnicodeDecodeError):
        return ""


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line.strip())
        if m:
            return m.group(1).strip()
    return ""


def _first_sentence(text: str) -> str:
    for line in text.splitlines():
        value = line.strip().lstrip("> ")
        if value and not value.startswith("#") and not value.startswith("```"):
            return value[:160]
    return "—"


def _frontmatter(text: str, key: str) -> str:
    if not text.startswith("---"):
        return ""
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        if re.match(rf"^{re.escape(key)}:\s*", line):
            return line.split(":", 1)[1].strip().strip("'\"")
    return ""


def _project_title(root: Path) -> str:
    title = _first_heading(_read(root / "README.md"))
    if title:
        return title
    package = _read(root / "package.json")
    match = re.search(r'"name"\s*:\s*"([^"]+)"', package)
    if match:
        return match.group(1)
    pyproject = _read(root / "pyproject.toml")
    match = re.search(r"^name\s*=\s*[\"']([^\"']+)", pyproject, re.MULTILINE)
    return match.group(1) if match else root.name


def _project_version(root: Path) -> str:
    value = _read(root / "VERSION").strip()
    if value:
        return value.splitlines()[0].strip()
    for filename in ("pyproject.toml", "package.json"):
        text = _read(root / filename)
        match = re.search(r'(?m)^\s*version\s*=\s*["\']([^"\']+)|"version"\s*:\s*"([^"]+)', text)
        if match:
            return next(group for group in match.groups() if group)
    return ""


def _changelog_rows(root: Path, rounds: int) -> list[list[str]]:
    text = _read(artifact_path(root, "changelog", must_exist=True))
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.strip().startswith("|") or re.match(r"^\|\s*-+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and re.fullmatch(r"[rR]\d+", cells[0]):
            rows.append(cells)
            if len(rows) >= rounds:
                break
    return rows


def _roadmap_table(root: Path) -> tuple[Path, list[list[str]]]:
    configured = artifact_path(root, "roadmap", must_exist=True)
    for path in (configured, root / "docs" / "01-product" / "roadmap.md", root / "docs" / "04-workflow" / "roadmap.md", root / "roadmap.md"):
        text = _read(path)
        if not text:
            continue
        rows: list[list[str]] = []
        for line in text.splitlines():
            if not line.strip().startswith("|") or re.match(r"^\|\s*-+\s*\|", line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not rows:
                rows.append(cells)
            elif cells:
                rows.append(cells)
        if len(rows) > 1:
            return path, rows
    return root / "roadmap.md", []


def _managed(root: Path) -> tuple[bool, dict[str, str]]:
    adoption = root / ".guiyuan-vibecoding" / "adoption.json"
    if adoption.is_file():
        try:
            workflows = (json.loads(adoption.read_text(encoding="utf-8")).get("workflows") or {})
        except (OSError, json.JSONDecodeError):
            workflows = {}
        return True, {k: str(workflows.get(k, "keep")) for k in WORKFLOW_LAYERS}
    if (root / "docs" / "04-workflow").is_dir() and (root / "AGENTS.md").is_file():
        return True, {}
    return False, {}


def _detect_agent(root: Path) -> str:
    text = _read(root / "AGENTS.md") + _read(root / "agents" / "openai.yaml")
    lowered = text.lower()
    if "doubao" in lowered or "豆包" in text:
        return "Doubao"
    if "harness" in lowered:
        return "Harness"
    if "codex" in lowered or "openai" in lowered:
        return "Codex"
    return "local"


def _status_class(pct: int) -> tuple[str, str]:
    if pct >= 90:
        return "b-ok", "已完成"
    if pct > 0:
        return "b-run", "进行中"
    return "b-wait", "待开始"


def _module_rows(root: Path, changelog: list[list[str]]) -> list[dict]:
    base = root / "docs" / "01-product"
    if not base.is_dir():
        return []
    modules: list[dict] = []
    for path in sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith("_")):
        prd, acceptance = path / "prd.md", path / "acceptance.md"
        if not prd.is_file() and not acceptance.is_file():
            continue
        acceptance_text = _read(acceptance)
        checks = re.findall(r"-\s*\[([ xX])\]\s*(.+)", acceptance_text)
        done = sum(mark.lower() == "x" for mark, _ in checks)
        pct = round(done * 100 / len(checks)) if checks else 0
        related = [row for row in changelog if path.name.lower() in " ".join(row).lower()]
        latest = related[0] if related else []
        cls, status = _status_class(pct)
        pending = [label.strip() for mark, label in checks if mark.lower() != "x"]
        docs = []
        for label, candidate in (("产品 PRD", prd), ("验收", acceptance)):
            if candidate.is_file():
                docs.append([label, candidate.relative_to(root).as_posix()])
        technical = root / "docs" / "02-technical" / path.name
        docs.extend([["技术文档", p.relative_to(root).as_posix()] for p in sorted(technical.glob("*.md"))] if technical.is_dir() else [])
        title = _first_heading(_read(prd)) or path.name.replace("-", " ").title()
        modules.append({
            "id": path.name, "name": title, "st": cls, "stxt": status, "pct": pct,
            "phase": _frontmatter(_read(prd), "status") or "项目能力", "date": latest[1] if len(latest) > 1 else "",
            "round": latest[0] if latest else "", "change": latest[3] if len(latest) > 3 else _first_sentence(_read(prd)),
            "block": "；".join(pending[:3]) if pending else "无已知阻塞点。", "docs": docs,
        })
    return modules


def _roadmap_rows(root: Path) -> list[dict]:
    source, table = _roadmap_table(root)
    rows: list[dict] = []
    for cells in table[1:13]:
        cells = cells + [""] * max(0, 4 - len(cells))
        raw = " ".join(cells)
        pct_match = re.search(r"(\d{1,3})\s*%", raw)
        status = cells[2] or ""
        pct = int(pct_match.group(1)) if pct_match else (100 if re.search(r"完成|done|complete", status, re.I) else 50 if status else 0)
        cls = "done" if pct >= 90 else "partial" if pct else ""
        rel = source.relative_to(root).as_posix() if source.is_relative_to(root) else source.name
        rows.append({"ph": cells[0] or f"P{len(rows)}", "title": cells[1], "cls": cls, "pct": pct, "when": "", "status": status or "待规划", "acc": cells[3] or "—", "links": [["roadmap.md", rel]] if source.is_file() else []})
    return rows


def _file_description(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    if rel in KNOWN_FILE_HINT or path.name in KNOWN_FILE_HINT:
        return KNOWN_FILE_HINT.get(rel, KNOWN_FILE_HINT[path.name])
    if path.suffix == ".md":
        return _first_heading(_read(path)) or ("迭代归档记录" if path.name.startswith("202") and "-r" in path.name else "Markdown 文档")
    if path.suffix in CODE_EXTENSIONS:
        text = _read(path)
        doc = re.search(r'^[\s]*["\']{3}(.+?)["\']{3}', text, re.S)
        if doc and re.search(r"[\u4e00-\u9fff]", doc.group(1)):
            return " ".join(doc.group(1).split())[:120]
        return "实现代码 / 配置文件"
    return "项目文件"


def _dir_description(path: Path, root: Path) -> str:
    if path.name in KNOWN_DIR_HINT:
        return KNOWN_DIR_HINT[path.name]
    return _first_sentence(_read(path / "README.md")) if (path / "README.md").is_file() else "项目目录"


def _doc_tree(root: Path) -> dict:
    tree: dict = {"__files__": []}
    for path in sorted(root.rglob("*")):
        rel_path = path.relative_to(root)
        if not path.is_file() or path.name == "status.html" or any(part in SKIP_DIRS for part in rel_path.parts):
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS and path.name not in {"VERSION", ".gitignore"}:
            continue
        node = tree
        for depth, part in enumerate(rel_path.parts[:-1]):
            node = node.setdefault(part, {"__files__": [], "__d__": _dir_description(root.joinpath(*rel_path.parts[: depth + 1]), root)})
        node.setdefault("__files__", []).append({"n": path.name, "p": rel_path.as_posix(), "d": _file_description(path, root)})
    tree["__d__"] = "项目根目录：文档、实现与配置的可浏览索引"
    return tree


def _arch_layers(root: Path) -> list[dict]:
    dirs = [p for p in sorted(root.iterdir()) if p.is_dir() and not p.name.startswith(".") and p.name not in SKIP_DIRS]
    if not dirs:
        return []
    mods = []
    for path in dirs[:12]:
        files = [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in CODE_EXTENSIONS]
        # Link only files: browsers cannot reliably open a directory from a
        # ``file://`` page across platforms.
        docs = [["实现", p.relative_to(root).as_posix()] for p in files[:3]]
        mods.append({"id": path.name, "name": path.name, "sub": _dir_description(path, root), "duty": _dir_description(path, root), "steps": [f"浏览 {path.name} 目录", "结合文档与实现确认职责"], "docs": docs})
    return [{"cls": "l-plan", "name": "项目结构 · Project Surface", "mods": mods}]


def _principle_flow() -> list[dict]:
    return [
        {"plain": "先说清楚要做什么", "t": "提出意图", "pts": ["用户输入自然语言目标", "保留未知与待确认项"]},
        {"plain": "把想法和项目事实对上", "t": "读取权威事实", "pts": ["读取 NOW、产品/技术文档与现有代码", "不把页面当成第二事实源"]},
        {"plain": "排出下一步能做的事", "t": "规划任务", "pts": ["按依赖与验收条件选择任务", "明确输入、输出与阻塞"]},
        {"plain": "动手并留下证据", "t": "执行与验证", "pts": ["修改代码或文档", "运行测试、门禁并记录回执"]},
        {"plain": "把结果沉淀下来", "t": "收口与复用", "pts": ["更新 changelog、归档与 NOW", "重新生成本页供下一轮阅读"]},
    ]


def _functional_modules(root: Path) -> list[dict]:
    """Read the human-facing functional directory's embedded JSON data block."""
    candidates = (
        root / "docs" / "00-system" / "functional-module-directory.md",
        root / "docs" / "04-workflow" / "functional-module-directory.md",
    )
    text = next((_read(path) for path in candidates if path.is_file()), "")
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if not match:
        defaults = [
            ("intake", "项目接入与生命周期", "把项目接入归园流程", "tools/bootstrap.py"),
            ("analysis", "需求接收与分析", "把想法整理成可确认的事实与选择", "tools/analysis.py"),
            ("brain", "权威工件与上下文", "只读取必要的项目事实，控制上下文成本", "tools/context_compiler.py"),
            ("planning", "规划与任务编排", "按依赖选出下一件能做的事", "tools/task_graph.py"),
            ("execution", "执行、验证与交付", "做完就测试并留下回执", "tools/receipt_loop.py"),
            ("reflection", "反思与经验回流", "把踩过的坑沉淀成可复用做法", "tools/experience_loop.py"),
        ]
        return [{"id": i, "name": n, "plain": p, "entry": e if (root / e).is_file() else "", "docs": []} for i, n, p, e in defaults]
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    modules = value.get("functionalModules") if isinstance(value, dict) else None
    if not isinstance(modules, list):
        return []
    result = []
    for item in modules:
        if not isinstance(item, dict) or not item.get("id") or not item.get("name"):
            continue
        entry = str(item.get("entry", ""))
        result.append({
            "id": str(item["id"]), "name": str(item["name"]),
            "plain": str(item.get("plain", "")), "entry": entry,
            "docs": [["功能目录", "docs/00-system/functional-module-directory.md"]]
            + ([["主要入口", entry]] if entry else []),
        })
    return result


def build_project(root: Path, agent: str, rounds: int) -> dict:
    managed, layers = _managed(root)
    changelog = _changelog_rows(root, rounds)
    origin, branch = _git(root, "remote", "get-url", "origin"), _git(root, "branch", "--show-current")
    latest_round = changelog[0][0] if changelog else ""
    now = _read(artifact_path(root, "project_state", must_exist=True))
    date_match = re.search(r"20\d{2}-\d{2}-\d{2}", now)
    return {
        "githubVibe": origin if "github.com" in origin else "#", "githubButler": "#", "installed": managed,
        "identity": {"title": _project_title(root), "desc": _first_sentence(_read(root / "README.md")), "address": "./", "addressLabel": "./（本地项目，相对路径）", "version": _project_version(root), "versionNote": "来自项目 VERSION / manifest", "iter": " · ".join(x for x in (date_match.group(0) if date_match else "", latest_round) if x), "internal": f"{root.name} · {branch or '未绑定 Git 分支'}"},
        "archLayers": _arch_layers(root), "modules": _module_rows(root, changelog), "functionalModules": _functional_modules(root), "roadmap": _roadmap_rows(root), "principleFlow": _principle_flow(), "docTree": _doc_tree(root),
        "meta": {"managed": managed, "layers": layers, "generatedAt": datetime.now().isoformat(timespec="minutes")},
    }


def _template_path(root: Path) -> Path:
    for path in (root / "templates" / "guiyuan-vibecoding-home.html", root / "guiyuan-vibecoding-home.html"):
        if path.is_file():
            return path
    raise FileNotFoundError("missing templates/guiyuan-vibecoding-home.html; reinstall Guiyuan assets")


def _inline_assets(document: str, template: Path) -> str:
    for filename, mime in (("taoyuanming-2.png", "image/png"), ("taoyuanming-bw.jpg", "image/jpeg")):
        candidates = (template.parent.parent / "assets" / filename, template.parent / "assets" / filename)
        asset = next((p for p in candidates if p.is_file()), None)
        if not asset:
            continue
        encoded = base64.b64encode(asset.read_bytes()).decode("ascii")
        document = document.replace(f'url("assets/{filename}")', f'url("data:{mime};base64,{encoded}")').replace(f"url('assets/{filename}')", f"url('data:{mime};base64,{encoded}')")
    return document


def _validate_links(root: Path, project: dict) -> None:
    """Fail closed on generated project-file links so the page never ships dead links."""
    candidates: list[str] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "p" and isinstance(item, str):
                    candidates.append(item)
                elif key == "links" and isinstance(item, list):
                    for pair in item:
                        if isinstance(pair, list) and len(pair) > 1 and isinstance(pair[1], str):
                            candidates.append(pair[1])
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(project)
    missing = sorted({p for p in candidates if not p.startswith(("http://", "https://", "#")) and not (root / p).is_file()})
    if missing:
        raise FileNotFoundError("generated project-home links do not exist: " + ", ".join(missing[:8]))


def render(root: Path, out: Path, agent: str, rounds: int) -> Path:
    template = _template_path(root)
    document = template.read_text(encoding="utf-8")
    project = build_project(root, agent, rounds)
    _validate_links(root, project)
    project_json = json.dumps(project, ensure_ascii=False, indent=2)
    document, count = re.subn(r"var PROJECT = .*?;\n\n\(function\(\)\{", "var PROJECT = " + project_json + ";\n\n(function(){", document, count=1, flags=re.S)
    if count != 1:
        raise ValueError("template must contain exactly one `var PROJECT = ...` data block")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_inline_assets(document, template), encoding="utf-8")
    return out


def snapshot(root: Path, agent: str, rounds: int = 10) -> dict:
    return build_project(root, agent, rounds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a static project status.html (no server required)")
    parser.add_argument("--out", default=str(ROOT / "status.html"))
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--agent", default=None)
    args = parser.parse_args()
    output = render(ROOT, Path(args.out), args.agent or _detect_agent(ROOT), max(1, args.rounds))
    try:
        shown = output.relative_to(ROOT)
    except ValueError:
        shown = output
    print(f"static project home written: {shown}")


if __name__ == "__main__":
    main()
