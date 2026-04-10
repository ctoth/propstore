# Generic Payload Slot Removal Workstream

Date: 2026-04-10

## Goal

Remove the remaining generic semantic `payload` slots from core runtime objects we control and replace them with explicit domain variants.

This is not another dict-typing pass. The dict-typing workstream already converged the obvious anonymous-map leaks into typed objects. The remaining problem is representational shape:

- `BeliefAtom(kind, payload, ...)`
- `ATMSNode(kind, payload, ...)`
- similar wrappers where the real semantic object is still hidden behind a generic inner slot

That shape is still too transport-like for the core semantic pipeline.

Target outcome:

- no generic payload slots on revision atoms or ATMS nodes
- subtype-specific fields live on subtype-specific dataclasses
- callers stop doing `kind` + payload extraction as the normal access pattern
- serialization stays explicit at the boundary only

## Why This Workstream Exists

The recent typing work established honest objects such as:

- `ClaimAtomPayload`
- `AssumptionAtomPayload`
- `ATMSClaimPayload`
- `ATMSAssumptionPayload`
- `ATMSDerivedPayload`

That was the right convergence step, but it preserved the wrong outer shape:

- one wrapper type
- one generic `payload` field
- stringly `kind` dispatch

That is better than raw `dict`, but still weaker than the architecture we actually want.

In this codebase, the right default is:

1. make the semantic variants explicit
2. update every caller
3. delete the generic-slot representation

## Design Rule

When we control both sides of the interface, do not keep:

- `kind: str`
- `payload: ...`

as the primary semantic representation.

Prefer one of these:

### Option A: Sum type of explicit variants

- `BeliefAtom = ClaimAtom | AssumptionAtom`
- `ATMSNode = ATMSClaimNode | ATMSAssumptionNode | ATMSDerivedNode`

### Option B: Shared abstract protocol plus explicit variants

Use only if many callers genuinely operate on shared fields without needing subtype data.

Do not keep a generic wrapper merely to avoid touching callers.

## Scope

This workstream targets:

- revision atom runtime objects in [state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py)
- ATMS node runtime objects in [atms.py](/C:/Users/Q/code/propstore/propstore/world/atms.py)
- direct callers of those objects
- CLI/render/debug helpers that still assume wrapper-plus-payload structure

This workstream does not target:

- boundary `to_dict()` / `to_payload()` projections
- honest map-shaped data such as bindings, score maps, or metadata bags
- document/YAML decode models
- the conflict detector and merge wrappers unless they still expose a generic payload slot after this redesign

## Current Smells

### Revision

Current shape in [state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py):

- `BeliefAtom.atom_id`
- `BeliefAtom.kind`
- `BeliefAtom.payload`
- helpers like `claim_atom_payload(atom)` and `assumption_atom_payload(atom)`

Why this is still wrong:

- the real semantic distinction is in the type, not a string field
- callers must branch on `kind` or call extraction helpers
- invalid states are still representable in one wrapper type

### ATMS

Current shape in [atms.py](/C:/Users/Q/code/propstore/propstore/world/atms.py):

- `ATMSNode.node_id`
- `ATMSNode.kind`
- `ATMSNode.payload`
- helper family such as `_node_claim_payload`, `_node_assumption_payload`, `_node_derived_payload`

Why this is still wrong:

- the helper family exists mostly to recover subtype identity we already know
- `kind` and `payload` are doing the work the type system should do
- ATMS nodes are core runtime entities, not transport envelopes

## Target Architecture

## Family A: Revision atom variants

Replace the current wrapper with explicit dataclasses in [state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py).

Preferred shape:

- `ClaimAtom`
- `AssumptionAtom`

Shared protocol or base class only if needed:

- `RevisionAtomLike`

Suggested fields:

### `ClaimAtom`

- `atom_id: str`
- `claim: ActiveClaim`
- `label: Label | None = None`

Convenience properties:

- `claim_id`
- `concept_id`

### `AssumptionAtom`

- `atom_id: str`
- `assumption: AssumptionRef`
- `label: Label | None = None`

Then define:

- `BeliefAtom = ClaimAtom | AssumptionAtom`

Delete:

- `BeliefAtom.kind`
- `BeliefAtom.payload`
- `ClaimAtomPayload`
- `AssumptionAtomPayload`
- `claim_atom_payload(...)`
- `assumption_atom_payload(...)`

Reason:

- these payload dataclasses only exist because the outer wrapper is generic

## Family B: ATMS node variants

Replace the current wrapper with explicit dataclasses in [atms.py](/C:/Users/Q/code/propstore/propstore/world/atms.py).

Preferred shape:

- `ATMSClaimNode`
- `ATMSAssumptionNode`
- `ATMSDerivedNode`

Suggested fields:

### `ATMSClaimNode`

- `node_id: str`
- `claim: ActiveClaim`
- `label: Label = field(default_factory=Label)`
- `justification_ids: tuple[str, ...] = ()`

### `ATMSAssumptionNode`

- `node_id: str`
- `assumption: AssumptionRef`
- `label: Label = field(default_factory=Label)`
- `justification_ids: tuple[str, ...] = ()`

### `ATMSDerivedNode`

