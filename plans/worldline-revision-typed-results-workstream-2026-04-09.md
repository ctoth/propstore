# Worldline And Revision Typed Results Workstream

Date: 2026-04-09

## Goal

Replace the remaining semantic result/state `dict` flow in the worldline and revision subsystems with explicit typed objects.

This is the next major cleanup after:
- canonical concept typing
- sidecar row typing
- active runtime claim typing
- stance/conflict/context runtime typing

The remaining problem is not SQLite rows and not active runtime claims. The remaining problem is that worldline materialization and revision state still use nested anonymous payload maps to represent real domain state:

- worldline target values
- worldline trace steps
- worldline dependencies
- worldline revision queries
- revision explanations
- entrenchment reasons
- iterated epistemic state payloads

Those are not harmless wire dictionaries. They are semantic program objects that get built, merged, hashed, serialized, reparsed, and tested against shape conventions.

Target outcome:
- worldline result internals are typed dataclasses
- revision explanation and entrenchment internals are typed dataclasses
- iterated epistemic state serialization is projected from typed objects, not `asdict()` of map-bearing dataclasses
- hashing works over typed result/state objects
- YAML/JSON boundaries remain the only place where `dict` is the primary representation

## Explicit Execution Style

This workstream should be executed in many commits, with aggressive cleanup at each step.

Rules for execution:
- no `cast(...)`
- no widening types to `Mapping[str, Any]` to silence type errors
- no “compatibility helper” that keeps dict and typed result/state objects equally first-class
- no leaving half of the subsystem on dict payloads while the other half is typed unless that is strictly inside the current commit boundary and removed before the end of the workstream
- if an interface changes and we control both sides, change the interface and update every caller

This is a cleanup-heavy workstream. The point is not to preserve the old shape. The point is to remove it.

## Why This Is The Next Slice

The core runtime/store path is now mostly typed. The remaining big dict families are concentrated here:

