# Project registry and confirmation-anchor contract

## Purpose

The project-management protocol is independent from the project's code topology. Human-facing
documents remain the authority for product and technical facts; a machine registry indexes those
documents and records their current hashes so derived views can be rebuilt without guessing paths.

## Human document contract

Each product capability or feature module lives under `docs/01-product/<module>/` and should contain
`prd.md` plus `acceptance.md`. Technical implementation lives under
`docs/02-technical/<module>/technical-spec.md` and, when needed, `iteration.md`. A module may have
technical documents without a product PRD for infrastructure-only work.

## Machine registry

`tools/project_registry.py --write` scans the manifest-selected `human_docs` root and writes:

- `.guiyuan-vibecoding/registry/artifacts.toml`: artifact IDs, semantic kind, path, status,
  revision, content hash and dependencies;
- `.guiyuan-vibecoding/registry/modules.toml`: module-level PRD, acceptance and technical links;
- `.guiyuan-vibecoding/indexes/doc-tree.json`: compact input for architecture, progress and
  documentation-overview views.

The registry is derived and disposable. It never replaces the source document or becomes a second
place to edit status. Re-run it after document changes. A PRD without `acceptance.md` is reported as
a review issue rather than silently treated as complete.

## Confirmation anchors

The four user gates are `REQ` (requirements), `PLAN` (execution plan), `QA` (verification), and
`RELEASE` (封装/交付). `tools/anchor.py` writes an immutable JSON record to
`.guiyuan-vibecoding/anchors/<id>.json` containing the decision, input/output references, current
file hashes, next manager state, confirming actor and UTC timestamp. IDs end in the phase (for
example `R66-REQ`). Reusing an ID with different content is rejected; this prevents history from
being rewritten after a user confirmation.

Anchors are lifecycle evidence, not a replacement for `NOW.md`, changelog, roadmap or receipts.
At each gate, human documents may be refined from the initial concept to the final implementation
details, while the anchor preserves what was confirmed and which files were visible then.
