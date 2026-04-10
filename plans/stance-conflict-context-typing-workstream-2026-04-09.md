# Stance, Conflict, And Context Typing Workstream

Date: 2026-04-09

## Goal

Replace the remaining `dict`-shaped stance, conflict, and context flow in the world/store boundary with explicit typed objects.

This is the next important slice after:
- typed sidecar concept rows
- typed claim rows
- typed nested claim source/provenance values
- typed runtime active claims

The problem is no longer claim identity or claim runtime shape. The remaining leak is that stance, conflict, and context surfaces are still repeatedly converted back to anonymous maps in the core semantic/runtime path.

Target outcome:
- `StanceRow` remains the stance boundary
- `ConflictRow` remains the conflict boundary
- context loading from the sidecar uses typed context objects directly
- store protocols stop advertising `list[dict]` for stance/conflict/context semantics
- `BoundWorld` and `HypotheticalWorld` stop turning typed rows back into dicts except at explicit UI/serialization edges

## Why This Slice Next

This is the cleanest continuation of the runtime-claim work:

- [environment.py](/C:/Users/Q/code/propstore/propstore/core/environment.py) still exposes `explain() -> list[dict]`
- [bound.py](/C:/Users/Q/code/propstore/propstore/world/bound.py) still returns `list[dict]` from `conflicts()` and `explain()`
- [hypothetical.py](/C:/Users/Q/code/propstore/propstore/world/hypothetical.py) still stores overlay stances/conflicts as `list[dict]`
- [model.py](/C:/Users/Q/code/propstore/propstore/world/model.py) still rebuilds context payload dicts in `_load_context_hierarchy()`

Those are all places where we already have typed domain-ish row/context objects available, then discard them and fall back to map-shuffling.

## Non-goals

- Do not redesign revision/report/worldline output payloads here.
- Do not redesign sidecar schema.
- Do not redesign claim runtime typing again.
- Do not merge row types and canonical domain types into one class family.
- Do not preserve dict and typed production paths in parallel once the slice is complete.

## Existing Typed Surfaces To Reuse

- `StanceRow` in [row_types.py](/C:/Users/Q/code/propstore/propstore/core/row_types.py)
- `ConflictRow` in [row_types.py](/C:/Users/Q/code/propstore/propstore/core/row_types.py)
- `ContextRecord` and `LoadedContext` in [context_types.py](/C:/Users/Q/code/propstore/propstore/context_types.py)
- `ContextHierarchy` in [validate_contexts.py](/C:/Users/Q/code/propstore/propstore/validate_contexts.py)
- `ContextId`, `ClaimId`, `ConceptId` in [id_types.py](/C:/Users/Q/code/propstore/propstore/core/id_types.py)
- `BeliefSpace` in [types.py](/C:/Users/Q/code/propstore/propstore/world/types.py)
- `ArtifactStore` and adjacent protocols in [environment.py](/C:/Users/Q/code/propstore/propstore/core/environment.py)

Do not reuse as the semantic control surface:
- raw `sqlite3.Row`
- anonymous `dict` stance chains
- anonymous `dict` conflict payloads
- intermediate `contexts_by_id: dict[str, dict[str, Any]]`

## Architectural Invariants

- `dict` is allowed at decode/encode boundaries only.
- `StanceRow` and `ConflictRow` are row-boundary types, not generic payload bags.
- context sidecar loading must materialize typed context objects immediately.
- world/runtime code must not call `.to_dict()` on stance/conflict/context objects unless it is crossing an explicit reporting or serialization boundary.
- if we control both sides of an interface, change the interface and update every caller.

## Main Leaks To Eliminate

### Leak 1: Explanation path returns `dict`

Current shape:
- `ExplanationStore.explain()` in [environment.py](/C:/Users/Q/code/propstore/propstore/core/environment.py) returns `list[dict]`
- `WorldModel.explain()` in [model.py](/C:/Users/Q/code/propstore/propstore/world/model.py) already builds `StanceRow`
- `BoundWorld.explain()` in [bound.py](/C:/Users/Q/code/propstore/propstore/world/bound.py) converts those typed rows back to dicts
- `_GraphOverlayStore.explain()` in [hypothetical.py](/C:/Users/Q/code/propstore/propstore/world/hypothetical.py) does the same

Required fix:
- make the protocol and world/boundary methods return `Sequence[StanceRowInput]`
- keep `to_dict()` only for CLI/report edges that truly serialize explanation chains

