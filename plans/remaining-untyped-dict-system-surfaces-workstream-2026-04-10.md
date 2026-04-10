# Remaining Untyped Dict System Surfaces Workstream

Date: 2026-04-10

## Goal

Finish the remaining semantic uses of anonymous `dict` payloads in the live system code.

This is a convergence plan, not a fresh architecture. The repo already established the right pattern in the recent typing workstreams and commits:

- typed document objects at decode boundaries
- typed row/domain objects in the semantic pipeline
- `dict` only at explicit serialization, CLI, hashing, or external-API boundaries

## What Already Landed

These are no longer the main problem surfaces:

- typed document decode boundary (`document_schema.py`, document models)
- typed canonical/source-local document families
- typed runtime claims via `ActiveClaim`
- typed stance/conflict runtime surfaces in `BoundWorld` and store protocols
- typed worldline result and revision result wrappers

So the remaining work is not "replace every dict in the repo". It is narrower:

- remove the places where real semantic objects are still carried across functions or subsystems as anonymous maps
- stop rebuilding typed objects out of those maps later

## Scope Rules

Target these:

- claim-like semantic payloads that survive across multiple helpers/modules
- ATMS node payloads that are semantically structured but still `dict`
- revision atom payloads that are semantically structured but still `dict`
- merge/conflict detector claim payloads that are semantically structured but still `dict`
- worldline argumentation state still built as raw maps before being wrapped

Do not target these in this workstream:

- obvious index/cache/config maps
- dynamic key-value state where the map is the honest model (`bindings`, score maps, override maps)
- explicit `to_dict()` / `to_payload()` serialization edges
- CLI/search/report outputs that are intentionally loose boundary payloads

## Established Migration Pattern

Use the same strategy as the recent typing slices:

1. Add or reuse an honest typed object for the semantic surface.
2. Change the interface we control to use that type directly.
3. Update every caller.
4. Delete the old dict-shaped helper path.
5. Keep `to_dict()` only at the explicit edge that still needs wire-format output.

Rules:

- no compatibility shim that keeps dict and typed paths both first-class
- no widening to `Mapping[str, Any]` just to quiet types
- no "temporary" dual-path production interfaces left behind after the slice
- types first, then behavior, then deletion of the old path

## Current Remaining Leaks

### Cluster A: World Resolution Still Accepts Claim Mappings

Live evidence:

- `propstore/world/resolution.py:55`
- `propstore/world/resolution.py:67`
- `propstore/world/resolution.py:135`
- `propstore/world/resolution.py:180`
- `propstore/world/resolution.py:503`

Current problem:

- `_ResolutionClaimView` still exists mainly to normalize mixed typed-plus-dict inputs.
- Helpers still accept `ActiveClaim | Mapping[str, object]`.
- Resolution still reads claim data through `.get(...)` in multiple helper paths.

Required fix:

- make world resolution consume `ActiveClaim` only
- delete the `Mapping[str, object]` claim path
- keep any coercion at the single outer boundary, not across internal helpers
- remove `_claim_*` helpers whose only purpose is dict parsing

### Cluster B: ATMS Runtime Still Uses Anonymous Payload Dicts

Live evidence:

- `propstore/world/atms.py:148`
- `propstore/world/atms.py:214`
- `propstore/world/atms.py:226`
- `propstore/world/atms.py:237`
- `propstore/world/atms.py:374`
- `propstore/world/atms.py:1419`

Current problem:

- `ATMSNode.payload` is still `dict[str, Any]`.
- claim, derived, and assumption nodes are all inspected through `.payload.get(...)`.
- helper adapters still turn typed graph/runtime structures into row-shaped dicts and then back again.

Required fix:

- replace `ATMSNode.payload` with an explicit typed payload family
- use `ActiveClaim` directly for claim nodes or introduce a small `ATMSClaimPayload`
- introduce typed payloads for assumption and derived nodes instead of one catch-all dict
- delete `_parameterization_edge_to_row(...)` and `_conflict_witness_to_row(...)` as internal transport helpers

Preferred shape:

- `ATMSClaimPayload`
- `ATMSDerivedPayload`
- `ATMSAssumptionPayload`

### Cluster C: Hypothetical Overlay Still Mutates Row Dicts

Live evidence:

- `propstore/world/hypothetical.py:112`
- `propstore/world/hypothetical.py:168`
- `propstore/world/hypothetical.py:281`
- `propstore/world/hypothetical.py:503`

Current problem:

- `_ParameterizationCatalogAdapter.all_parameterizations()` still returns `list[dict[str, Any]]`.
- `_synthetic_row(...)` still rebuilds and mutates a row-shaped dict before reparsing to `ClaimRow`.
- `_synthetic_to_dict(...)` preserves that old dict transport surface.

Required fix:

- keep parameterization transport typed as row objects end to end
- add a typed synthetic-claim to `ClaimRow` constructor/helper
- stop mutating row dicts in overlay construction
- delete `_synthetic_to_dict(...)` unless an explicit serialization edge still needs it

### Cluster D: Revision Claim Atoms Still Carry Generic Payload Maps

Live evidence:

- `propstore/revision/state.py:38`
- `propstore/revision/af_adapter.py:126`
- `propstore/revision/operators.py:17`
- `propstore/revision/operators.py:57`
- `propstore/worldline/revision_capture.py:58`
- `propstore/worldline/revision_types.py:20`

Current problem:

