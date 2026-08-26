#!/usr/bin/env python3
"""One-click scaffold of the iteration-management skeleton into a new project.

Usage:
  python bootstrap.py [target] --name "project" [--force] [--no-install-skill] \
      --module "name=kw1,kw2" --code "name=dir" \
      [--template default] \
      [--python auto|system|install|<path>] [--env auto|shared|isolated|reuse|skip]

Default module catalog (used by --template default or bare --module names):
  web=apps/web · api=apps/api · db=data/db · worker=workers · tests=tests
  A module name matching the catalog gets keywords and a code dir automatically;
  override the code dir with --code.

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

Interactive module list:
  Confirm modules with the user in conversation (name/keywords/code dir), then pass them via
  --module / --code; the script fills the routing tables in AGENTS.md and AGENTS_WORKFLOW.md.
  Without --module, the {{module}} placeholders are kept for manual filling.

Extras:
  - creates placeholder dirs per module (docs/01-product|02-technical/{name}/ + code dir, .gitkeep);
  - resolves the Python runtime first, then handles .venv per policy;
  - runs `git init` (skipped if .git exists) and prints the commit command.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS = SKILL_ROOT / "assets" / "project"
SKILL_ASSETS = SKILL_ROOT / "assets" / "skills" / "iteration-close-loop"
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")
DEFAULT_MODULES = {
    "web": {"kw": "frontend,web", "code": "apps/web"},
    "api": {"kw": "backend,api", "code": "apps/api"},
    "db": {"kw": "database,schema", "code": "data/db"},
    "worker": {"kw": "async,queue", "code": "workers"},
    "tests": {"kw": "tests", "code": "tests"},
    "docs": {"kw": "docs", "code": "docs"},
}


def _replace_placeholders(root: Path, name: str) -> list[str]:
    today = dt.date.today()
    mapping = {
        "{{PROJECT_NAME}}": name,
        "{{YYYY-MM-DD}}": today.isoformat(),
        "{{MM-DD}}": today.strftime("%m-%d"),
    }
    remaining: set[str] = set()
    for p in root.rglob("*.md"):
        text = p.read_text(encoding="utf-8")
        for k, v in mapping.items():
            text = text.replace(k, v)
        p.write_text(text, encoding="utf-8")
        remaining.update(PLACEHOLDER_RE.findall(text))
    return sorted(remaining)


def _write_r1_archive(root: Path) -> Path:
    date = dt.date.today()
    arch_dir = root / "docs" / "04-workflow" / "archive"
    arch_dir.mkdir(parents=True, exist_ok=True)
    out = arch_dir / f"{date.isoformat()}-r1.md"
    if out.exists():
        return out
    out.write_text(
        f"# R1 · init ({date.isoformat()})\n\n"
        "## Background\n\nOne-click deployment of the iteration-management skeleton "
        "(startup contract / ledger / archive / state cards / tooling).\n\n"
        "## Verification\n\n- `tools/check_drift.py` passes; `llms.txt` generated.\n\n"
        "## Next\n\n- Fill in AGENTS.md technical constraints; continue rounds with the five-step loop.\n",
        encoding="utf-8",
    )
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


def main() -> None:
    ap = argparse.ArgumentParser(description="One-click scaffold of the iteration system")
    ap.add_argument("target", nargs="?", default=".", help="target directory (default: current)")
    ap.add_argument("--name", default=None, help="project name (default: target dir name)")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    ap.add_argument("--no-install-skill", action="store_true", help="skip iteration-close-loop install")
    ap.add_argument("--module", action="append", default=[], metavar="name=kw1,kw2",
                    help="business modules (repeatable; keywords comma-separated; catalog defaults)")
    ap.add_argument("--code", action="append", default=[], metavar="name=dir",
                    help="module code dir (repeatable, e.g. myapp=apps/web)")
    ap.add_argument("--template", choices=["default"], default=None,
                    help="default template: web + api + db + worker + tests")
    ap.add_argument("--python", default="auto", metavar="auto|system|install|<path>",
                    help="Python runtime: auto=detect user's existing (default); system=no fallback; "
                         "install=auto-deploy (uv/winget); or an explicit interpreter path")
    ap.add_argument("--env", choices=["auto", "shared", "isolated", "reuse", "skip", "create", "uv"],
                    default="auto",
                    help="dependency policy: auto=reuse existing/uv venv/project-local (default); "
                         "shared=--system-site-packages; isolated=clean local .venv; reuse=existing only; "
                         "skip=none (legacy create/uv mapped)")
    ap.add_argument("--no-venv", action="store_true", help="alias for --env skip")
    args = ap.parse_args()

    target = Path(args.target).resolve()
    name = args.name or target.name
    target.mkdir(parents=True, exist_ok=True)

    copied, skipped = 0, 0
    for src in sorted(ASSETS.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(ASSETS)
        dst = target / rel
        if dst.exists() and not args.force:
            skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

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

    _fill_routing_tables(target, modules)
    remaining = _replace_placeholders(target, name)
    arch = _write_r1_archive(target)
    created_dirs = _ensure_module_dirs(target, modules)

    gen = target / "tools" / "gen_llms_txt.py"
    if gen.exists():
        subprocess.run([sys.executable, str(gen)], cwd=target, check=True)

    env_mode = "skip" if args.no_venv else {"create": "isolated", "uv": "auto"}.get(args.env, args.env)
    if args.python in ("auto", "system"):
        python_exe, py_source = _find_python(args.python)
    elif args.python == "install":
        python_exe, py_source = _install_python()
    else:
        python_exe, py_source = args.python, "user-specified path"
    py_version = _py_version(python_exe) if python_exe else "-"

    venv_status = "no-python" if python_exe is None else "skipped"
    if python_exe is not None and env_mode != "skip":
        try:
            venv_status = _handle_venv(target, env_mode, python_exe)
        except (subprocess.CalledProcessError, OSError):
            venv_status = "failed"
    git_inited = _git_init(target)

    installed = None
    if not args.no_install_skill:
        installed = _install_skill(args.force)

    print(f"Deployment complete: {target}")
    print(f"  copied {copied} files, skipped {skipped} existing")
    if created_dirs:
        print(f"  module placeholder dirs: {'、'.join(created_dirs)}")
    print(f"  init archive: {arch.relative_to(target).as_posix()}")
    status_text = {
        "reused": "existing, reused (--env auto/reuse)",
        "created": "created (local Python)",
        "created-uv": "created (uv venv)",
        "created-shared": "created (shared system packages, --system-site-packages)",
        "missing": "no existing env and policy is reuse-only; not created",
        "skipped": "skipped (--env skip)",
        "failed": "creation failed (run manually: python -m venv .venv)",
        "no-python": "no Python found; env not created",
    }
    print(f"  Python: {py_version} ({py_source})")
    if python_exe:
        print(f"    path: {python_exe}")
    print(f"  .venv: {status_text[venv_status]}")
    if venv_status == "no-python":
        print("  hint: rerun with --python install to auto-deploy (uv python install / winget Python 3.12)")
    if git_inited:
        print("  git: initialized")
    elif (target / ".git").exists():
        print("  git: already a repository")
    else:
        print("  git: unavailable or skipped")
    print("  commit: git add -A && git commit -m \"chore: init\"")
    if installed:
        print(f"  installed skill: {installed}")
    else:
        print("  iteration-close-loop already present, not reinstalled")
    if remaining:
        print("  remaining placeholders: " + "、".join(remaining))
    else:
        print("  all placeholders replaced")
    print("  next: fill AGENTS.md technical constraints; run tools/check_drift.py to verify")


if __name__ == "__main__":
    main()
