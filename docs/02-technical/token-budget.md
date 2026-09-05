# Token budget and efficiency contract

> Status: P1 extreme-budget contract (2026-08-31). Budgets cover management context and generated management
> artifacts; target source code and unavoidable tool output are measured separately.

## 1. Measured v1.2 baseline

| Content | Characters | Approximate tokens |
| --- | ---: | ---: |
| project AGENTS.md | 2,767 | 500–800 |
| project NOW.md | 279 | 50–100 |
| public guiyuan-vibecoding skill (routes internal modules) | 5,606 | 1,100–1,600 |
| internal close-loop payload (loaded only at close-out) | 2,541 | 500–800 |
| full reusable methodology | 11,965 | 2,300–3,200 |
| all project-template Markdown | 22,848 | 5,000–7,000 |

The R17 deterministic estimator measures this repository's always-loaded AGENTS + NOW package at
approximately 1,150 tokens. A copied project must remain below the 2,500 hard ceiling as part of
the full drift/pre-commit gate.

Typical v1.2 management overhead is approximately 2,000–4,000 tokens for a normal development
round. A naive vNext that loads all product/design/technical/task/history documents would grow to
15,000–30,000 tokens per task. The extreme-budget vNext target is 1,200–2,500 management tokens
per normal task, with 1,800 as the operating target and 2,500 as a blocking ceiling. Source code,
tool output, and user-provided evidence remain separate measured classes so management efficiency
cannot be hidden by reclassification.

At midpoint, this changes projected management overhead from about 3,000 tokens in v1.2 and 22,500
in a naive vNext to about 1,850: roughly 38% below v1.2 and 92% below the naive design. These are
design projections until P8 records provider-native usage across an end-to-end delivered task.

## 2. Blocking budgets

| Context class | Target budget |
| --- | ---: |
| resident pointer plane | <= 350 tokens |
| current task + acceptance | <= 550 |
| retrieved authority fields | <= 650 |
| phase policy + output schema | <= 200 |
| safety/decision reserve | <= 250 |
| normal operating target | <= 1,800 |
| normal hard ceiling | <= 2,500 |
| close-out context | <= 1,000 |
| milestone reflection batch | <= 3,500 |

Budgets are release gates, not documentation suggestions. A context compiler must emit actual
counts, included artifact fields/spans and revisions, exclusions, cache hits, and degradation steps.
If acceptance or a safety gate cannot fit, the manager blocks instead of silently truncating it.

## 3. Efficiency rules

1. **Zero-history startup**: preload neither chat history, README, changelog, archive, methodology,
   nor unrelated module docs. Start from a compact state pointer and current task id.
2. **Compile fields, not documents**: select exact authority fields or line spans; L1 is assembled
   for the task and is not a stored mini-document that gets injected wholesale.
3. **Reference instead of copy**: a fact has one authority; downstream artifacts carry ids/hashes.
4. **Evidence handles**: use receipt id + verdict + relevant excerpt; load full output only on failure,
   dispute, audit, or when the excerpt cannot support the decision.
5. **No repeated policy prose**: phase rules and output contracts are compact schemas/enums; stable
   platform policy stays outside the task package when the runtime already enforces it.
6. **Cache by content hash**: unchanged field slices and summaries are reused across tasks/models.
7. **Delta-only continuation**: after the first task turn, send changed facts, new evidence, and the
   next required decision; never replay the previous assembled package.
8. **Script instead of prompt**: routing, indexing, state transitions, readiness, diff parsing,
   checks, deduplication, token accounting, and authorization remain deterministic.
9. **Batch reflection**: distillation runs at milestone/event boundaries, not after trivial edits.
10. **Smallest capable model**: extraction/classification may use a cheap model; material decisions
    use the stronger executor; authorization stays code-based.

## 4. Extreme context compiler

The compiler fills fixed slots in priority order:


| Priority | Slot | Rule |
| --- | --- | --- |
| P0 | safety + permission | always retained; concise ids and exact constraints |
| P0 | task acceptance | always retained; measurable clauses only |
| P1 | current state/task | ids, state, blocker, next transition |
| P1 | affected authority fields | exact fields/spans required for this decision |
| P2 | recent evidence | verdict + minimal excerpt + receipt pointer |
| P3 | rationale/history | excluded unless the task disputes or changes a decision |

Compilation is two-pass: first build the smallest complete package, then spend remaining budget on
the highest-value optional evidence. Unused capacity is not a reason to add background material.
The compiler records a negative-retrieval list so repeated runs do not reconsider obviously unrelated
artifacts.

## 5. Context accounting

Each manager run records:

```text
phase, task_id, model/provider/config
resident_tokens, task_tokens, authority_tokens, policy_tokens, safety_reserve_tokens
code_tokens, tool_output_tokens, output_tokens, total_tokens
cache_hits, reused_hashes, context_degradation
included_artifact_ids/revisions/fields/spans, excluded_ids/reasons, unused_context_findings
```

Project evaluation reports:

- tokens per accepted requirement;
- tokens per delivered task;
- unused-context ratio;
- repeated fact injection count;
- context-miss rework rate;
- summary cache hit rate;
- total token delta against the v1.2 baseline and previous release.

## 6. Blocking thresholds

```text
unused management context < 10%
normal management context operating target <= 1,800 tokens
normal management context hard ceiling <= 2,500 tokens
resident pointer plane <= 350 tokens
same accepted fact injected at most once per context package
unchanged context replay = 0 tokens after the first turn
context-miss rework rate < 10%
summary/field-slice cache hit rate > 85% after the first project pass
no release increases tokens/delivered-task without an accepted product reason
```

When a budget regression is intentional, the release record must state the new capability, measured
cost, and why deterministic or cached alternatives were insufficient.


Run the context-budget tool to audit startup or selected context files. The estimator is
deliberately conservative for CJK and is a local gate until provider-native tokenizers are wired.
