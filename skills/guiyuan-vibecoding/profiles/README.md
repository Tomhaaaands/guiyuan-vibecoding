# Project-type profiles

Profiles inject **content and constraints per project type** into the scaffold: extra routing
rows, red-line stubs, technical constraints, doc placeholders, and .gitignore additions.
The skeleton itself stays identical — only the injected content differs.

## Built-in presets

| Preset | Dimensions | Injects |
| --- | --- | --- |
| `default` | — | nothing (current generic behavior) |
| `script` | — | root-entry-point + runtime-pinning constraints (single-file scripts) |
| `plugin` | deploy=local-tool, data=files, surface=extension | extension module + gateway/secret red lines |
| `page` | deploy=local-tool, data=files, surface=web, runtime=node | web module (Next.js skeleton in scaffold mode) + node constraints |
| `saas` | deploy=saas, data=relational, runtime=python, surface=api-first | billing/account modules, tenant + billing red lines, data-layer/deployment stubs |
| `c-end` | deploy=c-end, data=relational, runtime=python, surface=web | auth/payment modules, payment/PII red lines, compliance stub |
| `vector-db` | deploy=local-tool, data=vector-db, runtime=python, surface=api-first | kb module, derived-index red lines, vector-layer stub |
| `cli-tool` | deploy=local-tool, data=files, runtime=python, surface=cli | cli module, local-tool constraints |
| `content-site` | deploy=local-tool, data=files, runtime=node, surface=web | content-site constraints |
| `ecommerce` | deploy=saas, data=relational, runtime=python, surface=web | catalog/cart/order payment red lines, data/deployment stubs |
| `admin-dashboard` | deploy=saas, data=relational, runtime=python, surface=web | admin authorization red line, data-layer stub |
| `bot` | deploy=local-tool, data=files, runtime=python, surface=api-first | bot secret red line |

The `script` / `plugin` / `page` presets are artifact-oriented: they match what a novice
actually uploads. In **adopt mode** `bootstrap.py` picks them automatically by fingerprint
(manifest.json -> plugin, package.json deps -> page, single root script -> script);
in **scaffold mode** `profiles/intent-map.toml` resolves a free-text description to a preset.

## Intent mapping

`profiles/intent-map.toml` is the deterministic layer for "what are you building?". The Skill
prompt asks users for one plain sentence, then `bootstrap.py --intent "<description>"` maps it to
the preset whose signal terms have the highest score. Longer matched signals win; low/medium
confidence falls back to a plain-language clarification instead of a menu. Add aliases there
rather than changing prompts, so the same description resolves to the same profile every time.

## Dimensions (composable, not exhaustive)

Four orthogonal axes; pick any combination with `--dimension "key=value"`:

- `deploy`: `saas` / `c-end` / `local-tool`
- `data`: `relational` / `vector-db` / `files`
- `runtime`: `python` / `node` / `polyglot`
- `surface`: `web` / `extension` / `cli` / `api-first`

## Custom profiles

Drop a `.toml` file anywhere and pass its path:

```bash
python .../bootstrap.py <folder> --name demo --profile /path/to/my-profile.toml
```

Schema (all keys optional):

```toml
name = "my-type"
description = "..."
dimensions = { deploy = "saas" }      # optionally reference built-in dimension files

[[modules]]
name = "foo"
keywords = "foo,bar"
code = "apps/foo"

red_lines = ["..."]
constraints = ["..."]
docs_stubs = ["00-system/data-layer.md"]
gitignore_add = [".env.local"]
```

If a dimension key is set, the matching built-in dimension file is merged first; the custom
file's own lists are appended on top.
