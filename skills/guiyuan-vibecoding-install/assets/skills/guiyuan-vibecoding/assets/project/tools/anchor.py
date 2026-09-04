#!/usr/bin/env python3
"""Record an immutable user-confirmation anchor for a management phase."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json
from pathlib import Path

PHASES = {"REQ": "ANALYSIS", "PLAN": "PLANNING", "QA": "VERIFICATION", "RELEASE": "DELIVERY"}

def _hash(path: Path) -> str | None:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def record(root: Path, anchor_id: str, phase: str, decision: str, inputs: list[str], outputs: list[str], next_state: str,
           confirmed_by: str = "user") -> Path:
    phase = phase.upper()
    if phase not in PHASES: raise ValueError(f"phase must be one of {sorted(PHASES)}")
    if not anchor_id.upper().endswith("-" + phase): raise ValueError(f"anchor id must end with -{phase}")
    if decision not in {"accepted", "rejected", "blocked"}: raise ValueError("invalid decision")
    directory = root / ".guiyuan-vibecoding" / "anchors"; directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{anchor_id}.json"
    input_hashes = {x: value for x in inputs if (value := _hash(root / x))}
    output_hashes = {x: value for x in outputs if (value := _hash(root / x))}
    payload = {"anchor_id": anchor_id, "phase": phase, "manager_state": PHASES[phase], "decision": decision,
               "input_refs": inputs, "output_refs": outputs, "input_hashes": input_hashes,
               "output_hashes": output_hashes, "next_state": next_state,
               "confirmed_by": confirmed_by or "user",
               "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()}
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded: raise FileExistsError(f"anchor already exists with different content: {anchor_id}")
    path.write_text(encoded, encoding="utf-8")
    return path

def main():
    p=argparse.ArgumentParser(); p.add_argument("anchor_id"); p.add_argument("--root",type=Path,default=Path(".")); p.add_argument("--phase",required=True,choices=sorted(PHASES)); p.add_argument("--decision",required=True,choices=["accepted","rejected","blocked"]); p.add_argument("--input",action="append",default=[]); p.add_argument("--output",action="append",default=[]); p.add_argument("--next-state",required=True); p.add_argument("--confirmed-by",default="user"); a=p.parse_args(); print(record(a.root.resolve(),a.anchor_id,a.phase,a.decision,a.input,a.output,a.next_state,a.confirmed_by))

if __name__ == "__main__": main()
