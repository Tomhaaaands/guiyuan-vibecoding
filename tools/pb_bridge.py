#!/usr/bin/env python3
"""VCM-side bridge to 归园大管家 / Guiyuan Butler (Guiyuan Butler).

Follows the PB package's `docs/api-contract.md` (v1):

- MCP endpoint: `POST <pb_endpoint>/mcp`, JSON-RPC `tools/call`.
- Auth: `Authorization: Bearer <pb_token>`.
- Health: `GET <pb_endpoint>/healthz` (no token).
- Tools: `guiyuan_butler_chat_context`, `guiyuan_butler_capture`,
  `guiyuan_butler_similarity`. No `memory_*` aliases.

Reads `.guiyuan-vibecoding/config.json` (``pb_enabled``, ``pb_endpoint``, ``pb_token``). Every call
degrades gracefully to ``None`` when PB is disabled, unreachable, or returns an error.  The bridge
can also perform the MCP ``initialize`` → ``tools/list`` → ``guiyuan_butler_capabilities``
discovery handshake; its in-memory cache never persists endpoint credentials or PB data.
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
PROTOCOL_VERSION = "2025-06-18"
TOOL_MEMORY_CONTEXT = "guiyuan_butler_chat_context"
TOOL_MEMORY_RESULT = "guiyuan_butler_capture"
TOOL_SIMILARITY = "guiyuan_butler_similarity"
TOOL_CAPABILITIES = "guiyuan_butler_capabilities"
SIMILARITY_MAX_TEXTS = 100
SIMILARITY_MAX_BYTES = 64 * 1024
SIMILARITY_MAX_TEXT_BYTES = 16 * 1024
CAPABILITY_CACHE_TTL = 300.0

# {endpoint, token} -> (monotonic timestamp, sanitized discovery result)
_CAPABILITY_CACHE: dict[tuple[str, str], tuple[float, dict[str, object]]] = {}


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


def _request(
    endpoint: str,
    body: dict[str, object],
    timeout: int,
    token: str,
) -> dict[str, object] | None:
    """POST one JSON-RPC request and return its outer ``result`` object.

    JSON-RPC errors, HTTP errors, malformed responses and transport failures are
    deliberately collapsed to ``None`` so callers can apply their local fallback.
    """
    url = _base(endpoint) + "/mcp"
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            response = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    if not isinstance(response, dict) or response.get("error") is not None:
        return None
    result = response.get("result")
    return result if isinstance(result, dict) else None


def _decode_result(result: dict[str, object] | None) -> dict | None:
    """Decode PB's MCP text envelope while preserving direct protocol results."""
    if not isinstance(result, dict) or result.get("isError"):
        return None
    text = ""
    content = result.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = str(item.get("text", ""))
                break
    if not text:
        return result
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"text": text}
    return value if isinstance(value, dict) else {"value": value}


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
    result = _request(
        endpoint,
        {
            "jsonrpc": "2.0",
            "id": "vcm-" + os.urandom(4).hex(),
            "method": "tools/call",
            "params": {"name": method, "arguments": params},
        },
        timeout,
        token,
    )
    return _decode_result(result)


def _protocol_rpc(
    endpoint: str,
    method: str,
    params: dict[str, object],
    timeout: int,
    token: str,
) -> dict | None:
    result = _request(
        endpoint,
        {
            "jsonrpc": "2.0",
            "id": "vcm-" + os.urandom(4).hex(),
            "method": method,
            "params": params,
        },
        timeout,
        token,
    )
    return _decode_result(result)


def pb_capabilities(
    root: Path | None = None,
    timeout: int = 4,
    *,
    refresh: bool = False,
) -> dict[str, object] | None:
    """Discover the PB protocol and public tools, caching only sanitized metadata.

    The returned object contains ``protocol_version``, ``server_info``, ``tools``
    (names only) and the capability payload.  Tokens and raw memory content are
    never returned or persisted.  ``None`` means PB is disabled or the handshake
    failed and callers should use their documented fallback.
    """
    cfg = config(root)
    if not cfg["pb_enabled"]:
        return None
    endpoint = _base(str(cfg["pb_endpoint"]))
    token = str(cfg["pb_token"] or "")
    key = (endpoint, token)
    now = time.monotonic()
    cached = _CAPABILITY_CACHE.get(key)
    if not refresh and cached and now - cached[0] < CAPABILITY_CACHE_TTL:
        return dict(cached[1])

    initialize = _protocol_rpc(
        endpoint,
        "initialize",
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "guiyuan-vibecoding", "version": "v1"},
        },
        timeout,
        token,
    )
    tools_result = _protocol_rpc(endpoint, "tools/list", {}, timeout, token)
    if not isinstance(initialize, dict) or not isinstance(tools_result, dict):
        return None
    raw_tools = tools_result.get("tools")
    names = [
        str(tool.get("name"))
        for tool in (raw_tools if isinstance(raw_tools, list) else [])
        if isinstance(tool, dict) and tool.get("name")
    ]
    capabilities = _rpc(endpoint, TOOL_CAPABILITIES, {}, timeout, token)
    discovered: dict[str, object] = {
        "protocol_version": str(initialize.get("protocolVersion") or ""),
        "server_info": initialize.get("serverInfo") if isinstance(initialize.get("serverInfo"), dict) else {},
        "tools": names,
        "capabilities": capabilities if isinstance(capabilities, dict) else {},
    }
    _CAPABILITY_CACHE[key] = (now, discovered)
    return dict(discovered)


def pb_tool_available(
    name: str,
    root: Path | None = None,
    timeout: int = 4,
    *,
    refresh: bool = False,
) -> bool:
    """Return whether a discovered PB tool is actually exposed to this token."""
    discovered = pb_capabilities(root, timeout, refresh=refresh)
    return bool(discovered and name in set(discovered.get("tools", [])))


def pb_memory_context(query: str, root: Path | None = None, timeout: int = 4,
                      max_tokens: int = 800) -> dict | None:
    cfg = config(root)
    if not cfg["pb_enabled"]:
        return None
    if not pb_tool_available(TOOL_MEMORY_CONTEXT, root, timeout):
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
    cfg = config(root)
    if not cfg["pb_enabled"]:
        return None
    if not pb_tool_available(TOOL_SIMILARITY, root, timeout):
        return None
    return _rpc(
        str(cfg["pb_endpoint"]), TOOL_SIMILARITY,
        {"api_version": "v1", "query": query, "texts": texts}, timeout, str(cfg["pb_token"] or ""),
    )
