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

- [x] `propstore/core/aliases.py`
  - Read: 2026-05-21.
  - Action: move or delete from `core`.
  - Reason: the module opens repository family handles and exports a concept
    alias report. That is repository/app/family presentation behavior, not a
    core semantic primitive. It imports `Repository`,
    `parse_concept_record_document`, and identity helper code, so keeping it in
    `core` violates owner layering.
  - Required follow-up: find callers. If the export is still used, move it to
    the concept app/family owner and delete the `propstore.core.aliases` import
    path first; no core re-export.

- [x] `propstore/core/analyzers.py`
  - Read: 2026-05-21.
  - Action: delete from `core`; move real analyzer orchestration to the
    world/argumentation owner.
  - Reason: it builds active-world analyzer inputs, converts family records to
    graph rows, constructs Dung/bipolar/PrAF frameworks, runs claim-graph and
    PrAF analysis, wraps ASPIC backend solving, and projects analyzer results.
    That is world/argumentation runtime orchestration, not core primitive
    ownership.
  - Delete: `propstore/core/analyzers.py` as an import path.
  - Required follow-up: create the target owner only as
    `propstore/world/analyzers.py` or another explicitly chosen
    world/argumentation owner, update every caller, and leave no
    `propstore.core.analyzers` shim, alias, or package re-export.
  - Additional cleanup: remove helper-shaped local coercion inside the moved
    code, including `coerce_graph_relation_type("rebuts")` and broad
    query-claim-id normalization that accepts multiple loose collection shapes
    past the owner boundary.

- [x] `propstore/core/anytime.py`
  - Read: 2026-05-21.
  - Action: keep as a narrow core result sentinel.
  - Reason: `EnumerationExceeded` is typed, small, and does not duplicate field
    metadata, storage mechanics, family lookup, compatibility handling, or old
    import paths. It is a cross-cutting computation sentinel, not an IO parser
    or owner-specific workflow.

## Progress

- Files read: 6 / 51.
- Next file: `propstore/core/assertions/__init__.py`.