- [definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- [runner.py](/C:/Users/Q/code/propstore/propstore/worldline/runner.py)
- [trace.py](/C:/Users/Q/code/propstore/propstore/worldline/trace.py)
- [hashing.py](/C:/Users/Q/code/propstore/propstore/worldline/hashing.py)
- [revision/state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py)
- [revision/explain.py](/C:/Users/Q/code/propstore/propstore/revision/explain.py)
- [revision/entrenchment.py](/C:/Users/Q/code/propstore/propstore/revision/entrenchment.py)
- [revision/iterated.py](/C:/Users/Q/code/propstore/propstore/revision/iterated.py)
- [worldline/revision_capture.py](/C:/Users/Q/code/propstore/propstore/worldline/revision_capture.py)

These modules are still doing exactly the kind of thing we have been removing elsewhere:
- building nested dict payloads in memory
- passing them through multiple layers
- indexing them by string keys instead of field access
- serializing them to hashable output without a typed semantic surface

## Non-goals

- Do not redesign claim/concept/store typing again.
- Do not redesign worldline YAML schema more than necessary to replace internal dict semantics with typed objects.
- Do not redesign the full argumentation payload family in this slice unless it is needed to keep the worldline result coherent.
- Do not collapse all revision atom payloads into one mega-dataclass if multiple typed value objects are more honest.

## Existing Typed Surfaces To Reuse

- `Environment` and `RenderPolicy` in [world/types.py](/C:/Users/Q/code/propstore/propstore/world/types.py)
- `ActiveClaim`, `ValueResult`, `DerivedResult`, `ResolvedResult` in [active_claims.py](/C:/Users/Q/code/propstore/propstore/core/active_claims.py) and [types.py](/C:/Users/Q/code/propstore/propstore/world/types.py)
- `ClaimId`, `ConceptId`, `ContextId`, `AssumptionId` in [id_types.py](/C:/Users/Q/code/propstore/propstore/core/id_types.py)
- `Label` and `AssumptionRef` in [labels.py](/C:/Users/Q/code/propstore/propstore/core/labels.py)
- `BeliefBase`, `BeliefAtom`, `RevisionResult`, `RevisionEpisode`, `EpistemicState`, `EntrenchmentReport` in [revision/state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py) and [revision/entrenchment.py](/C:/Users/Q/code/propstore/propstore/revision/entrenchment.py)

These should be reused where their shape is already honest.

Do not reuse as the long-term semantic surface:
- `dict[str, dict[str, Any]]`
- `list[dict[str, Any]]`
- `Mapping[str, Mapping[str, Any]]`
- `asdict(state)` in [iterated.py](/C:/Users/Q/code/propstore/propstore/revision/iterated.py) as the primary serialization model

## Main Leaks To Eliminate

### Leak 1: Worldline results are nested dict payloads

Current shape in [definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py):
- `WorldlineResult.values: dict[str, dict[str, Any]]`
- `WorldlineResult.steps: list[dict[str, Any]]`
- `WorldlineResult.dependencies: dict[str, list[str]]`
- `WorldlineRevisionQuery.atom: dict[str, Any] | None`

This means the materialized worldline state has no typed semantic surface at all.

### Leak 2: Worldline runner manufactures dict payloads directly

Current shape in [runner.py](/C:/Users/Q/code/propstore/propstore/worldline/runner.py):
- `values[target_name] = {...}`
- `argumentation_state: dict[str, Any] | None`
- `revision_state: dict[str, Any] | None`
- `dependencies = {"claims": ..., "stances": ..., "contexts": ...}`

That is domain state being built as maps rather than projected to maps.

### Leak 3: Resolution trace is an untyped list of dicts

Current shape in [trace.py](/C:/Users/Q/code/propstore/propstore/worldline/trace.py):
- `self.steps: list[dict[str, Any]]`
- `record_step(**payload: Any)`

This is exactly the kind of “open bag of fields” that makes later cleanup harder.

### Leak 4: Worldline hashing hashes dict payloads instead of typed result state

Current shape in [hashing.py](/C:/Users/Q/code/propstore/propstore/worldline/hashing.py):
- hash input is `values`, `steps`, `dependencies`, `sensitivity`, `argumentation`, `revision` as nested dict/list payloads

The content hash should be computed from typed result/state projections, not from ad hoc dicts assembled in the runner.

### Leak 5: Revision explanations and entrenchment reasons are nested maps

Current shape:
- [state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py): `RevisionResult.explanation`, `RevisionEpisode.explanation`, `EpistemicState.entrenchment_reasons`
- [entrenchment.py](/C:/Users/Q/code/propstore/propstore/revision/entrenchment.py): `reasons: Mapping[str, dict[str, Any]]`
- [explain.py](/C:/Users/Q/code/propstore/propstore/revision/explain.py): `atoms: dict[str, dict[str, Any]]`

These are semantic explanation objects masquerading as maps.

### Leak 6: Iterated revision payload is driven by `asdict()` over map-bearing state

Current shape in [iterated.py](/C:/Users/Q/code/propstore/propstore/revision/iterated.py):
- `payload = asdict(state)`
- then manual patch-up of list/tuple fields

That is a warning sign. It means the state model is not serialization-shaped in a principled way.

### Leak 7: Revision capture still returns loose dict payloads

Current shape in [revision_capture.py](/C:/Users/Q/code/propstore/propstore/worldline/revision_capture.py):
- `capture_revision_state(...) -> dict[str, Any]`
- `_revision_result_payload(...) -> dict[str, Any]`
- `_query_atom_id(atom: dict[str, Any] | None)`

This is the bridge between revision semantics and worldline results, and it is still entirely dict-shaped.

## Proposed Type Families

The types below are the minimum honest surface. This is not “nice to have”; this is what the program is already pretending exists.

## Family A: Worldline value/result objects

Add a module like:
- [worldline/result_types.py](/C:/Users/Q/code/propstore/propstore/worldline/result_types.py)

Define:

### `WorldlineTargetValue`

Represents one target in a materialized worldline result.

Fields:
- `status: str`
- `value: float | str | None = None`
- `source: str | None = None`
- `reason: str | None = None`
- `claim_id: str | None = None`
- `winning_claim_id: str | None = None`
- `claim_type: str | None = None`
- `statement: str | None = None`
- `expression: str | None = None`
- `body: str | None = None`
- `name: str | None = None`
- `canonical_ast: str | None = None`
- `variables: tuple[WorldlineVariableRef, ...] | str | None = None`
- `formula: str | None = None`
- `strategy: str | None = None`
- `inputs_used: Mapping[str, WorldlineInputSource] | None = None`

Required behavior:
- typed constructor from mapping
- `to_dict()` for serialization only

### `WorldlineInputSource`

Represents an input used to derive or explain a worldline target.

Fields:
- `source: str`
- `value: float | str | None = None`
- `claim_id: str | None = None`
- `formula: str | None = None`

### `WorldlineVariableRef`

If worldline target values continue to expose variable payloads, do not keep them as bare `dict`.

Fields:
- `name: str | None`
- `symbol: str | None`
- `concept_id: str | None`

### `WorldlineDependencies`

Replace `dict[str, list[str]]`.

Fields:
- `claims: tuple[str, ...] = ()`
- `stances: tuple[str, ...] = ()`
- `contexts: tuple[str, ...] = ()`

Required behavior:
- deterministic serialization order
- `from_dict()` / `to_dict()`

### `WorldlineResult`

Keep the existing top-level class name in [definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py), but change its fields:

- `values: Mapping[str, WorldlineTargetValue]`
- `steps: tuple[WorldlineStep, ...]`
- `dependencies: WorldlineDependencies`
- `sensitivity: WorldlineSensitivityReport | None`
- `argumentation: WorldlineArgumentationState | None`
- `revision: WorldlineRevisionState | None`

The exact names of the nested argumentation/revision types can vary, but the structure must be typed.

## Family B: Worldline trace objects

Define in:
- [worldline/result_types.py](/C:/Users/Q/code/propstore/propstore/worldline/result_types.py)
- or [worldline/trace_types.py](/C:/Users/Q/code/propstore/propstore/worldline/trace_types.py)

### `WorldlineStep`

Represents one provenance step.

Fields:
- `concept: str`
- `source: str`
- `value: float | str | None = None`
- `claim_id: str | None = None`
- `strategy: str | None = None`
- `reason: str | None = None`
- `formula: str | None = None`

Notes:
- This may feel “sparse”, but that sparsity is still far more honest than `dict[str, Any]`.
- If later steps need additional structured variants, split by step kind instead of widening back to `dict`.

`ResolutionTrace` should then store:
- `steps: list[WorldlineStep]`

And `record_step` should stop taking arbitrary `**payload`.

## Family C: Revision query and capture objects

Add a module like:
- [worldline/revision_types.py](/C:/Users/Q/code/propstore/propstore/worldline/revision_types.py)

### `RevisionAtomRef`

Replace `WorldlineRevisionQuery.atom: dict[str, Any] | None`.

Fields:
- `kind: str`
- `atom_id: str | None = None`
- `claim_id: str | None = None`
- `assumption_id: str | None = None`

Purpose:
- this is the query-facing reference to a revision atom, not the full atom payload

### `RevisionConflictSelection`

Replace `dict[str, list[str]]` conflict target maps where appropriate.

Fields:
- `targets_by_atom_id: Mapping[str, tuple[str, ...]]`

### `WorldlineRevisionQuery`

Keep the class name, but change fields to:
- `operation: str`
- `atom: RevisionAtomRef | None`
- `target: str | None`
- `conflicts: RevisionConflictSelection`
- `operator: str | None`

### `WorldlineRevisionResult`

Represents the per-operation result payload currently built in [revision_capture.py](/C:/Users/Q/code/propstore/propstore/worldline/revision_capture.py).

Fields:
- `accepted_atom_ids: tuple[str, ...]`
- `rejected_atom_ids: tuple[str, ...]`
- `incision_set: tuple[str, ...]`
- `explanation: RevisionExplanation`

### `WorldlineRevisionState`

Represents the full revision section currently emitted into a worldline result.

Fields:
- `operation: str`
- `input_atom_id: str | None`
- `target_atom_ids: tuple[str, ...]`
- `result: WorldlineRevisionResult`
- `state: EpistemicStateSnapshot | None = None`
- `status: str | None = None`
- `error: str | None = None`

This type should also be the error-capture target instead of raw dicts assembled in exception handlers.

## Family D: Revision explanation and entrenchment objects

Add a module like:
- [revision/explanation_types.py](/C:/Users/Q/code/propstore/propstore/revision/explanation_types.py)

### `RevisionAtomDetail`

Replace `Mapping[str, Mapping[str, Any]]` in `RevisionResult.explanation`.

Fields:
- `reason: str | None = None`
- `incision_set: tuple[str, ...] = ()`
- `support_sets: tuple[tuple[str, ...], ...] = ()`
- `raw: Mapping[str, object] = field(default_factory=dict)` only if truly needed

Preferred default:
- do not add `raw` unless there is a real unsupported field family

### `RevisionAtomExplanation`

Replace the nested atom payload produced by [explain.py](/C:/Users/Q/code/propstore/propstore/revision/explain.py).

Fields:
- `status: str`
- `reason: str`
- `ranking: EntrenchmentReason | None = None`
- `incision_set: tuple[str, ...] = ()`
- `support_sets: tuple[tuple[str, ...], ...] = ()`

### `RevisionExplanation`

Replace the top-level dict returned by `build_revision_explanation`.

Fields:
- `accepted_atom_ids: tuple[str, ...]`
- `rejected_atom_ids: tuple[str, ...]`
- `incision_set: tuple[str, ...]`
- `atoms: Mapping[str, RevisionAtomExplanation]`

### `EntrenchmentReason`

Replace `dict[str, Any]` entries in `EntrenchmentReport.reasons` and `EpistemicState.entrenchment_reasons`.

Fields:
- `override_priority: int | None = None`
- `override_key: str | None = None`
- `support_count: int | None = None`
- `essential_support: tuple[AssumptionId, ...] = ()`
- `iterated_operator: str | None = None`
- `revised_in: bool | None = None`

This object should absorb what [entrenchment.py](/C:/Users/Q/code/propstore/propstore/revision/entrenchment.py) and [iterated.py](/C:/Users/Q/code/propstore/propstore/revision/iterated.py) currently treat as open dictionaries.

## Family E: Epistemic state snapshot objects

The current in-memory `EpistemicState` can stay, but its nested explanation/reason fields need to become typed.

Also add a serialization-facing snapshot type if needed:
- `EpistemicStateSnapshot`
- `RevisionEpisodeSnapshot`

These should be explicit serialization targets for worldline capture instead of the current `asdict(...)` approach.

## Architectural Invariants

- Typed objects are the primary in-memory representation.
- YAML/JSON dicts are boundary representations only.
- No `cast`.
- No “just use `Mapping[str, Any]` here” escape hatch.
- No generic `payload: dict[str, Any]` field unless the field represents true arbitrary user data we do not control.
- If a result object must serialize to the old shape, add `to_dict()` on the typed class; do not keep the old dict as the real state.
- If a parser must accept existing YAML shape, parse immediately into typed objects and reject malformed data hard.

## File Clusters

### Cluster A: Worldline result model

Primary files:
- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- new [worldline/result_types.py](/C:/Users/Q/code/propstore/propstore/worldline/result_types.py)

Work:
- replace nested result dict/list fields with typed dataclasses
- rewrite `from_dict()` / `to_dict()` to parse/project typed objects
- replace `WorldlineRevisionQuery.atom` and `conflicts` with typed query objects

Delete:
- dict-shaped internal fields in `WorldlineResult`
- dict-shaped `atom` field in `WorldlineRevisionQuery`

### Cluster B: Worldline trace and hashing

Primary files:
- [worldline/trace.py](/C:/Users/Q/code/propstore/propstore/worldline/trace.py)
- [worldline/hashing.py](/C:/Users/Q/code/propstore/propstore/worldline/hashing.py)
- [worldline/runner.py](/C:/Users/Q/code/propstore/propstore/worldline/runner.py)

Work:
- add typed `WorldlineStep`
- make `ResolutionTrace.steps` typed
- replace `record_step(**payload)` with explicit constructors or explicit named parameters
- make hashing consume typed result objects or typed projections from them

Important:
- do not silently widen `WorldlineStep` into a “bag of fields”
- if multiple step kinds are needed, split them

### Cluster C: Worldline resolution result assembly

Primary files:
- [worldline/resolution.py](/C:/Users/Q/code/propstore/propstore/worldline/resolution.py)
- [worldline/runner.py](/C:/Users/Q/code/propstore/propstore/worldline/runner.py)

Work:
- make `resolve_target(...)` return `WorldlineTargetValue`
- make `_trace_derived_inputs(...)` and related helpers return typed input-source objects
- stop building dict payloads for missing/derived/resolved/claim-backed targets
- make `_capture_sensitivity(...)` return typed sensitivity objects

### Cluster D: Revision explanation and entrenchment

Primary files:
- [revision/state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py)
- [revision/explain.py](/C:/Users/Q/code/propstore/propstore/revision/explain.py)
- [revision/entrenchment.py](/C:/Users/Q/code/propstore/propstore/revision/entrenchment.py)
- [revision/iterated.py](/C:/Users/Q/code/propstore/propstore/revision/iterated.py)

Work:
- replace map-shaped explanation and reason fields with typed objects
- rewrite `build_revision_explanation(...)` to produce `RevisionExplanation`, not `dict`
- rewrite entrenchment computation to produce `EntrenchmentReason`
- remove `asdict(state)` from `epistemic_state_payload`
- replace it with explicit projection from typed state/snapshot objects

Delete:
- `Mapping[str, Mapping[str, Any]]` explanation surfaces
- `dict[str, dict[str, Any]]` entrenchment reasons

### Cluster E: Revision capture bridge

Primary files:
- [worldline/revision_capture.py](/C:/Users/Q/code/propstore/propstore/worldline/revision_capture.py)
- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- [world/bound.py](/C:/Users/Q/code/propstore/propstore/world/bound.py)

Work:
- `capture_revision_state(...)` should return `WorldlineRevisionState`
- `_revision_result_payload(...)` becomes typed result conversion
- `_query_atom_id(...)` should consume `RevisionAtomRef`, not dict
- `BoundWorld` revision APIs should return typed explanation/state objects internally and project only where required

### Cluster F: Argumentation and sensitivity payload cleanup

Primary files:
- [worldline/argumentation.py](/C:/Users/Q/code/propstore/propstore/worldline/argumentation.py)
- [worldline/runner.py](/C:/Users/Q/code/propstore/propstore/worldline/runner.py)

Work:
- type the argumentation and sensitivity sections that still flow as nested dicts
- if a fully typed argumentation-state family is too large for the same early commit, introduce it as its own sub-family inside this workstream

Preferred direction:
- `WorldlineArgumentationState`
- `WorldlineSensitivityReport`

Do not leave these as raw dicts if the worldline result has otherwise become typed.

## Execution Sequence

This workstream should land in many commits. A reasonable sequence is:

### Commit 1: Add typed worldline result/value/step/dependency classes

Files:
- new result-types module
- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)

