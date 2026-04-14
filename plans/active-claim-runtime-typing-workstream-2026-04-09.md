# Active Claim Runtime Typing Workstream

## Goal

Replace the remaining runtime claim `dict` flow with explicit typed runtime claim objects across the world, hypothetical, ATMS, revision, and worldline layers.

This workstream is the next important slice after typed sidecar claim rows and typed nested claim source/provenance values.

The problem is no longer the storage boundary. The problem is the runtime boundary:

- [bound.py](/C:/Users/Q/code/propstore/propstore/world/bound.py) still turns `ClaimRow` into `dict` immediately.
- [hypothetical.py](/C:/Users/Q/code/propstore/propstore/world/hypothetical.py) still mutates synthetic claim payload dicts.
- [value_resolver.py](/C:/Users/Q/code/propstore/propstore/world/value_resolver.py) still resolves over `dict[str, object]`.
- [atms.py](/C:/Users/Q/code/propstore/propstore/world/atms.py) still rebuilds runtime rows as dict payloads.
- [resolution.py](/C:/Users/Q/code/propstore/propstore/world/resolution.py) still accepts `Mapping[str, object]` claim inputs.
- [af_adapter.py](/C:/Users/Q/code/propstore/propstore/revision/af_adapter.py) and [projection.py](/C:/Users/Q/code/propstore/propstore/revision/projection.py) still build revision atoms from claim dicts.
- [argumentation.py](/C:/Users/Q/code/propstore/propstore/worldline/argumentation.py) and [trace.py](/C:/Users/Q/code/propstore/propstore/worldline/trace.py) still inspect claim ids through `.get(...)`.

The intended end state is:

- sidecar boundary: `ClaimRow`
- runtime active/bound/hypothetical boundary: `ActiveClaim`
- graph/runtime explanation boundary: `ClaimNode`, `ConflictWitness`, `StanceRow`, `ResolvedResult`, `ValueResult`
- only explicit UI/serialization/report boundaries project typed claims back to dicts

## Non-goals

- Do not redesign authored/canonical claim schema here.
- Do not change sidecar schema.
- Do not merge runtime active claims into `ClaimRow`.
- Do not add another compatibility shim layer that keeps dict and typed paths both first-class.

## Existing pieces to reuse

- `ClaimRow` and nested value types in [row_types.py](/C:/Users/Q/code/propstore/propstore/core/row_types.py) and [claim_values.py](/C:/Users/Q/code/propstore/propstore/core/claim_values.py)
- `ClaimId`, `ConceptId`, `ContextId` in [id_types.py](/C:/Users/Q/code/propstore/propstore/core/id_types.py)
- `Label`, `SupportQuality`, `EnvironmentKey` in [labels.py](/C:/Users/Q/code/propstore/propstore/core/labels.py)
- `ValueResult`, `DerivedResult`, `ResolvedResult` in [types.py](/C:/Users/Q/code/propstore/propstore/world/types.py)
- `ClaimNode` in [graph_types.py](/C:/Users/Q/code/propstore/propstore/core/graph_types.py)

## New runtime types

Add a new leaf-ish runtime module, preferably:

- [active_claims.py](/C:/Users/Q/code/propstore/propstore/world/active_claims.py)

Define:

### `ActiveClaim`

Canonical runtime claim object for active/bound/hypothetical reasoning.

Fields:

- `claim_id: ClaimId`
- `artifact_id: str`
- `claim_type: str | None`
- `concept_id: ConceptId | None`
- `target_concept: ConceptId | None`
- `logical_ids: tuple[LogicalId, ...]`
- `version_id: str | None`
- `seq: int | None`
- `value: float | str | None`
- `lower_bound: float | None`
- `upper_bound: float | None`
- `uncertainty: float | None`
- `uncertainty_type: str | None`
- `sample_size: int | None`
- `unit: str | None`
- `conditions: tuple[str, ...]`
- `statement: str | None`
- `expression: str | None`
- `sympy_generated: str | None`
- `sympy_error: str | None`
- `name: str | None`
- `measure: str | None`
- `listener_population: str | None`
- `methodology: str | None`
- `notes: str | None`
- `description: str | None`
- `auto_summary: str | None`
- `body: str | None`
- `canonical_ast: str | None`
- `variables: tuple[ActiveClaimVariable, ...] | Mapping[str, str] | None`
- `stage: str | None`
- `source: ClaimSource | None`
- `provenance: ClaimProvenance | None`
- `value_si: float | None`
- `lower_bound_si: float | None`
- `upper_bound_si: float | None`
- `context_id: ContextId | None`
- `branch: str | None`
- `attributes: Mapping[str, Any]`

Required convenience properties:

