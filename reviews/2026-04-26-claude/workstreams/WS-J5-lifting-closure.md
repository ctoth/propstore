# WS-J5: Context Lifting Fixpoint Closure

**Status**: OPEN
**Depends on**: WS-J
**Blocks**: complete CKR-style worldline context provenance.

## Scope

Replace single-pass lifting materialization with a fixpoint closure over authored lifting rules and local exceptions. WS-J only made blocked exceptions observable in worldline dependencies; it did not implement transitive closure or cycle discipline.

## First Tests

- A two-hop lifting rule chain materializes the target assertion only after fixpoint iteration.
- A blocked exception on an intermediate lift prevents downstream lifts and records the blocking exception.
- Cyclic lifting rules terminate with deterministic closure metadata.

## Done Means Done

`LiftingSystem.materialize_lifted_assertions` computes a deterministic fixpoint with typed convergence metadata, and worldline dependencies include every lifting rule and blocked exception used by the closure.