End state:
- `WorldlineResult` fields are typed internally
- parsing/serialization still round-trips existing on-disk shape

### Commit 2: Replace trace dicts with typed steps

Files:
- [worldline/trace.py](/C:/Users/Q/code/propstore/propstore/worldline/trace.py)
- [worldline/hashing.py](/C:/Users/Q/code/propstore/propstore/worldline/hashing.py)

End state:
- no `list[dict[str, Any]]` trace steps

### Commit 3: Convert worldline resolution helpers to typed target values

Files:
- [worldline/resolution.py](/C:/Users/Q/code/propstore/propstore/worldline/resolution.py)
- [worldline/runner.py](/C:/Users/Q/code/propstore/propstore/worldline/runner.py)

End state:
- `resolve_target(...)` returns typed target values
- `run_worldline(...)` stops building nested dicts directly

### Commit 4: Type revision explanation detail and entrenchment reasons

Files:
- [revision/state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py)
- [revision/entrenchment.py](/C:/Users/Q/code/propstore/propstore/revision/entrenchment.py)
- new revision explanation-types module

End state:
- `RevisionResult.explanation` and `EntrenchmentReport.reasons` are typed

### Commit 5: Rewrite revision explanation builder

Files:
- [revision/explain.py](/C:/Users/Q/code/propstore/propstore/revision/explain.py)
- [world/bound.py](/C:/Users/Q/code/propstore/propstore/world/bound.py)

