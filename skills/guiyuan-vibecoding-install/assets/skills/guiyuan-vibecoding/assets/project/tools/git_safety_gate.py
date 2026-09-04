#!/usr/bin/env python3
"""Fail-closed staged-content safety gate for Git commits.

Only the staged snapshot is inspected.  Findings never print secret values.  This is a local
fast gate; hosted repositories should run the same checks in CI with branch protection enabled.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import re
import subprocess
import sys
from pathlib import Path

SECRET_PATTERNS = (
    ("SEC001", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "private-key header"),
    ("SEC002", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"), "GitHub token"),
    ("SEC003", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    ("SEC004", re.compile(r"\b(?:sk|sk-proj)-[A-Za-z0-9_-]{20,}\b"), "provider token"),
    ("SEC005", re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}\b", re.I), "bearer token"),
    ("SEC006", re.compile(r"\b(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9/+=_-]{16,}", re.I), "credential assignment"),
)
SENSITIVE_NAME = re.compile(r"(^|/)(?:\.env(?:\..*)?|credentials?|secrets?)(?:$|/)|\.(?:pem|key|p12|pfx)$|\.sqlite(?:3)?$|\.db$", re.I)
CACHE_NAME = re.compile(r"(^|/)(?:__pycache__|\.venv|venv|node_modules|\.next|dist|build|out|\.pytest_cache|\.mypy_cache|\.ruff_cache)(?:/|$)|(?:\.pyc|\.pyo)$", re.I)
ALLOWED_BINARY = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf"}
MAX_FILE_BYTES = 10 * 1024 * 1024


def _root() -> Path:
    try:
        raw = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
        return Path(raw)
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd()


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=root)


def staged_paths(root: Path) -> list[str]:
    raw = _git(root, "diff", "--cached", "--name-only", "-z")
    return [x.decode("utf-8", "replace") for x in raw.split(b"\0") if x]


def _blob(root: Path, rel: str) -> bytes | None:
    try:
        return _git(root, "show", f":{rel}")
    except subprocess.CalledProcessError:
        return None


def _mode(root: Path, rel: str) -> str:
    try:
        line = _git(root, "ls-files", "-s", "--", rel).decode("utf-8", "replace").splitlines()[0]
        return line.split()[0]
    except (IndexError, subprocess.CalledProcessError):
        return ""


def _placeholder(line: str) -> bool:
    lowered = line.casefold()
    return any(x in lowered for x in ("example", "placeholder", "your_", "replace_me", "changeme", "<token>"))


def _entropy(value: str) -> float:
    counts = {c: value.count(c) for c in set(value)}
    n = len(value)
    return -sum((count / n) * math.log2(count / n) for count in counts.values()) if n else 0.0


def scan(root: Path, paths: list[str] | None = None, allow_paths: set[str] | None = None) -> list[dict]:
    findings: list[dict] = []
    allow_paths = allow_paths or set()
    for rel in paths if paths is not None else staged_paths(root):
        rel = rel.replace("\\", "/")
        if rel in allow_paths:
            continue
        data = _blob(root, rel)
        if data is None:
            continue  # deleted from index
        if SENSITIVE_NAME.search(rel):
            findings.append({"rule": "FILE001", "path": rel, "message": "sensitive filename is not commit-safe"})
        if CACHE_NAME.search(rel):
            findings.append({"rule": "FILE002", "path": rel, "message": "cache/build artifact must not be committed"})
        if len(data) > MAX_FILE_BYTES:
            findings.append({"rule": "FILE003", "path": rel, "message": f"file exceeds {MAX_FILE_BYTES // (1024 * 1024)} MiB"})
        mode = _mode(root, rel)
        if mode == "120000":
            target = data.decode("utf-8", "replace")
            if target.startswith("/") or ".." in Path(target).parts:
                findings.append({"rule": "FILE004", "path": rel, "message": "symlink leaves project boundary"})
        is_binary = b"\0" in data[:8192]
        suffix = Path(rel).suffix.casefold()
        if is_binary and suffix not in ALLOWED_BINARY:
            findings.append({"rule": "FILE005", "path": rel, "message": "binary file is not on the allowlist"})
        if suffix in {".zip", ".tar", ".gz", ".tgz", ".7z", ".rar"}:
            findings.append({"rule": "FILE006", "path": rel, "message": "archive files are blocked in commits"})
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = ""
        for line_no, line in enumerate(text.splitlines(), 1):
            for rule, pattern, label in SECRET_PATTERNS:
                if pattern.search(line) and not _placeholder(line):
                    findings.append({"rule": rule, "path": rel, "line": line_no, "message": label})
            # JWT-like values are checked separately and only reported by shape.
            for value in re.findall(r"\b[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b", line):
                try:
                    base64.urlsafe_b64decode(value.split('.')[0] + "===")
                except Exception:
                    continue
                if not _placeholder(line) and _entropy(value) >= 3.2:
                    findings.append({"rule": "SEC007", "path": rel, "line": line_no, "message": "JWT-like credential"})
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fail-closed staged-content Git safety gate")
    ap.add_argument("--json", action="store_true", help="emit machine-readable findings")
    ap.add_argument("--allow-path", action="append", default=[], help="explicitly allow one staged path (repeatable)")
    args = ap.parse_args(argv)
    root = _root()
    try:
        paths = staged_paths(root)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"[gate] cannot read staged snapshot: {exc}")
        return 1
    findings = scan(root, paths, set(args.allow_path))
    if args.json:
        print(json.dumps({"ok": not findings, "paths": paths, "findings": findings}, ensure_ascii=False, indent=2))
    else:
        print(f"== staged safety gate ({len(paths)} path(s)) ==")
        for item in findings:
            location = f"{item['path']}:{item['line']}" if item.get("line") else item["path"]
            print(f"  [BLOCK] {item['rule']} {location} — {item['message']}")
        print("staged safety gate " + ("passed ✓" if not findings else f"blocked: {len(findings)} finding(s)"))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())