- `primary_logical_id`
- `primary_logical_value`
- `display_claim_id`
- `source_slug`
- `source_paper`
- `provenance_page`
- `conditions_cel_json`

Required constructors:

- `from_claim_row(row: ClaimRow) -> ActiveClaim`
- `from_mapping(data: Mapping[str, Any]) -> ActiveClaim`

Required serializers:

- `to_dict()` only for explicit legacy/report edges
- `to_source_claim_payload()` for the conflict detector bridge in `BoundWorld`

### `ActiveClaimVariable`

Only if variable payloads are kept structured.

Fields:

- `name: str | None`
- `symbol: str | None`
- `concept_id: ConceptId | None`

If variable payloads are not normalized in this slice, keep them opaque and typed as a dedicated union instead of `dict`.

## Architectural rules

### Rule 1

`BoundWorld.active_claims()` and `inactive_claims()` must return `list[ActiveClaim]`, not `list[dict]`.

### Rule 2

`ValueResult.claims` and `ResolvedResult.claims` must hold `ActiveClaim` objects, not dicts.

This is the key interface change. We control both sides.

### Rule 3

Do not keep `_claim_mapping(...)` helpers in world/runtime code.

If a module still needs `dict`, that module is the explicit serialization edge and should call `to_dict()` itself.

### Rule 4

`ClaimRow` is storage-shaped.
`ActiveClaim` is runtime-shaped.
Neither should pretend to be the other.

### Rule 5

ATMS runtime claim payloads must stop using anonymous `dict` payloads internally.

If `ATMSNode.payload` still needs a claim-like payload, give it an explicit type:

- either `ActiveClaim`
- or a smaller typed `ATMSClaimPayload`

Do not preserve raw dict payloads there.

## Phase plan

### Phase 1: Define the runtime claim type and change world protocols

Files:

- [active_claims.py](/C:/Users/Q/code/propstore/propstore/world/active_claims.py)
- [types.py](/C:/Users/Q/code/propstore/propstore/world/types.py)

Changes:

- Add `ActiveClaim`.
- Add `ActiveClaimInput = ActiveClaim | ClaimRow | Mapping[str, Any]` temporarily only while callers are being updated.
- Change `ValueResult.claims` from `list[dict]` to `list[ActiveClaim]`.
- Change `ResolvedResult.claims` accordingly.
- Change `BeliefSpace.active_claims()` / `inactive_claims()` protocol to `list[ActiveClaim]`.
- Change `ClaimSupportView.claim_support()` to accept `ActiveClaim`.

Delete:

- Old dict-based `BeliefSpace` claim signatures in [types.py](/C:/Users/Q/code/propstore/propstore/world/types.py).

### Phase 2: Convert `BoundWorld`

Files:

- [bound.py](/C:/Users/Q/code/propstore/propstore/world/bound.py)
- [activation.py](/C:/Users/Q/code/propstore/propstore/core/activation.py)

Changes:

- Replace `_claim_mapping(...)` with `ActiveClaim.from_claim_row(...)`.
- Make `active_claims()` and `inactive_claims()` return `ActiveClaim`.
- Convert `is_active()` and support/label helpers to operate on `ActiveClaim`.
- Replace `_claim_row_to_source_claim(claim: dict)` with `claim.to_source_claim_payload()`.
- Update `algorithm_for`, `extract_variable_concepts`, `extract_bindings`, `conflicts`, `explain`, `claim_support`, `_claim_support_label`, `_support_quality`, and result-label attachment helpers to use typed fields.

Important deletion:

- Delete `_claim_mapping` from [bound.py](/C:/Users/Q/code/propstore/propstore/world/bound.py).

### Phase 3: Convert `ActiveClaimResolver`

Files:

- [value_resolver.py](/C:/Users/Q/code/propstore/propstore/world/value_resolver.py)

Changes:

- Delete `_ActiveClaimView.raw: dict[str, object]`.
- Make `_ActiveClaimView` either unnecessary or wrap `ActiveClaim` directly.
- Change all helper functions from `claim.get(...)` to typed attribute access.
- Change algorithm equivalence / direct-value matching to consume typed variables and body fields.
- Make `value_of_from_active()` accept `Sequence[ActiveClaim]`.
- Make all result objects return `ActiveClaim`, not raw dicts.

Important question to settle explicitly:

- Are algorithm claims valid runtime claims without scalar `value`?
Yes. Preserve that. The runtime type must represent that honestly instead of faking a generic dict shape.

### Phase 4: Convert `HypotheticalWorld`

Files:

- [hypothetical.py](/C:/Users/Q/code/propstore/propstore/world/hypothetical.py)

Changes:

- Replace `_claim_mapping(...)` and synthetic row dict mutation with typed overlay construction.
- Add a typed constructor for synthetic claims into `ActiveClaim` and `ClaimRow` as needed.
- Make overlay claims and overlay store return typed `ClaimRow` at storage boundary and typed `ActiveClaim` at runtime boundary.
- Recompute conflicts from typed `ActiveClaim.to_source_claim_payload()`.
- Update `_value_set()` and all claim-id lookups to use typed fields.

Delete:

- `_claim_mapping` from [hypothetical.py](/C:/Users/Q/code/propstore/propstore/world/hypothetical.py).

### Phase 5: Convert world resolution

Files:

- [resolution.py](/C:/Users/Q/code/propstore/propstore/world/resolution.py)

Changes:

- Replace `Mapping[str, object]` claim flow with `ActiveClaim`.
- `_ResolutionClaimView` should likely become unnecessary; either:
  - use `ActiveClaim` directly, or
  - rename it to a typed reduced projection built only from `ActiveClaim`
- Remove `_claim_id`, `_claim_value`, `_claim_optional_*` mapping helpers where possible.
- Make `_claim_concept_id`, branch filtering, IC merge grouping, and strategy selection operate on typed fields.

Important deletion:

- No more `ClaimRowInput | Mapping[str, object]` in resolution-facing internals once caller conversion is complete.

### Phase 6: Convert ATMS runtime

Files:

- [atms.py](/C:/Users/Q/code/propstore/propstore/world/atms.py)

Changes:

- Change `_ATMSRuntimeLike.active_claims` from `Callable[[], list[dict[str, Any]]]` to `Callable[[], list[ActiveClaim]]`
- Change `_ATMSRuntimeLike.claim_support` from `Callable[[dict[str, Any]], ...]` to `Callable[[ActiveClaim], ...]`
- Replace `_claim_node_to_row()` with `_claim_node_to_active_claim()` or similar.
- Replace `ATMSNode.payload: dict[str, Any]` for claim nodes with typed payload.
- Update all concept-id, claim-id, value, condition, and support-quality reads to use typed fields.

Important design constraint:

ATMS replay should not silently serialize typed runtime claims back to dicts just to feed itself.

### Phase 7: Convert revision projection and argumentation overlay

Files:

- [projection.py](/C:/Users/Q/code/propstore/propstore/revision/projection.py)
- [af_adapter.py](/C:/Users/Q/code/propstore/propstore/revision/af_adapter.py)

Changes:

- Make revision belief projection consume `ActiveClaim`.
- `BeliefAtom.payload` may remain mapping-shaped if revision state is intentionally generic, but the projection step must be explicit and one-way.
- Change `_claim_atom_id()` and `_claim_support_lookup_id()` to operate on `ActiveClaim`.
- Make `RevisionArgumentationStore` return typed active claims, not copied dicts.

Important question:

Should revision atoms themselves become typed claim atoms?

Not required for this slice. The runtime leak to remove here is the world/revision boundary, not the entire revision-state representation.

### Phase 8: Convert worldline consumers

Files:

- [argumentation.py](/C:/Users/Q/code/propstore/propstore/worldline/argumentation.py)
- [trace.py](/C:/Users/Q/code/propstore/propstore/worldline/trace.py)
- [resolution.py](/C:/Users/Q/code/propstore/propstore/worldline/resolution.py)

Changes:

- Make `capture_argumentation_state()` consume `list[ActiveClaim]`.
- Replace `.get("id")` lookups with typed access.
- Make `ResolutionTrace.record_claim_dependencies()` accept `Sequence[ActiveClaim]`.
- Remove any remaining logical-id or value reads from dict payloads in the worldline path.

### Phase 9: Sweep and delete old dict path

Files to revisit after the core conversion:

- [bound.py](/C:/Users/Q/code/propstore/propstore/world/bound.py)
- [hypothetical.py](/C:/Users/Q/code/propstore/propstore/world/hypothetical.py)
- [value_resolver.py](/C:/Users/Q/code/propstore/propstore/world/value_resolver.py)
- [resolution.py](/C:/Users/Q/code/propstore/propstore/world/resolution.py)
- [atms.py](/C:/Users/Q/code/propstore/propstore/world/atms.py)
- [af_adapter.py](/C:/Users/Q/code/propstore/propstore/revision/af_adapter.py)
- [projection.py](/C:/Users/Q/code/propstore/propstore/revision/projection.py)
- [argumentation.py](/C:/Users/Q/code/propstore/propstore/worldline/argumentation.py)
- [trace.py](/C:/Users/Q/code/propstore/propstore/worldline/trace.py)
- [types.py](/C:/Users/Q/code/propstore/propstore/world/types.py)

Delete:

- `_claim_mapping(...)`
- `_claim_row_to_source_claim(...)`
- dict-based `claim_support(...)` protocols
- dict-based `active_claims(...)` protocols
- dict-based helper functions whose only job was to compensate for anonymous claim payloads

