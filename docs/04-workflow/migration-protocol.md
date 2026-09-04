# Architecture Migration Protocol

## Detection standard

Run `python tools/architecture_audit.py <project>` in read-only mode before adoption. It checks
legacy `Apps/`/`Workers/` names, root authority documents, missing canonical `docs` layers, and
author-owned `CHANGELOG.md`, `NOW.md`, and `docs/` content.

## Migration sequence

1. Record the audit JSON outside the project.
2. Classify each item as `keep`, `map`, or `managed`.
3. Map without moving author content; manage only after user confirmation, hash verification, and
   backup under `.guiyuan-vibecoding/pre-adoption/`.
4. Re-run the audit and require zero unresolved conflicts before automatic writes.

The process is incremental and never silently merges two authorities.
