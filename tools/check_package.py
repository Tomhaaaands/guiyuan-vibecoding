#!/usr/bin/env python3
"""Block a public release when tracked source or reachable Git history contains token-like secrets.

Usage: python tools/check_package.py

This is a conservative public-release gate, not a replacement for provider secret scanning.
It scans only tracked files and Git objects reachable from local refs, so ignored local `.env`
files are neither read nor accidentally reported as release content.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
sys.stdout.reconfigure(encoding="utf-8")
PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def run(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip() or "git command failed")
    return r.stdout


def scan_text(label: str, text: str) -> int:
    hits = 0
    for number, line in enumerate(text.splitlines(), 1):
        if any(pattern.search(line) for pattern in PATTERNS):
            print(f"[secret] {label}:{number}")
            hits += 1
    return hits


def main() -> None:
    try:
        tracked = [line for line in run("ls-files").splitlines() if line]
    except RuntimeError as exc:
        print(f"[error] {exc}")
        sys.exit(1)
    hits = 0
    for rel in tracked:
        path = ROOT / rel
        try:
            data = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        hits += scan_text(rel, data)
    try:
        refs = run("rev-list", "--all").splitlines()
        for commit in refs:
            result = subprocess.run(
                ["git", "grep", "-n", "-I", "-E", r"gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}", commit, "--"],
                cwd=ROOT, capture_output=True, text=True,
            )
            if result.returncode not in (0, 1):
                raise RuntimeError(result.stderr.strip() or "git grep failed")
            for line in result.stdout.splitlines():
                print(f"[history-secret] {line.split(':', 2)[0]}:{line.split(':', 2)[1]}")
                hits += 1
    except RuntimeError as exc:
        print(f"[error] {exc}")
        sys.exit(1)
    print("package check " + ("passed ✓" if hits == 0 else f"failed: {hits} possible secret(s)"))
    sys.exit(0 if hits == 0 else 1)


if __name__ == "__main__":
    main()
