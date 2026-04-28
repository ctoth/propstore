# WS-J4: Bonanno Ternary Belief Merge

**Status**: OPEN
**Depends on**: WS-J, WS-J3
**Blocks**: merge-aware worldline revision.

## Scope

Implement Bonanno-style ternary belief change `B(h, K, phi)` for revision states with multiple merge parents. WS-J keeps the current explicit refusal for `merge_parent_commits`; this workstream owns replacing that refusal with a principled merge operator.

## First Tests

- A paper-derived Bonanno merge example where two parent states and a new formula produce the expected state.
- The current merge-point refusal test is rewritten to exercise the implemented operator.
- Journal replay records and replays the merge operator with typed parent-state inputs.

## Done Means Done

`iterated_revise` no longer raises solely because multiple merge parents exist; it either computes the Bonanno merge or raises a typed precondition error that is grounded in the operator contract.
