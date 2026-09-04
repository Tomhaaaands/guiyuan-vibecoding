# Registry and confirmation anchors · Technical spec

The registry is a deterministic scan over Markdown documents selected by
`.guiyuan-vibecoding/project-manifest.toml`. It writes disposable TOML/JSON views and reports a
missing product acceptance document. Anchor records are append-only JSON with SHA-256 references,
phase, decision, next state, actor and UTC creation time. Reusing an ID with changed content fails.
