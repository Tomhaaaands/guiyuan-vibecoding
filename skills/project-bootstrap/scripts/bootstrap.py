#!/usr/bin/env python3
"""一键部署迭代管理系统骨架到新项目。

用法：
  python bootstrap.py [target] --name "项目名" [--force] [--no-install-skill] \
      --module "名称=关键词1,关键词2" --code "名称=代码目录" \
      [--template default] \
      [--python auto|system|install|<路径>] [--env auto|shared|isolated|reuse|skip]

默认模块目录（--template default 或 --module 直接给目录名）：
  web=apps/web · api=apps/api · db=data/db · worker=workers · tests=tests
  模块名命中目录时自动使用目录内置的关键词与代码目录，可被 --code 覆盖。

Python 运行时（--python，默认 auto）：
  auto：检测用户已有 Python（py 启动器 → PATH python → uv python find），直接复用；
        全无才回退当前解释器
  system：同上但不回退，未检测到即报错
  install：自动部署（优先 uv python install 3.12，否则 winget 非交互安装 Python 3.12）
  直接传路径：使用指定解释器

依赖方式（--env，默认 auto）：
  auto：已有 .venv 直接复用；否则用 uv venv（共享依赖缓存）；uv 不可用则项目内 python -m venv
  shared：项目 .venv 带 --system-site-packages，直接共用基础 Python 已装的包
  isolated：项目内干净 .venv（--no-venv 等价 skip；旧值 create/uv 映射到 isolated/auto）
  reuse：仅复用已有 .venv，缺失不创建
  skip：跳过

交互式模块清单：
  在对话中先向用户逐个确认业务模块（名称/关键词/代码目录），再以 --module / --code
  传入脚本，自动填充 AGENTS.md 与 AGENTS_WORKFLOW.md 的路由表行；
  未传 --module 时保留 {{模块A}} 等占位符供用户手填。

附加能力：
  - 为每个模块创建占位目录（docs/01-product|02-technical/{name}/ 与代码目录，.gitkeep）；
  - 运行环境处理：先解析 Python（默认复用用户已有），再按依赖策略处理 .venv；
  - 自动 git init（已存在 .git 则跳过），提示提交命令。
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
    "web": {"kw": "前端,页面", "code": "apps/web"},
    "api": {"kw": "后端,接口", "code": "apps/api"},
    "db": {"kw": "数据库,表", "code": "data/db"},
    "worker": {"kw": "异步,队列", "code": "workers"},
    "tests": {"kw": "测试", "code": "tests"},
    "docs": {"kw": "文档", "code": "docs"},
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
        f"# R1 · 初始化（{date.isoformat()}）\n\n"
        "## 背景\n\n新项目一键部署：迭代管理系统骨架（启动契约 / 台账 / 档案 / 状态卡 / 工具链）就位。\n\n"
        "## 验证\n\n- `tools/check_drift.py` 通过；`llms.txt` 已生成。\n\n"
        "## 后续\n\n- 填写 AGENTS.md 模块路由表与技术约束；按五步闭环推进后续轮次。\n",
        encoding="utf-8",
    )
    return out


def _fill_routing_tables(root: Path, modules: list[dict]) -> None:
    """用模块清单替换 AGENTS.md / AGENTS_WORKFLOW.md 的路由表占位行。"""
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
            if line.startswith("| {{模块"):
                if not replaced:
                    out.extend(rows)
                    replaced = True
                continue
            if drop_note and "按项目裁剪" in line:
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
    return out if ok else "版本未知"


def _find_python(mode: str) -> tuple[str | None, str]:
    """解析用户 Python：py 启动器 → PATH python → uv python find → 兜底当前解释器。"""
    ok, _ = _run_quiet(["py", "-3", "--version"])
    if ok:
        ok2, exe = _run_quiet(["py", "-3", "-c", "import sys; print(sys.executable)"])
        if ok2 and exe:
            return exe, "py 启动器（用户已装）"
    p = shutil.which("python")
    if p:
        return p, "PATH 上的 python"
    ok, exe = _run_quiet(["uv", "python", "find"])
    if ok and exe:
        return exe, "uv 托管 Python"
    if mode == "system":
        return None, "未检测到用户 Python"
    return sys.executable, "当前解释器（未检测到独立用户 Python，兜底）"


def _install_python() -> tuple[str | None, str]:
    """自动部署 Python：优先 uv python install，其次 winget 非交互安装。"""
    ok, _ = _run_quiet(["uv", "--version"])
    if ok:
        r = subprocess.run(["uv", "python", "install", "3.12"], capture_output=True, text=True)
        if r.returncode == 0:
            ok2, exe = _run_quiet(["uv", "python", "find"])
            if ok2 and exe:
                return exe, "uv 已安装 Python 3.12"
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
                return exe, f"{source}（winget 已安装 Python 3.12）"
    return None, "自动安装失败：无 uv 且无 winget（可手动安装后重跑）"


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
    ap = argparse.ArgumentParser(description="一键部署迭代管理系统骨架")
    ap.add_argument("target", nargs="?", default=".", help="目标目录（默认当前目录）")
    ap.add_argument("--name", default=None, help="项目名（默认取目标目录名）")
    ap.add_argument("--force", action="store_true", help="覆盖已存在文件")
    ap.add_argument("--no-install-skill", action="store_true", help="跳过 iteration-close-loop 安装")
    ap.add_argument("--module", action="append", default=[], metavar="名称=关键词1,关键词2",
                    help="业务模块（可重复；关键词逗号分隔，省略时用模块名）")
    ap.add_argument("--code", action="append", default=[], metavar="名称=代码目录",
                    help="模块代码目录（可重复，如 suanming=apps/web）")
    ap.add_argument("--template", choices=["default"], default=None,
                    help="默认模板：web + api + db + worker + tests")
    ap.add_argument("--python", default="auto", metavar="auto|system|install|<路径>",
                    help="Python 运行时：auto=检测用户已有（默认）；system=仅用已检测不回退；"
                         "install=自动部署（uv/winget）；或直接给解释器路径")
    ap.add_argument("--env", choices=["auto", "shared", "isolated", "reuse", "skip", "create", "uv"],
                    default="auto",
                    help="依赖方式：auto=已有 .venv 复用/uv venv/项目内创建（默认）；"
                         "shared=共用基础 Python 已装包（--system-site-packages）；"
                         "isolated=项目内干净 .venv；reuse=仅复用已有；skip=跳过"
                         "（旧值 create/uv 兼容映射）")
    ap.add_argument("--no-venv", action="store_true", help="等价 --env skip")
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
        python_exe, py_source = args.python, "用户指定路径"
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

    print(f"部署完成：{target}")
    print(f"  复制 {copied} 个文件，跳过已存在 {skipped} 个")
    if created_dirs:
        print(f"  创建模块占位目录：{'、'.join(created_dirs)}")
    print(f"  初始化档案：{arch.relative_to(target).as_posix()}")
    status_text = {
        "reused": "已存在，复用（--env auto/reuse）",
        "created": "已创建（本机 Python）",
        "created-uv": "已创建（uv venv）",
        "created-shared": "已创建（共用系统依赖 --system-site-packages）",
        "missing": "未找到已有环境且策略为仅复用（reuse），未创建",
        "skipped": "跳过（--env skip）",
        "failed": "创建失败（可手动 python -m venv .venv）",
        "no-python": "未找到 Python，未创建环境",
    }
    print(f"  Python：{py_version}（{py_source}）")
    if python_exe:
        print(f"    路径：{python_exe}")
    print(f"  .venv：{status_text[venv_status]}")
    if venv_status == "no-python":
        print("  提示：可加 --python install 自动部署（uv python install / winget Python 3.12）")
    if git_inited:
        print("  git：已 git init")
    elif (target / ".git").exists():
        print("  git：已是 git 仓库")
    else:
        print("  git：不可用或已跳过")
    print("  提交命令：git add -A && git commit -m \"chore: init\"")
    if installed:
        print(f"  已安装 skill：{installed}")
    else:
        print("  iteration-close-loop 已存在，未重复安装")
    if remaining:
        print("  待填占位符：" + "、".join(remaining))
    else:
        print("  占位符全部替换完毕")
    print("  下一步：填写 AGENTS.md 模块路由表与技术约束；运行 tools/check_drift.py 验证")


if __name__ == "__main__":
    main()
