# Provider integration boundary (P2)

> Status: contract (2026-09-03). The deterministic core never imports a provider; this
> document fixes where a model backend may appear and how it is selected, degraded, and gated.

## 1. Principle

A provider is a replaceable *semantic executor*, not a dependency. The artifact store, context
compiler, and behavior harness stay provider-free. Only the analysis orchestrator may call one,
and it only accepts a validated, structured `AnalysisResult` back.

## 2. Ownership map

| Module | Responsibility | May import a provider |
| --- | --- | --- |
| `tools/artifact_store.py` | typed authority artifacts | no |
| `tools/context_compiler.py` | L0/L1 views + budget | no |
| `tools/behavior_harness.py` | deterministic behavior scenarios | no |
| `tools/analysis_labels.py` | labeled-output validation + gold scoring | no |
| `tools/analysis_provider.py` | provider registry + config + local fallback | self only |
| `tools/analysis.py` | orchestration, idempotency, persistence | yes (via registry) |
| `tools/analysis_eval.py` | score a provider against gold fixtures; semantic mode calls PB's public scorer | yes (via registry + PB bridge) |

Call chain: `analysis -> provider (JSON only) -> context_compiler (read-only) -> artifact_store
(sole writer)`. A provider never touches the store or the compiler directly.

## 3. Result contract

`AnalysisResult` has five labeled buckets - `known_facts`, `assumptions`, `options`,
`decisions`, `open_questions` - each item `{id, statement, source?, confidence?}`, plus
provenance `{provider, model, idempotency_key, context_id, created_at}`.

Rules:
- validated by `analysis_labels.validate_labels` before any write;
- `status` is only `draft` or `review`; a provider alone can never mark `accepted`;
- on invalid output the orchestrator rejects it (local fallback cannot fail this way).

## 4. Config and selection

- `VCM_ANALYSIS_PROVIDER` env var; fallback `<root>/.vibecoding/provider.toml`
  (`[analysis] provider = "..."`), read-only via tomllib;
- default `local-fallback` (deterministic heuristic);
- future backends register in `PROVIDERS` and never import the core.

## 5. Degradation, idempotency, safety

  - order: configured backend -> failure/timeout -> stored prior result (flagged stale) ->
    `local-fallback`;
  - idempotency key = `sha256(provider | red-line-hash | intent | context_hash)[:16]`; a matching
    stored result is reused, never re-invoked; a change to the red lines re-runs the analysis;
  - safety: project red-line enforcement is implemented in `tools/analysis.py`. It loads
    `red-lines.md` (root) or `docs/00-system/constitution/red-lines.md` (legacy), shortlists
    `decisions`/`options` that touch a red-line topic (char-bigram Dice >= 0.25), then asks the
    selected backend's `judge_red_line` for `respects`/`violates`/`unknown`. `violates` and `unknown`
    are surfaced as `open_questions` (with `red_line_touch`); `respects` keeps the item marked
    `red_line_reviewed`. A provider that cannot judge, or a failed judge call, degrades to `unknown`
    and is surfaced rather than accepted;
- budget: the provider request context is compiled by `context_compiler` under the hard ceiling;
  the response size also counts toward the estimate.

## 6. Persistence

Each result is written as an `analysis/<slug>` authority artifact at `draft`; promotion to
`accepted` requires an explicit gate. This adds an `analysis` kind to the authority artifact
catalog and closes the ANALYSIS-phase persistence gap.

## 7. Promotion gate

`tools/analysis_eval.py` runs a provider against gold fixtures via
`analysis_labels.score_labels` and only allows promotion when aggregate F1 meets `--min-f1`.
Gold fixtures live under `tools/fixtures/analysis/` and are written at **sentence granularity**
(matching how a real analysis expresses a fact/decision), which is what makes the semantic metric
meaningful.

Historical local calibration (before PB became the semantic scorer; these numbers are not current
PB acceptance evidence):

| backend | model | aggregate F1 |
| --- | --- | --- |
| `local-fallback` | heuristic-v1 | ~0.169 |
| `siliconflow` | Qwen/Qwen3-8B | ~0.299 |

The current semantic gate has no production aggregate until a reachable PB endpoint with its
configured embedder is exercised; fixture and bridge tests prove only protocol behavior.

The `siliconflow` backend is registered in `tools/analysis_provider.py` and reads its API key from
`VCM_SILICONFLOW_API_KEY` (never from a committed file); model/base-url default to
`Qwen/Qwen3-8B` and `https://api.siliconflow.cn/v1`.

The default gate is `--mode semantic` (PB-managed cosine, cutoff 0.70) with `--min-f1 0.25`.
The lexical char-bigram
`--mode similarity` is retained but documented as **not sound on sentence-level gold**: it is fooled
by `local-fallback` echoing the intent, so it is only suitable for
dependency-free feature/regression experiments, not as the promotion gate.

Semantic scoring delegates query-against-text comparisons to PB's
`guiyuan_butler_similarity` v1 tool. VCM receives only scores and never receives, stores or
selects an embedding model; the PB endpoint and token come from the project's
`.guiyuan-vibecoding/config.json`. The gate first performs PB's
`initialize` → `tools/list` → `guiyuan_butler_capabilities` handshake and fails closed when the
semantic capability is unavailable. Red-line enforcement inside the analysis step is implemented
(see section 5).