End state:
- `build_revision_explanation(...)` returns `RevisionExplanation`

### Commit 6: Remove `asdict()` payload serialization from iterated revision

Files:
- [revision/iterated.py](/C:/Users/Q/code/propstore/propstore/revision/iterated.py)

End state:
- explicit snapshot projection instead of dict-generation by structural recursion

### Commit 7: Type revision capture and worldline revision query/state

Files:
- [worldline/revision_capture.py](/C:/Users/Q/code/propstore/propstore/worldline/revision_capture.py)
- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)

End state:
- `WorldlineRevisionQuery` and captured revision state are typed

### Commit 8: Type sensitivity and argumentation result sections

Files:
- [worldline/argumentation.py](/C:/Users/Q/code/propstore/propstore/worldline/argumentation.py)
- [worldline/runner.py](/C:/Users/Q/code/propstore/propstore/worldline/runner.py)
- new result-types submodules as needed

End state:
- no raw dict sections left inside `WorldlineResult`

### Commit 9: Caller/test sweep

Files:
- worldline tests
- revision tests
- CLI/report callers that serialize these objects

End state:
- dict projection remains only at explicit serialization edges

## Likely Caller Fallout

The likely direct fallout is in:
- [tests/test_worldline.py](/C:/Users/Q/code/propstore/tests/test_worldline.py)
- [tests/test_worldline_revision.py](/C:/Users/Q/code/propstore/tests/test_worldline_revision.py)
- [tests/test_revision_explain.py](/C:/Users/Q/code/propstore/tests/test_revision_explain.py)
- [tests/test_revision_iterated.py](/C:/Users/Q/code/propstore/tests/test_revision_iterated.py)
- [tests/test_revision_bound_world.py](/C:/Users/Q/code/propstore/tests/test_revision_bound_world.py)
- [tests/test_worldline_error_visibility.py](/C:/Users/Q/code/propstore/tests/test_worldline_error_visibility.py)