## Type conversion rules

### ClaimRow -> ActiveClaim

Valid and required.

This is the main runtime construction boundary.

### ActiveClaim -> source-claim payload dict

Valid only for explicit legacy detector/input boundaries that still require authoring-ish payloads.

This conversion should be a named method on `ActiveClaim`, not an ad hoc helper in `BoundWorld`.

### ActiveClaim -> dict

Valid only for:

- legacy serialization
- CLI/report/UI payloads
- revision atom payloads if revision remains generic in this slice

Not valid as an internal world/runtime transport type.

### ActiveClaim -> ClaimRow

Generally not valid.

Runtime claims are not storage rows. If overlay code needs a storage row to enter the sidecar/store-shaped world, that conversion must be explicit and narrow.

## Known sharp edges

### 1. `ValueResult` / `ResolvedResult` interface break

This is intentional. A large fraction of runtime callers assume `claims` is a list of dicts.

The right fix is to update every caller, not to carry both shapes.

### 2. Algorithm variable payloads

Current code treats `variables_json` as a JSON string in some places and as source-local `variables` payloads in others.

This slice must decide whether:

- variables become a typed runtime object now, or
- variables remain opaque but explicitly wrapped

Do not keep raw `dict`/`list[dict]` as the hidden default.

### 3. Revision payload shape

Revision atoms may still want generic `payload: Mapping[str, Any]`.

That is acceptable only if projection from `ActiveClaim` into revision payload is explicit and localized in [projection.py](/C:/Users/Q/code/propstore/propstore/revision/projection.py).

### 4. ATMS internal payload typing

`ATMSNode.payload` is a major dict sink today. If not fixed, the workstream will leave a large internal leak intact.

## Test plan

Focused suites to keep green throughout:

- [test_world_model.py](/C:/Users/Q/code/propstore/tests/test_world_model.py)
- [test_graph_build.py](/C:/Users/Q/code/propstore/tests/test_graph_build.py)
- [test_graph_export.py](/C:/Users/Q/code/propstore/tests/test_graph_export.py)
- [test_worldline_praf.py](/C:/Users/Q/code/propstore/tests/test_worldline_praf.py)
- [test_worldline_error_visibility.py](/C:/Users/Q/code/propstore/tests/test_worldline_error_visibility.py)
- [test_praf_integration.py](/C:/Users/Q/code/propstore/tests/test_praf_integration.py)
- [test_atms_engine.py](/C:/Users/Q/code/propstore/tests/test_atms_engine.py)
- [test_core_justifications.py](/C:/Users/Q/code/propstore/tests/test_core_justifications.py)

Add new direct guardrail tests for:

- `BoundWorld.active_claims()` returns `ActiveClaim`
- `HypotheticalWorld.active_claims()` returns `ActiveClaim`
- `ValueResult.claims` and `ResolvedResult.claims` contain `ActiveClaim`
- revision projection derives atom ids from typed logical ids without dict parsing
- ATMS runtime active-claim input is typed end-to-end
- worldline trace dependency capture accepts typed claims directly

## Recommended execution order

1. Add `ActiveClaim` and update [types.py](/C:/Users/Q/code/propstore/propstore/world/types.py)
2. Convert [value_resolver.py](/C:/Users/Q/code/propstore/propstore/world/value_resolver.py)
3. Convert [bound.py](/C:/Users/Q/code/propstore/propstore/world/bound.py)
4. Convert [hypothetical.py](/C:/Users/Q/code/propstore/propstore/world/hypothetical.py)
5. Convert [resolution.py](/C:/Users/Q/code/propstore/propstore/world/resolution.py)
6. Convert [atms.py](/C:/Users/Q/code/propstore/propstore/world/atms.py)
7. Convert [projection.py](/C:/Users/Q/code/propstore/propstore/revision/projection.py) and [af_adapter.py](/C:/Users/Q/code/propstore/propstore/revision/af_adapter.py)
8. Convert [argumentation.py](/C:/Users/Q/code/propstore/propstore/worldline/argumentation.py) and [trace.py](/C:/Users/Q/code/propstore/propstore/worldline/trace.py)
9. Sweep and delete all remaining dict claim transport helpers

## Success criteria

This workstream is complete only when:

- `BeliefSpace.active_claims()` no longer returns `dict`
- `ValueResult.claims` and `ResolvedResult.claims` no longer carry `dict`
- `BoundWorld`, `HypotheticalWorld`, `ActiveClaimResolver`, `ATMSEngine`, revision projection, and worldline capture do not use `claim.get(...)` on runtime claim transport objects
- the remaining `dict` claim payloads exist only at explicit serialization/projection edges
- the old dict transport helpers are deleted