- `BeliefAtom.payload` is still `Mapping[str, Any]`.
- revision operators still recover claim identity by scanning payload keys.
- revision argumentation projection still rebuilds active claims with `dict(atom.payload)`.
- the worldline revision bridge still drops to dict input for revision operations.

Required fix:

- replace `BeliefAtom.payload` with a typed atom-payload family
- at minimum split claim atoms from assumption atoms
- normalize revision inputs into typed atom payloads immediately
- update `af_adapter.py`, `operators.py`, and worldline revision capture to consume typed payloads directly

Preferred shape:

- `ClaimAtomPayload`
- `AssumptionAtomPayload`

## Cluster E: Worldline Argumentation Capture Still Manufactures Dict State

Live evidence:

- `propstore/worldline/argumentation.py:26`
- `propstore/worldline/argumentation.py:38`
- `propstore/worldline/argumentation.py:84`
- `propstore/worldline/argumentation.py:134`
- `propstore/worldline/argumentation.py:182`
- `propstore/worldline/argumentation.py:194`

Current problem:

- `capture_argumentation_state(...)` still returns `dict[str, Any] | None`.
- each backend helper still builds raw map payloads and only later relies on `WorldlineArgumentationState` elsewhere.

Required fix:

- make `capture_argumentation_state(...)` return `WorldlineArgumentationState | None`
- make each backend helper construct that typed object directly
- keep dict projection only in `to_dict()` on the typed state

This is likely a short slice because the typed wrapper already exists.

### Cluster F: Conflict Detector Internals Still Operate On Claim Dicts

Live evidence:

- `propstore/conflict_detector/collectors.py:16`
- `propstore/conflict_detector/algorithms.py:92`
- `propstore/conflict_detector/parameters.py:38`
- `propstore/conflict_detector/parameters.py:96`
- `propstore/conflict_detector/context.py:34`
- `propstore/conflict_detector/orchestrator.py:32`

Current problem:

- claim and concept semantic inputs are still plain dicts across collector/orchestrator/parameter-analysis helpers
- world/runtime code currently has to project typed claims back to source-claim dict payloads to reuse this subsystem

Required fix:

- define a typed conflict-detector claim surface and a typed concept-registry surface
- convert decode/bridge inputs once at the package boundary
- make collector/algorithm/parameter helpers operate on typed fields instead of `claim.get(...)`

Important note:

- this is a larger subsystem slice than Clusters A-E
- do it after the world/revision/worldline runtime cleanup unless an active slice needs it earlier

### Cluster G: Merge Semantics Still Use Raw Claim Dicts

Live evidence:

- `propstore/repo/structured_merge.py:23`
- `propstore/repo/structured_merge.py:27`
- `propstore/repo/structured_merge.py:34`
- `propstore/repo/structured_merge.py:239`
- `propstore/repo/merge_classifier.py:32`
- `propstore/repo/merge_classifier.py:48`
- `propstore/repo/merge_classifier.py:66`

Current problem:

- structured merge summaries still store active claims and stance payloads as raw dicts
- merge classifier still indexes, compares, and annotates claims as raw dicts
- these are semantic merge objects, not mere YAML decode leftovers

Required fix:

- introduce a typed merge-facing claim surface
- load branch claims into that typed surface once
- keep `StanceRow` as the typed stance boundary
- update summary hashing/comparison logic to project from typed claim objects instead of using raw dicts as the semantic representation

## Recommended Execution Order

### Phase 1: Finish core world runtime convergence

Targets:

- Cluster A
- Cluster B
- Cluster C

Why first:

- these are still on the main semantic runtime path
- they are the direct continuation of the existing active-claim and stance/conflict workstreams

### Phase 2: Finish revision and worldline runtime convergence

Targets:

- Cluster D
- Cluster E

Why second:

- the typed wrappers already exist in much of this surface
- the remaining leak is mostly the internal construction/control path

### Phase 3: Type the conflict detector package

Target:

- Cluster F

Why third:

- it is a larger subsystem
- it becomes easier once world/runtime callers have stopped carrying generic claim maps

### Phase 4: Type merge-semantic claim payloads

Target:

- Cluster G

Why fourth:

- important, but less central than the live world/revision/runtime path
- likely benefits from whatever typed claim/conflict-detector surfaces exist after Phases 1-3

## Acceptance Criteria

This workstream is done when all of the following are true:

- `propstore/world/resolution.py` no longer accepts claim `Mapping[str, object]`
- `ATMSNode.payload` is no longer `dict[str, Any]`
- `propstore/world/hypothetical.py` no longer rebuilds synthetic rows by mutating dict payloads
- `BeliefAtom.payload` is no longer a generic `Mapping[str, Any]`
- `capture_argumentation_state(...)` no longer returns raw dict state
- conflict detector semantic helpers no longer traffic in raw claim dicts internally
- merge-semantic claim objects are no longer stored and compared as raw dicts

Allowed remaining dicts:

- decode/encode boundaries
- explicit `to_dict()` or `to_payload()` projections
- honest map-shaped data such as bindings, score tables, and keyed metadata

## Immediate Next Slice

Start with Cluster A in `propstore/world/resolution.py`.

Reason:

- it is the smallest high-value remaining semantic dict leak on the core runtime path
- it removes the mixed typed-plus-dict contract that still contaminates downstream code
- it sets up the ATMS and hypothetical cleanup to stay fully typed instead of reintroducing mixed helper signatures
