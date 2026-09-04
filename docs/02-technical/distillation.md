# Distillation pipeline

> Status: `pitfalls` (坑 → 红线) implemented (2026-08-30, deterministic first pass); the other
> three directions are stubs. Distillation reads project archives only — it does **not** depend
> on Private_butler or any external memory/embedding service. CLI: `tools/distill.py`.

## Why distillation

Guiyuan Vibecoding is a per-project "project manager" kit. For it to self-iterate, each project
must periodically distill its private experience — pitfalls, proven methods, matured
conclusions — into reusable assets, so the next project starts smarter.

## Four directions

| Direction | Transform | Status | Source -> Target |
| --- | --- | --- | --- |
| pitfalls | 坑 -> 红线 | ✅ implemented | archive volumes + module `iteration.md` -> `red-lines.draft.md` (review → `red-lines.md`) |
| method | 方法 -> 模板 | stub | a proven workflow in archive -> `templates/` + `profiles/` |
| consolidate | 碎片 -> 结论 | stub | repeated module facts -> one stable conclusion per fact |
| promote | 私有 -> 共性 | stub | one project's reusable lesson -> shared kit (`templates/` / `skills/`) |

## Loop

1. **capture** — archive volumes and module state cards already record what happened;
2. **review** — a milestone or node triggers distillation (periodic or event-driven);
3. **distill** — run one of the four directions (`python tools/distill.py <direction>`);
4. **commit** — the lifted asset lands in templates / skills / profiles in the same round;
5. **verify** — `python tools/check_drift.py` + `python tools/install_skills.py --doctor`.

## Boundaries

- Red lines and key decisions are **never archived**; the `pitfalls` direction emits a
  `[AI-DRAFT]` candidate list, and a human promotes confirmed items into `red-lines.md`
  (the tool never auto-writes the authoritative red-line doc).
- Only **reusable** lessons are promoted; project-private facts stay in the project.
- The life-manager memory system (Private_butler) handles *personal* memory separately; this
  pipeline distills *project* experience only.
