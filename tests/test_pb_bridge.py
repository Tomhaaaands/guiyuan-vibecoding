"""Contract tests for the VCM -> PB MCP bridge (no real PB endpoint required)."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pb_bridge


class _FixtureHandler(BaseHTTPRequestHandler):
    calls: list[str] = []

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        method = str(body.get("method", ""))
        _FixtureHandler.calls.append(method)
        params = body.get("params") or {}
        if method == "initialize":
            result = {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "guiyuan_butler_MCP", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {"name": "guiyuan_butler_capabilities"},
                    {"name": "guiyuan_butler_similarity"},
                    {"name": "guiyuan_butler_chat_context"},
                ]
            }
        elif method == "tools/call":
            name = params.get("name")
            if name == "guiyuan_butler_capabilities":
                value = {"api_version": "v1", "budgets": {"similarity_bytes": 65536}}
            elif name == "guiyuan_butler_similarity":
                args = params.get("arguments") or {}
                texts = args.get("texts") or []
                value = {
                    "results": [
                        {"index": i, "score": 0.9 if "match" in str(text) else 0.1}
                        for i, text in enumerate(texts)
                    ],
                    "count": len(texts),
                }
            else:
                value = {"context": ""}
            result = {"content": [{"type": "text", "text": json.dumps(value)}], "isError": False}
        else:
            self.send_error(404)
            return
        payload = json.dumps({"jsonrpc": "2.0", "id": body.get("id"), "result": result}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _fmt, *_args) -> None:
        return


class PbBridgeTest(unittest.TestCase):
    def setUp(self) -> None:
        pb_bridge._CAPABILITY_CACHE.clear()
        _FixtureHandler.calls.clear()
        self.httpd = ThreadingHTTPServer(("localhost", 0), _FixtureHandler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        cfg_dir = self.root / ".guiyuan-vibecoding"
        cfg_dir.mkdir()
        (cfg_dir / "config.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "pb_enabled": True,
                    "pb_endpoint": f"http://localhost:{self.httpd.server_address[1]}",
                    "pb_token": "fixture-token",
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.tmp.cleanup()
        pb_bridge._CAPABILITY_CACHE.clear()

    def test_discovery_is_cached_and_similarity_uses_formal_tool(self):
        discovered = pb_bridge.pb_capabilities(self.root)
        self.assertEqual(discovered["protocol_version"], "2025-06-18")
        self.assertIn(pb_bridge.TOOL_SIMILARITY, discovered["tools"])
        first_handshake_calls = list(_FixtureHandler.calls)

        result = pb_bridge.pb_similarity("q", ["nope", "match this"], root=self.root)
        self.assertEqual(result["results"][1]["index"], 1)
        # The second call reuses the in-memory discovery result; only tools/call is new.
        self.assertEqual(_FixtureHandler.calls[: len(first_handshake_calls)], first_handshake_calls)
        self.assertEqual(_FixtureHandler.calls.count("initialize"), 1)
        self.assertEqual(_FixtureHandler.calls.count("tools/list"), 1)

    def test_disabled_bridge_is_silent(self):
        cfg = json.loads((self.root / ".guiyuan-vibecoding" / "config.json").read_text(encoding="utf-8"))
        cfg["pb_enabled"] = False
        (self.root / ".guiyuan-vibecoding" / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        self.assertIsNone(pb_bridge.pb_capabilities(self.root))
        self.assertIsNone(pb_bridge.pb_similarity("q", ["x"], root=self.root))


if __name__ == "__main__":
    unittest.main()