### Leak 2: Conflict path returns `dict`

Current shape:
- `BeliefSpace.conflicts()` in [types.py](/C:/Users/Q/code/propstore/propstore/world/types.py) returns `list[dict]`
- `ConflictStore.conflicts()` in [environment.py](/C:/Users/Q/code/propstore/propstore/core/environment.py) is already typed-ish
- `BoundWorld.conflicts()` in [bound.py](/C:/Users/Q/code/propstore/propstore/world/bound.py) converts `ConflictRow` back to dicts and recomputed conflicts are also dict payloads
- `HypotheticalWorld` stores and recomputes overlay conflicts as dict payloads in [hypothetical.py](/C:/Users/Q/code/propstore/propstore/world/hypothetical.py)

Required fix:
- define the world/runtime conflict surface explicitly as `ConflictRow`
- make recomputed conflicts produce `ConflictRow`, not `dict`
- update `BeliefSpace.conflicts()` and direct callers to consume typed conflicts

### Leak 3: Sidecar context loading rebuilds dict payloads

Current shape:
- `_load_context_hierarchy()` in [model.py](/C:/Users/Q/code/propstore/propstore/world/model.py) creates `contexts_by_id: dict[str, dict[str, Any]]`
- assumptions and exclusions are appended into those dicts
- the dicts are then reparsed into `LoadedContext`

Required fix:
- add a direct typed load path from SQL rows into `ContextRecord` or a small `ContextRow`
- construct `LoadedContext` without the anonymous intermediate payload map

## Proposed Type Surface

### Stance and conflict surfaces

No new semantic type family is required if `StanceRow` and `ConflictRow` already carry the real row shape.

The work here is interface tightening:
- `ExplanationStore.explain() -> Sequence[StanceRowInput]`
- `BeliefSpace.conflicts() -> list[ConflictRow]`
- `BoundWorld.conflicts() -> list[ConflictRow]`
- `HypotheticalWorld.conflicts() -> list[ConflictRow]`
- `BoundWorld.explain() -> list[StanceRow]`
- `HypotheticalWorld.explain() -> list[StanceRow]`

If a report/UI edge wants dicts, that edge should explicitly project them.

### Context sidecar surface

There are two acceptable implementations:

Option A:
- load SQL rows directly into `ContextRecord`
- add a local helper in [model.py](/C:/Users/Q/code/propstore/propstore/world/model.py) that builds `LoadedContext` from typed fields

Option B:
- add a small explicit `ContextRow` dataclass near the row types
- convert `ContextRow -> ContextRecord -> LoadedContext`

Preferred default:
- Option A unless a reusable store/query context row type is clearly needed outside `_load_context_hierarchy()`

The important part is not the exact class name. The important part is deleting the `dict[str, Any]` middle step.

## File Clusters

### Cluster A: Store protocols and world interfaces

Primary files:
- [environment.py](/C:/Users/Q/code/propstore/propstore/core/environment.py)
- [types.py](/C:/Users/Q/code/propstore/propstore/world/types.py)

Work:
- tighten `ExplanationStore.explain()` to `Sequence[StanceRowInput]`
- tighten `BeliefSpace.conflicts()` to `list[ConflictRow]`
- tighten `BeliefSpace.explain()` to `list[StanceRow]`
- update any remaining protocol signatures that still force `list[dict]` for these surfaces

Delete:
- dict-shaped explanation/conflict signatures we control

### Cluster B: Bound world stance/conflict flow

Primary files:
- [bound.py](/C:/Users/Q/code/propstore/propstore/world/bound.py)

Work:
- make `_recomputed_conflicts(...)` return `list[ConflictRow]`
- make `conflicts()` traffic in `ConflictRow` end to end
- make `explain()` traffic in `StanceRow` end to end
- remove `.to_dict()` calls from the world/runtime path
- update caches and local helper types accordingly

Important:
- preserve current semantic filtering behavior
- only change representation, not conflict/explanation semantics

### Cluster C: Hypothetical overlay stance/conflict flow

Primary files:
- [hypothetical.py](/C:/Users/Q/code/propstore/propstore/world/hypothetical.py)

Work:
- replace `_stances: list[dict]` with typed stance rows
- replace `_conflicts: list[dict]` with typed conflict rows
- update overlay store methods to return typed rows
- update recomputed conflict path to use typed `ConflictRow`
- keep dict projection only at explicit external edges if any exist

