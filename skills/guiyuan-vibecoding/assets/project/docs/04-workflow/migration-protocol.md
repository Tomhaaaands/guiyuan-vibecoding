# Architecture Migration Protocol

## Detection standard

Before adoption, run `python tools/architecture_audit.py <project>` (read-only). It reports:

- legacy `Apps/` or `workers/` directories versus canonical lowercase `apps/` and `workers/`;
- root product/technical docs that have no `01-product/` or `02-technical/` destination;
- root `CHANGELOG.md`, `NOW.md`, and `docs/` ownership conflicts;
- empty canonical directories that need placeholders.

The audit never moves, deletes, or overwrites files. A conflict is actionable only when a source
and destination both contain content; an empty destination is safe to create with `.gitkeep`.

## Migration sequence

1. Audit and record a baseline JSON report outside the project.
2. Classify each item as `keep`, `map`, or `managed`.
3. For `map`, add routing pointers without moving author content.
4. For `managed`, copy to the canonical layer after hashing and backing up the original under
   `.guiyuan-vibecoding/pre-adoption/`.
5. Re-run the audit and require zero unresolved conflicts before enabling automatic writes.

Migration is incremental and user-confirmed; adoption must never silently merge two authorities.
