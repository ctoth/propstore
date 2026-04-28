# WS-J3: Spohn OCF Kappa Revision State

**Status**: OPEN
**Depends on**: WS-J
**Blocks**: AGM/DP-strengthened iterated revision and subjective-logic uncertainty bridges that need real firmness.

## Scope

Replace positional `ranked_atom_ids` ranking with explicit Spohn OCF kappa values and firmness-aware conditionalization. WS-J deliberately did not do this; it only made worldline revision state deterministic enough for this representation change to be testable.

## First Tests

- Paper-derived Spohn 1988 A_n-conditionalization example with explicit firmness `n`.
- Snapshot round-trip preserves kappa values and firmness reasons.
- Iterated revision uses kappa arithmetic rather than list position.

## Done Means Done

No production API treats ranking position as a substitute for kappa value, and every caller that needs entrenchment reads the typed kappa surface.