And probably:
- code that compares `WorldlineResult.to_dict()` output directly
- code that hashes worldline payloads by assuming raw dict/list shape
- code that mutates revision explanation maps directly in tests

The correct fix is not to keep dicts around longer. The correct fix is:
- typed access internally
- explicit `to_dict()` only at final compare/serialize boundaries

## Verification Strategy

Targeted suites should be run after each substantial cluster:

Worldline:
- [test_worldline.py](/C:/Users/Q/code/propstore/tests/test_worldline.py)
- [test_worldline_revision.py](/C:/Users/Q/code/propstore/tests/test_worldline_revision.py)
- [test_worldline_error_visibility.py](/C:/Users/Q/code/propstore/tests/test_worldline_error_visibility.py)

Revision:
- [test_revision_explain.py](/C:/Users/Q/code/propstore/tests/test_revision_explain.py)
- [test_revision_iterated.py](/C:/Users/Q/code/propstore/tests/test_revision_iterated.py)
- [test_revision_bound_world.py](/C:/Users/Q/code/propstore/tests/test_revision_bound_world.py)
- [test_revision_phase1.py](/C:/Users/Q/code/propstore/tests/test_revision_phase1.py)

Adjacent safety checks:
- [test_atms_engine.py](/C:/Users/Q/code/propstore/tests/test_atms_engine.py)
- [test_praf_integration.py](/C:/Users/Q/code/propstore/tests/test_praf_integration.py)
- [test_review_regressions.py](/C:/Users/Q/code/propstore/tests/test_review_regressions.py)

