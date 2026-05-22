# Propstore Core Deletion Audit - 2026-05-21

Status: in progress. Scope is every tracked Python file under `propstore/core`.

## Decision Rule

Content is kept only when all are true:

- it is in the correct owner layer;
- it does not duplicate field, schema, identity, enum parsing, family lookup,
  storage-root, or reference mechanics that should come from Quire charters,
  field metadata, or family APIs;
- it does not preserve an old path through wrappers, aliases, adapters,
  fallbacks, compatibility branches, or re-export modules;
- it does not accept loose `dict`, `object`, mixed string payloads, or
  source-local handles past the IO boundary;
- its public API is typed at the semantic boundary;
- literal search does not reveal an equivalent implementation that should own
  the behavior instead.

If any condition fails, the action is delete, move, consolidate, or rewrite.

## File Checklist

- [x] `propstore/core/__init__.py`
  - Read: 2026-05-21.
  - Action: keep shallow package initializer.
  - Reason: empty `__all__` and no eager re-exports; it does not preserve old
    paths or pull runtime owners into `core`.

- [x] `propstore/core/activation.py`
  - Read: 2026-05-21.
  - Action: rewrite/move candidate.
  - Reason: activation over compiled world graphs is real behavior, but it is
    world runtime orchestration over `CompiledWorldGraph`, `Environment`,
    condition solvers, and context lifting. It should be audited against the
    world owner boundary before being kept in `core`.
  - Required follow-up: decide whether the semantic primitive is only
    condition-activation math or whether the whole module belongs under
    `propstore.world`. If moved, delete the old `propstore.core.activation`
    import path first and update callers; no re-export module.

- [x] `propstore/core/algorithm_stage.py`
  - Read: 2026-05-21.
  - Action: delete helper functions; keep only the branded type if stage remains
    a Propstore semantic primitive.
  - Delete: `to_algorithm_stage` and `coerce_algorithm_stage`.
  - Reason: both functions are helper-shaped wrappers around the `NewType`.
    `coerce_algorithm_stage` accepts `object` and reconstructs semantic meaning
    locally instead of requiring the boundary to pass `AlgorithmStage | None`.
  - Required follow-up: update all callers to construct `AlgorithmStage(value)`
    at IO/document/app boundaries and pass typed values through runtime APIs.

## Progress

- Files read: 3 / 51.
- Next file: `propstore/core/aliases.py`.
