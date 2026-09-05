#!/usr/bin/env python3
"""Unified QA gate for the Guiyuan Vibecoding internal repo (stdlib only).

Single entrypoint for the internal test suite plus the delivery gates, so a round can be
closed with one command instead of remembering each tool. Exits non-zero if any blocking gate
fails.

Usage:
  python tools/run_qa.py                       # unittest + behavior harness + delivery gates
  python tools/run_qa.py --coverage            # add approximate stdlib trace coverage
  python tools/run_qa.py --frontend            # add frontend typecheck/build smoke if node present
  python tools/run_qa.py --skip delivery:build  # exclude one gate

Reports are written to .qa/qa-report.json. Frontend smoke and coverage are non-blocking (they
are reported but never fail the run); the backend/behavior/delivery gates are blocking.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = next(p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file())
QA_DIR = ROOT / ".qa"
PY = sys.executable


def _run(name: str, args: list[str], cwd: Path | None = None, timeout: int = 180) -> dict:
    proc = subprocess.run(args, cwd=cwd or ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    out = (proc.stdout + proc.stderr).strip()
    return {
        "name": name,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "detail": out[-2000:] if out else "",
    }


def _unittest_gate() -> dict:
    proc = subprocess.run(
        [PY, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"],
        cwd=ROOT, capture_output=True, text=True, timeout=240,
        encoding="utf-8", errors="replace",
    )
    out = (proc.stdout + proc.stderr)
    # Summarize the final result line, e.g. "Ran 32 tests in 0.5s\n\nOK".
    tail = "\n".join(l for l in out.splitlines() if l.strip())[-1200:]
    return {
        "name": "unittest",
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "detail": tail,
        "summary": _parse_unittest_summary(out),
    }


def _parse_unittest_summary(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    ran = next((l for l in lines if l.startswith("Ran ")), "")
    ok_line = next((l for l in reversed(lines) if l in ("OK", "FAILED")), "")
    return {"ran": ran, "result": ok_line}


def _coverage_gate() -> dict:
    qa_dir = QA_DIR / "coverage"
    qa_dir.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            [PY, "-m", "trace", "--count", "--summary", "--coverdir", str(qa_dir),
             "--module", "tests.run_tests"],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return {"name": "coverage", "ok": False, "returncode": 124, "detail": "timed out"}
    out = (proc.stdout + proc.stderr).strip()
    return {
        "name": "coverage",
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "detail": out[-1800:] if out else "",
    }


def _frontend_gate() -> dict:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if not node or not npm:
        return {"name": "frontend", "ok": True, "returncode": 0, "detail": "skipped: node/npm not detected"}
    results: list[dict] = []
    for name in ("web", "admin"):
        frontend_dir = ROOT / "skills" / "guiyuan-vibecoding" / "assets" / "frontend" / name
        if not frontend_dir.is_dir():
            results.append({"name": f"frontend:{name}", "ok": True, "detail": "skipped: dir missing"})
            continue
        # Typecheck requires the installed TS toolchain; build needs node_modules. If the
        # scaffolded template has neither, report a non-blocking skip rather than a false fail.
        tsc = frontend_dir / "node_modules" / ".bin" / ("tsc.cmd" if sys.platform == "win32" else "tsc")
        if not tsc.is_file() and not (frontend_dir / "node_modules").is_dir():
            results.append({
                "name": f"frontend:{name}",
                "ok": True,
                "returncode": 0,
                "detail": "skipped: node_modules not installed (npm install then rerun --frontend)",
            })
            continue
        proc = subprocess.run([npm, "run", "build"], cwd=frontend_dir, capture_output=True, text=True,
                              timeout=300, encoding="utf-8", errors="replace")
        results.append({
            "name": f"frontend:{name}",
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "detail": (proc.stdout + proc.stderr).strip()[-800:],
        })
    return {"name": "frontend", "ok": all(r["ok"] for r in results), "returncode": max(r.get("returncode", 0) for r in results), "detail": json.dumps(results)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the internal QA gate suite")
    ap.add_argument("--coverage", action="store_true", help="add approximate stdlib-trace coverage")
    ap.add_argument("--frontend", action="store_true", help="add optional frontend build/typecheck smoke")
    ap.add_argument("--skip", action="append", default=[], metavar="GATE", help="exclude a gate by name")
    args = ap.parse_args()

    QA_DIR.mkdir(parents=True, exist_ok=True)
    skip = set(args.skip)
    results: list[dict] = []

    if "unittest" not in skip:
        results.append(_unittest_gate())
    if "behavior" not in skip:
        results.append(_run("behavior", [PY, str(ROOT / "tools" / "behavior_harness.py")]))
    if "delivery:drift" not in skip:
        results.append(_run("delivery:drift", [PY, str(ROOT / "tools" / "check_drift.py")]))
    if "delivery:build" not in skip:
        results.append(_run("delivery:build", [PY, str(ROOT / "tools" / "build_dist.py"), "--verify", "--out", str(QA_DIR / "dist")]))
    if "delivery:architecture" not in skip:
        results.append(_run("delivery:architecture", [PY, str(ROOT / "tools" / "architecture_audit.py"), ".", "--json"]))
    if "delivery:package" not in skip:
        results.append(_run("delivery:package", [PY, str(ROOT / "tools" / "check_package.py")]))
    if "delivery:security" not in skip:
        results.append(_run("delivery:security", [PY, str(ROOT / "tools" / "git_safety_gate.py")]))
    if args.coverage:
        results.append(_coverage_gate())
    if args.frontend:
        results.append(_frontend_gate())

    blocking = [r for r in results if r["name"] in ("unittest", "behavior", "delivery:drift",
                                                    "delivery:build", "delivery:architecture", "delivery:package",
                                                    "delivery:security")]
    failed = [r for r in blocking if not r["ok"]]

    report = {
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "blocking_passed": not failed,
        "results": results,
    }
    report_path = QA_DIR / "qa-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("== QA gate report ==")
    for r in results:
        status = "PASS" if r["ok"] else "FAIL"
        print(f"  [{status}] {r['name']} (rc={r.get('returncode', '')})")
        if not r["ok"]:
            print(r["detail"])
    print(f"\nreport: {report_path.relative_to(ROOT)}")

    if failed:
        names = ", ".join(f["name"] for f in failed)
        print(f"\n{len(failed)} blocking gate(s) failed: {names}")
        return 1
    print("\nQA gates passed ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