Delete:
- overlay conflict/stance dict storage

### Cluster D: Sidecar context hierarchy loading

Primary files:
- [model.py](/C:/Users/Q/code/propstore/propstore/world/model.py)
- [context_types.py](/C:/Users/Q/code/propstore/propstore/context_types.py)

Work:
- delete `contexts_by_id: dict[str, dict[str, Any]]`
- load base context rows into typed objects immediately
- attach assumptions/exclusions to typed objects, not payload dicts
- construct `ContextHierarchy` from typed `LoadedContext`

Open design choice:
- whether to add a reusable `ContextRow`
- default to no new row type unless it materially simplifies multiple callers

### Cluster E: Direct typed callers and serialization edges

Primary files:
- CLI/report callers discovered during implementation
- likely [compiler_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/compiler_cmds.py)
- any worldline/report module that serializes explanation/conflict output

Work:
- update callers to consume typed stance/conflict rows
- where dict output is genuinely required, project there with `to_dict()`
- do not leak that projection back into the store/runtime API

## Execution Sequence

### Phase 1: Tighten the public interfaces

Change:
- store protocols in [environment.py](/C:/Users/Q/code/propstore/propstore/core/environment.py)
- world protocols in [types.py](/C:/Users/Q/code/propstore/propstore/world/types.py)

End state:
- explanation and conflict interfaces are typed

### Phase 2: Convert `BoundWorld`

Change:
- `BoundWorld.conflicts()`
- `BoundWorld.explain()`
- `_recomputed_conflicts(...)`
- conflict caches and helper signatures

End state:
- no dict churn inside bound-world conflict/explanation flow

### Phase 3: Convert `HypotheticalWorld`

Change:
- overlay storage of stances/conflicts
- overlay store methods
- recomputed conflict integration

End state:
- overlay world matches the typed store/runtime surface

### Phase 4: Convert sidecar context load

Change:
- `_load_context_hierarchy()` in [model.py](/C:/Users/Q/code/propstore/propstore/world/model.py)

End state:
- contexts are typed as soon as they cross the SQLite boundary

### Phase 5: Sweep external callers

Change:
- CLI/report callers that still expect `dict`

End state:
- only explicit serialization/report edges call `to_dict()`

## Expected Fallout

The likely direct fallout is:
- tests that assert `conflict["claim_a_id"]` or `stance["claim_id"]`
- CLI code that prints explanation/conflict payloads
- worldline/report code that stores explanation/conflict results in YAML/JSON

That fallout is acceptable. The correct fix is:
- typed access in core/runtime code
- explicit projection at the final serialization edge

## Guardrail Tests

Minimum targeted test clusters:
- [test_world_model.py](/C:/Users/Q/code/propstore/tests/test_world_model.py)
- [test_contexts.py](/C:/Users/Q/code/propstore/tests/test_contexts.py)
- [test_atms_engine.py](/C:/Users/Q/code/propstore/tests/test_atms_engine.py)
- [test_worldline_error_visibility.py](/C:/Users/Q/code/propstore/tests/test_worldline_error_visibility.py)
- explanation/conflict-focused CLI or integration tests that fail during the slice

Required assertions:
- `BoundWorld.conflicts()` returns typed conflicts
- `BoundWorld.explain()` returns typed stances
- `HypotheticalWorld` preserves those typed surfaces
- context hierarchy behavior is unchanged after removing the dict detour

## Completion Criteria

This workstream is complete when all of the following are true:

- the store/world interfaces for explanations and conflicts are typed
- `BoundWorld` and `HypotheticalWorld` no longer keep stance/conflict dict payloads in their production path
- sidecar context hierarchy loading no longer constructs anonymous context payload dicts
- remaining dict projection for stance/conflict/context exists only at explicit serialization/report edges
- targeted tests pass

## Explicit Deferral

This workstream deliberately does not finish the worldline/revision result payload family.

That remains a separate follow-on slice:
- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- [worldline/runner.py](/C:/Users/Q/code/propstore/propstore/worldline/runner.py)
- [worldline/trace.py](/C:/Users/Q/code/propstore/propstore/worldline/trace.py)
- [revision/state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py)
- [revision/explain.py](/C:/Users/Q/code/propstore/propstore/revision/explain.py)

Reason:
- those are report/state payload structures rather than the immediate store/runtime semantic boundary
- the current highest-leverage rigor gain is to finish typing the remaining world/store plumbing first
