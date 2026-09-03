#!/usr/bin/env python3
"""Provider registry for P2 semantic analysis (deterministic + reserved backends).

The provider is an isolated, replaceable "semantic executor": it never imports the
artifact store or context compiler and only returns a structured AnalysisResult dict.
The default backend is a deterministic local heuristic; real model backends are
registered here as stubs and are selected by name, never imported by the core loop.

Config (read-only, reserved): VCM_ANALYSIS_PROVIDER env var, or <root>/.vibecoding/provider.toml.

Usage:
  python tools/analysis_provider.py local-fallback --intent "build an email login"
  python tools/analysis_provider.py --list
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from analysis_labels import LABEL_BUCKETS

sys.stdout.reconfigure(encoding="utf-8")


class ProviderError(RuntimeError):
    """Raised when a provider cannot produce a usable AnalysisResult."""


class AnalysisProvider:
    """Minimal provider interface. Implementations only return a labeled dict."""

    name = "base"
    model = "none"

    def analyze(self, intent: str, context: dict | None = None) -> dict:
        raise NotImplementedError

    def judge_red_line(self, statement: str, red_line: str) -> dict:
        """Return {'verdict': 'respects'|'violates'|'unknown', 'confidence', 'reason'}.

        The default is conservative: a provider that cannot judge returns 'unknown', which
        the orchestrator treats as needing confirmation rather than accepted.
        """
        return {"verdict": "unknown", "confidence": 0.0, "reason": "provider cannot judge"}


class LocalFallbackProvider(AnalysisProvider):
    """Deterministic heuristic fallback that always yields a structurally valid result."""

    name = "local-fallback"
    model = "heuristic-v1"

    def analyze(self, intent: str, context: dict | None = None) -> dict:
        intent = (intent or "").strip()
        if not intent:
            raise ProviderError("intent is empty")
        return {
            "intent": intent,
            "known_facts": [
                {
                    "id": "f1",
                    "statement": f"User stated an intent: {intent}",
                    "source": "intent",
                    "confidence": 0.4,
                }
            ],
            "assumptions": [
                {
                    "id": "a1",
                    "statement": "No explicit constraints supplied; assume minimal viable scope.",
                    "source": "heuristic",
                    "confidence": 0.2,
                }
            ],
            "options": [],
            "decisions": [],
            "open_questions": [
                {
                    "id": "q1",
                    "statement": f"Clarify success criteria and acceptance for: {intent}",
                    "source": "heuristic",
                    "confidence": 1.0,
                }
            ],
        }


class SiliconFlowProvider(AnalysisProvider):
    """OpenAI-compatible chat backend over SiliconFlow (stdlib urllib, key via env)."""

    name = "siliconflow"
    model = "Qwen/Qwen3-8B"
    default_base = "https://api.siliconflow.cn/v1"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        self.model = model or os.environ.get("VCM_SILICONFLOW_MODEL") or self.model
        self.base_url = (
            base_url
            or os.environ.get("VCM_SILICONFLOW_BASE_URL")
            or self.default_base
        ).rstrip("/")
        self.api_key = (
            api_key
            or os.environ.get("VCM_SILICONFLOW_API_KEY")
            or os.environ.get("SILICONFLOW_API_KEY")
            or ""
        )

    def analyze(self, intent: str, context: dict | None = None) -> dict:
        if not self.api_key:
            raise ProviderError("siliconflow API key is not configured (set VCM_SILICONFLOW_API_KEY)")
        prompt = _build_prompt(intent, context)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
        }
        content = self._chat(payload)
        return _parse_model_json(content, intent)

    def _chat(self, payload: dict) -> str:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            err = exc.read().decode("utf-8", "replace")[:300]
            raise ProviderError(f"siliconflow HTTP {exc.code}: {err}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"siliconflow unreachable: {exc.reason}") from exc
        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("siliconflow returned an unexpected response shape") from exc

    def judge_red_line(self, statement: str, red_line: str) -> dict:
        content = self._chat(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": _JUDGE_SYSTEM},
                    {
                        "role": "user",
                        "content": f"red line:\n{red_line}\n\nproposed decision or option:\n{statement}",
                    },
                ],
                "temperature": 0.0,
            }
        )
        return _parse_judge(content)


# Registry: name -> class. Future real backends slot in here without touching core.
PROVIDERS: dict[str, type[AnalysisProvider]] = {
    "local-fallback": LocalFallbackProvider,
    "siliconflow": SiliconFlowProvider,
}


_SYSTEM_PROMPT = (
    "You are an R&D analysis engine. Given the user's product/design/technical intent, "
    "return ONLY strict JSON with exactly these keys: "
    '"known_facts", "assumptions", "options", "decisions", "open_questions". '
    "Each key maps to a list of objects shaped as {\"id\": \"k1\", \"statement\": \"...\", "
    "\"source\": \"intent|inference|context\", \"confidence\": 0.0-1.0}. "
    "Do not invent certainty: leave a bucket empty when the intent does not support it, and put "
    "anything you must clarify into open_questions. No prose before or after the JSON."
)


def _build_prompt(intent: str, context: dict | None) -> str:
    lines = ["Intent:", intent]
    if context:
        lines.append("Context:")
        lines.append(json.dumps(context, ensure_ascii=False))
    return "\n".join(lines)


def _parse_model_json(content: str, intent: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"model returned non-JSON: {text[:200]}") from exc
    if not isinstance(result, dict):
        raise ProviderError("model JSON is not an object")
    result["intent"] = result.get("intent", intent)
    return result


_JUDGE_SYSTEM = (
    "You are a governance guard. A project has an irreversible red line. Judge whether the "
    "proposed decision or option violates that red line. Return ONLY strict JSON "
    '{"verdict": "respects" | "violates" | "unknown", "confidence": 0.0-1.0, "reason": "..."}. '
    'Use "violates" only when the proposal directly enables what the red line forbids; use '
    '"unknown" when you cannot decide; otherwise "respects".'
)


def _parse_judge(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"verdict": "unknown", "confidence": 0.0, "reason": "unparseable judgment"}
    verdict = str(data.get("verdict", "unknown")).lower()
    if verdict not in ("respects", "violates", "unknown"):
        verdict = "unknown"
    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    return {"verdict": verdict, "confidence": confidence, "reason": str(data.get("reason", ""))}


def embed_statements(
    texts: list[str],
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = "BAAI/bge-m3",
    batch: int = 64,
) -> list[list[float]]:
    """Embed a list of statements via SiliconFlow's OpenAI-compatible /embeddings endpoint."""
    key = api_key or os.environ.get("VCM_SILICONFLOW_API_KEY") or os.environ.get("SILICONFLOW_API_KEY")
    if not key:
        raise ProviderError("siliconflow API key is not configured (set VCM_SILICONFLOW_API_KEY)")
    base = (base_url or os.environ.get("VCM_SILICONFLOW_BASE_URL") or SiliconFlowProvider.default_base).rstrip("/")
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch):
        chunk = texts[start : start + batch]
        payload = {"model": model, "input": chunk}
        request = urllib.request.Request(
            f"{base}/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            err = exc.read().decode("utf-8", "replace")[:300]
            raise ProviderError(f"siliconflow embedding HTTP {exc.code}: {err}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"siliconflow embedding unreachable: {exc.reason}") from exc
        data = body.get("data", [])
        order = sorted(data, key=lambda item: item.get("index", 0))
        if len(order) != len(chunk):
            raise ProviderError("siliconflow embedding returned a mismatched batch")
        vectors.extend(item["embedding"] for item in order)
    return vectors


def _config_file(root: Path) -> Path:
    return Path(root) / ".vibecoding" / "provider.toml"


def parse_config(root: Path) -> dict:
    """Read <root>/.vibecoding/provider.toml (tomllib) if present; never requires it."""
    path = _config_file(root)
    if not path.is_file():
        return {}
    try:
        import tomllib

        with path.open("rb") as handle:
            return tomllib.load(handle)
    except Exception as exc:  # noqa: BLE001 - config must never break the core
        print(f"[provider] cannot read config {path}: {exc}", file=sys.stderr)
        return {}


def resolve_provider(root: Path | None = None, explicit: str | None = None) -> str:
    """Return the provider name in priority: explicit > env > config > local-fallback."""
    if explicit:
        return explicit
    if os.environ.get("VCM_ANALYSIS_PROVIDER"):
        return os.environ["VCM_ANALYSIS_PROVIDER"]
    if root is not None:
        config = parse_config(root)
        name = config.get("analysis", {}).get("provider")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return "local-fallback"


def load_provider(name: str) -> AnalysisProvider:
    cls = PROVIDERS.get(name)
    if cls is None:
        print(
            f"[provider] unknown backend {name!r}; falling back to local-fallback",
            file=sys.stderr,
        )
        return LocalFallbackProvider()
    return cls()


def _slug(intent: str, limit: int = 40) -> str:
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", intent.lower()).strip("-")
    return slug[:limit].strip("-") or "intent"


def main() -> None:
    parser = argparse.ArgumentParser(description="Provider registry and local fallback")
    parser.add_argument("--list", action="store_true", help="list registered backends")
    parser.add_argument("--intent", help="intent text to analyze")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.list:
        for name, cls in PROVIDERS.items():
            print(f"{name} ({cls().model})")
        return
    if not args.intent:
        parser.error("provide --intent")

    name = resolve_provider(args.root, args.provider)
    provider = load_provider(name)
    result = provider.analyze(args.intent)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"provider={provider.name} model={provider.model}")
        for bucket in LABEL_BUCKETS:
            for item in result[bucket]:
                print(f"  {bucket}: {item['statement']}")


if __name__ == "__main__":
    main()
