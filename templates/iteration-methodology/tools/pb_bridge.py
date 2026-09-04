#!/usr/bin/env python3
"""VCM-side bridge to 归园大管家 / Guiyuan Butler (Private Butler).

Follows `private_butler/docs/api-contract.md` (v1):

- MCP endpoint: `POST <pb_endpoint>/mcp`, JSON-RPC `tools/call`.
- Auth: `Authorization: Bearer <pb_token>`.
- Health: `GET <pb_endpoint>/healthz` (no token).
- Tools: `guiyuan_butler_chat_context`, `guiyuan_butler_capture`. No `memory_*` aliases.
- ``similarity(query, texts[])`` is NOT implemented by PB; use keyword fallback.

Reads `.guiyuan-vibecoding/config.json` (``pb_enabled``, ``pb_endpoint``, ``pb_token``). Every call
degrades gracefully to ``None`` when PB is disabled, unreachable, or returns an error.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_ENDPOINT = "http://192.168.2.123:8001"
TOOL_MEMORY_CONTEXT = "guiyuan_butler_chat_context"
TOOL_MEMORY_RESULT = "guiyuan_butler_capture"
SIMILARITY_UNIMPLEMENTED = "similarity(query, texts[]) is not implemented by PB (api v1); use keyword fallback"


def _root() -> Path:
    return next(
        (p for p in (Path(__file__).resolve(), *Path(__file__).resolve().parents) if (p / "README.md").is_file()),
        Path.cwd(),
    )


def _base(endpoint: str) -> str:
    return str(endpoint or DEFAULT_ENDPOINT).rstrip("/")


def config(root: Path | None = None) -> dict[str, object]:
    root = root or _root()
    cfg: dict[str, object] = {
        "pb_enabled": False,
        "pb_endpoint": DEFAULT_ENDPOINT,
        "pb_token": os.environ.get("VCM_PB_TOKEN", ""),
    }
    try:
        data = json.loads((root / ".guiyuan-vibecoding" / "config.json").read_text(encoding="utf-8"))
        cfg["pb_enabled"] = bool(data.get("pb_enabled", False))
        cfg["pb_endpoint"] = str(data.get("pb_endpoint") or DEFAULT_ENDPOINT)
        cfg["pb_token"] = str(data.get("pb_token") or cfg["pb_token"])
    except (OSError, json.JSONDecodeError):
        pass
    return cfg


def health(root: Path | None = None, timeout: int = 2) -> bool:
    cfg = config(root)
    if not cfg["pb_enabled"]:
        return False
    url = _base(str(cfg["pb_endpoint"])) + "/healthz"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def _rpc(endpoint: str, method: str, params: dict[str, object], timeout: int,
         token: str) -> dict | None:
    url = _base(endpoint) + "/mcp"
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": "vcm-" + os.urandom(4).hex(), "method": "tools/call",
         "params": {"name": method, "arguments": params}},
        ensure_ascii=False,
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    result = body.get("result")
    if not isinstance(result, dict) or result.get("isError"):
        return None
    text = ""
    for item in result.get("content", []):
        if item.get("type") == "text":
            text = item.get("text", "")
            break
    if not text:
        return result
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"text": text}


def pb_memory_context(query: str, root: Path | None = None, timeout: int = 4,
                      max_tokens: int = 800) -> dict | None:
    cfg = config(root)
    if not cfg["pb_enabled"]:
        return None
    return _rpc(
        str(cfg["pb_endpoint"]), TOOL_MEMORY_CONTEXT,
        {"query": query, "max_tokens": max_tokens}, timeout, str(cfg["pb_token"] or ""),
    )


def pb_memory_result(result: dict[str, object], root: Path | None = None,
                     source_instance: str = "vcm-local", timeout: int = 6) -> dict | None:
    cfg = config(root)
    if not cfg["pb_enabled"]:
        return None
    event_id = str(result.get("client_request_id") or result.get("source_event_id") or f"run-{int(time.time())}")
    args = {
        "api_version": "v1",
        "content": str(result.get("content", "")),
        "source": "vcm",
        "source_instance": source_instance,
        "source_event_id": event_id,
        "client_request_id": str(result.get("client_request_id") or event_id),
    }
    return _rpc(
        str(cfg["pb_endpoint"]), TOOL_MEMORY_RESULT, args, timeout, str(cfg["pb_token"] or ""),
    )


def pb_similarity(query: str, texts: list[str], root: Path | None = None, timeout: int = 4) -> dict | None:
    # PB has not shipped a versioned similarity tool; do not call or fake it.
    return {"unavailable": True, "reason": SIMILARITY_UNIMPLEMENTED}