Every run should use:
- `uv run pytest -vv ...`
- full output tee’d to `logs/test-runs/`

## Completion Criteria

This workstream is complete when all of the following are true:

- `WorldlineResult` no longer stores nested dict/list payloads as its primary internal representation
- `ResolutionTrace` no longer stores `list[dict[str, Any]]`
- worldline hashing operates over typed result state or explicit typed projections
- `WorldlineRevisionQuery` no longer uses raw `atom: dict[str, Any]`
- `RevisionResult.explanation`, `RevisionEpisode.explanation`, and `EpistemicState.entrenchment_reasons` are typed
- `EntrenchmentReport.reasons` is typed
- `build_revision_explanation(...)` returns a typed explanation object
- `epistemic_state_payload(...)` no longer relies on `asdict()` over map-bearing state
- `capture_revision_state(...)` returns a typed revision-state object
- any remaining `dict` use in these subsystems is strictly at YAML/JSON serialization boundaries

## Explicit Deferrals

This workstream does not include:
- source registry/proposal dict cleanup
- repository merge payload cleanup
- artifact code report cleanup
- compiler context/CEL registry dict cleanup

Those are still real, but they are separate families.

If you want the next family after this one, it is probably:
- compiler/CEL concept registry dicts in [compiler/context.py](/C:/Users/Q/code/propstore/propstore/compiler/context.py) and [cel_checker.py](/C:/Users/Q/code/propstore/propstore/cel_checker.py)

But this workstream should stand on its own first.
