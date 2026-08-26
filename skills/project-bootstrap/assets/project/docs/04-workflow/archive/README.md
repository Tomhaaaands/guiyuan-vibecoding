# Iteration Archive (archive)

> Full archive volumes behind the `changelog.md` one-line ledger — archaeology only, not for daily reading.

## Rules

- one file per numbered round: `YYYY-MM-DD-rNN.md`;
- every round's full detail (root cause / implementation / verification) goes into its volume;
  the changelog keeps only one index row;
- **red lines, pitfalls, key decisions are never archived**: they stay in module `iteration.md`
  and the red-line doc;
- create a volume with `python tools/rollup_round.py --round R27 --date 2026-08-23 --module docs --summary "..." --detail path/to/detail.md`.
