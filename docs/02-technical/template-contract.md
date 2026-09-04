# Composable project template contract

> Status: v1 implemented 2026-09-04. This contract defines how a topology template changes a
> generated layout without changing the Guiyuan iteration protocol.

## 1. Composition model

```text
governance base + topology + scale + capability overlays
```

The built-in topologies are `python-service`, `web-app`, `monorepo`, `cli`, and `composite`.
`small`, `medium`, and `large` add only the structural directories appropriate to the selected
size. Overlays may add code roots, document stubs, constraints, and red lines.

## 2. Machine-facing records

Scaffold writes `.guiyuan-vibecoding/project-manifest.toml` and
`.guiyuan-vibecoding/template.lock.toml`. The manifest maps semantic artifacts (`project-state`,
`changelog`, `roadmap`, `red-lines`, and `archive`) to project-relative paths. The lock records
the source template identity; it does not contain project progress.

`docs/03-reference/template-usage.md` is the human-facing explanation generated for the selected
template. Project progress remains in the mapped state card, ledger, receipts, roadmap, and
red-line artifacts.

## 3. Compatibility

Tools resolve paths through the manifest first and use the canonical five-layer paths as a
legacy fallback. Existing projects can retain, map, or manage their workflow through the normal
adoption gate. Changing `src/`, `apps/`, `packages/`, or other code roots therefore does not
invalidate the iteration protocol.

The generated machine layer, registry and confirmation anchors are specified in
[project-registry-anchor-contract.md](project-registry-anchor-contract.md). This keeps the
human-document model and execution evidence stable across all topology templates.