- `node_id: str`
- `concept_id: str`
- `value: float | str`
- `parameterization_index: int`
- `formula: str | None = None`
- `label: Label = field(default_factory=Label)`
- `justification_ids: tuple[str, ...] = ()`

Then define:

- `ATMSNode = ATMSClaimNode | ATMSAssumptionNode | ATMSDerivedNode`

Delete:

- `ATMSNode.kind`
- `ATMSNode.payload`
- `ATMSClaimPayload`
- `ATMSAssumptionPayload`
- `ATMSDerivedPayload`
- `_node_*payload(...)` helper family

## Representation Rules

- subtype identity comes from the type, not a `kind` string
- subtype fields are direct attributes, not hidden inside `.payload`
- serialization helpers may still emit a tagged dict at the boundary if needed
- runtime code should not reconstruct a fake wrapper for convenience

## Migration Strategy

This repo should use direct replacement, not dual-path compatibility.

For each subsystem:

1. introduce the explicit variants
2. update constructor sites
3. update all readers and pattern-matching logic
4. delete the generic wrapper path
5. fix tests and CLI callers

Rules:

- no keeping both `BeliefAtom(kind, payload)` and `ClaimAtom | AssumptionAtom` alive in production
- no aliases that let callers keep using `.payload`
- no helper that recreates generic wrappers from explicit variants just to preserve old code

## Work Clusters

### Cluster A: Revision atom redesign

Primary files:

- [state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py)
- [projection.py](/C:/Users/Q/code/propstore/propstore/revision/projection.py)
- [operators.py](/C:/Users/Q/code/propstore/propstore/revision/operators.py)
- [af_adapter.py](/C:/Users/Q/code/propstore/propstore/revision/af_adapter.py)
- [snapshot_types.py](/C:/Users/Q/code/propstore/propstore/revision/snapshot_types.py)
- [revision_types.py](/C:/Users/Q/code/propstore/propstore/worldline/revision_types.py)
- [revision_capture.py](/C:/Users/Q/code/propstore/propstore/worldline/revision_capture.py)
- [compiler_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/compiler_cmds.py)

Required end state:

- explicit `ClaimAtom` / `AssumptionAtom`
- `BeliefBase.atoms` stores the explicit union
- normalization and snapshot code stop routing through payload dataclasses

### Cluster B: Revision caller cleanup

Primary files:

- revision tests
- worldline revision tests
- CLI tests

Required end state:

- no caller reads `.payload`
- no caller branches on `.kind`
- tests assert on real fields

### Cluster C: ATMS node redesign

Primary files:

- [atms.py](/C:/Users/Q/code/propstore/propstore/world/atms.py)

Required end state:

- explicit ATMS node variants
- justification/explanation/status logic uses direct field access
- claim, assumption, and derived nodes are no longer “same object plus hidden payload”

### Cluster D: ATMS caller cleanup

Primary files:

- [hypothetical.py](/C:/Users/Q/code/propstore/propstore/world/hypothetical.py) if it touches node construction
- world/ATMS tests
- worldline capture code if it inspects ATMS nodes

Required end state:

- no `.payload`
- no `.kind` dispatch except perhaps at an explicit serialization boundary

### Cluster E: Final deletion sweep

Primary files:

- any helpers left behind

Delete:

- payload dataclasses that only existed for the generic-wrapper representation
- extraction helpers whose only job is downcasting from the wrapper
- tests whose only purpose is preserving wrapper behavior

## Suggested Execution Order

1. Revision atom variants
2. Revision caller cleanup
3. ATMS node variants
4. ATMS caller cleanup
5. deletion sweep
6. full suite

Why this order:

- revision is smaller and more self-contained
- ATMS has more runtime surface area and more helper fallout
- finishing revision first establishes the exact pattern to repeat in ATMS

## Test Strategy

After the revision slice:

- `uv run pytest -vv tests/test_revision_state.py tests/test_revision_projection.py tests/test_revision_operators.py tests/test_revision_phase1.py tests/test_revision_phase1_cli.py tests/test_worldline_revision.py`

After the ATMS slice:

- `uv run pytest -vv tests/test_atms_engine.py tests/test_world_model.py tests/test_worldline.py`

Final:

- `uv run pytest -vv`

Every run should tee to `logs/test-runs/`.

## Acceptance Criteria

This workstream is complete when all of the following are true:

- [state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py) no longer defines a generic `BeliefAtom` wrapper with `kind` and `payload`
- revision callers no longer use `.payload` or `claim_atom_payload(...)` / `assumption_atom_payload(...)`
- [atms.py](/C:/Users/Q/code/propstore/propstore/world/atms.py) no longer defines a generic `ATMSNode` wrapper with `kind` and `payload`
- ATMS callers no longer use `_node_*payload(...)` helpers
- subtype-specific data is accessed through explicit fields on explicit variants
- any remaining dict output on these surfaces exists only in explicit serialization functions

## Non-goals

- do not redesign unrelated map-shaped state
- do not broaden this into a general “remove all unions” campaign
- do not invent a plugin-style visitor framework unless the ordinary dataclass union becomes unmanageable

## Immediate First Slice

Start with revision atoms in [state.py](/C:/Users/Q/code/propstore/propstore/revision/state.py).

Reason:

- it is the smallest remaining generic-slot family
- its callers are already relatively well isolated
- it gives a clear pattern for the ATMS redesign afterward
