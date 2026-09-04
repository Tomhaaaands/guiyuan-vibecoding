# Registry and confirmation anchors · Acceptance

- A scaffolded project contains registry, state/tasks, receipts, anchors, indexes and views under
  `.guiyuan-vibecoding/`.
- Running `tools/project_registry.py --write` produces artifact/module TOML plus a doc-tree JSON
  index from the manifest-selected document root.
- Running `tools/anchor.py` for `REQ`, `PLAN`, `QA` or `RELEASE` stores referenced file hashes and
  rejects reuse of an anchor ID with different content.
- Moving code or human-document directories requires only a manifest/adapter update; derived views
  still resolve semantic state artifacts.
