# NOW - VibeCoding_Manager state card (2026-08-31)

## Focus
- R20 makes existing-project adoption lossless: assess first, then user-selected keep/map/managed
  workflow layers with baseline hashes, backups, receipts, and milestone optimization bundles.
- Public release remains skill + standard-library Python; no MCP, central registry, CreatorOS
  replacement, or Flash_assistant migration is in this round.
- Version 1.2.0 remains the public-release baseline; ZIP builds now emit SHA-256 and manifest files.

## Blockers
- The local `origin` points to a GitHub repository that no longer resolves; identify the matching
  private repository, rename it to `vibecoding-manager`, then publish only after clean release gates.
- Runtime artifact store/context compiler and behavior evaluation harness are not implemented yet.

## Next
1. Run adoption, package, sync, and isolated-install verification; split R14–R20 into reviewable commits.
2. Rename and publish the verified GitHub repository and immutable 1.2.0 release assets.
3. Install the verified skills into the current Codex root; return to P2 only after release closure.

## Authority pointers
- [Token contract](docs/token-budget.md) · [Context contract](docs/artifact-context-contract.md) · [Roadmap](docs/roadmap.md)
