# World/Worldline Cleanup Refactor Fixed-Point Log - 2026-05-22

Target architecture:
- `propstore.world` and `propstore.worldline` runtime APIs receive typed domain
  values after the IO/app boundary.
- CLI/app request boundaries parse strings into typed enums before calling
  runtime owners.
- Package and runtime modules do not preserve old paths through coercers,
  normalizers, compatibility branches, fallback readers, broad re-exports, or
  duplicated field knowledge.

Forbidden surfaces:
- `coerce_*` helpers that accept `object` or raw strings past the boundary.
- `normalize_*` helpers that carry old spellings or aliases through runtime.
- fallback/legacy compatibility paths not required by an external data target.
- loose `dict`/payload constructors past exact IO/document boundaries.
- broad package initializer imports used by production internals instead of
  concrete owner modules.

Search gates:
- `rg -n -F -- "coerce_value_status" propstore tests`
- `rg -n -F -- "normalize_reasoning_backend" propstore tests`
- `rg -n -F -- "normalize_argumentation_semantics" propstore tests`
- `rg -n -F -- "fallback" propstore/world propstore/worldline`
- `rg -n -F -- "legacy" propstore/world propstore/worldline`
- `rg -n -F -- "from_payload" propstore/world propstore/worldline`

Runtime gates:
- `powershell -File scripts/run_logged_pytest.ps1 -Label world-value-status-cleanup ...`
- `uv run pyright propstore`

## Iteration 18 - `propstore/worldline/__init__.py`

Slice read:
- `propstore/worldline/__init__.py`
- `propstore/app/worldlines.py`
- current production and test imports of `propstore.worldline`.

Surfaces:
- `propstore.worldline` package initializer exports
  - Disposition: keep as the small public worldline API surface.
  - Owner after cleanup: package-level public imports for external/test callers
    only; production internals use concrete owner modules.
  - Evidence: the initializer exports six named worldline entrypoints and does
    not contain compatibility branches, fallback readers, field restatement, or
    runtime coercion.
- production imports from the worldline package initializer
  - Disposition: delete.
  - Owner after cleanup: `propstore.worldline.definition` owns
    `WorldlineDefinition` and `WorldlineResult`; `propstore.worldline.runner`
    owns `run_worldline`.
  - Action: update `propstore/app/worldlines.py` to import from concrete owner
    modules, and update tests that patched the old package-barrel runner symbol
    to patch the concrete runner owner.

Gate results:
- Pass: full-suite pre-slice rerun
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  goal-rerun-before-next-slice` returned `3518 passed, 4 skipped, 30 warnings`.
- Log: `logs/test-runs/goal-rerun-before-next-slice-20260522-031819.log`.
- Pass: `rg -n -F -- "from propstore.worldline import" propstore`
  returned zero hits.
- Pass: `rg -n -F -- "propstore.worldline.run_worldline" tests propstore`
  returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Failed then fixed: first targeted logged pytest run exposed two stale test
  monkeypatches of `propstore.worldline.run_worldline`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-init-barrel-cleanup-rerun tests/test_worldline.py
  tests/test_worldline_revision.py tests/test_artifact_store.py
  tests/test_atms_engine.py tests/test_capture_journal.py
  tests/test_lifting_blocked_in_provenance.py tests/test_policy_governance.py
  tests/test_structured_projection.py tests/test_worldline_hash_width.py
  tests/test_worldline_hash_excludes_transient_errors.py
  tests/test_worldline_praf.py tests/test_worldline_properties.py
  tests/test_worldline_target_shape_validation.py` returned `175 passed`.
- Log: `logs/test-runs/worldline-init-barrel-cleanup-rerun-20260522-032908.log`.

Commit:
- Remove app worldline barrel imports.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/worldline/_constants.py`.

## Iteration 19 - `propstore/worldline/_constants.py`

Slice read:
- `propstore/worldline/_constants.py`
- `propstore/worldline/trace.py`
- `tests/test_worldline_override_prefix_constant.py`
- current `OVERRIDE_CLAIM_PREFIX`, `__override_`, and
  `record_claim_dependency` hits.

Surfaces:
- `OVERRIDE_CLAIM_PREFIX`
  - Disposition: delete.
  - Owner after cleanup: none; the current runtime records typed claim
    dependencies from real claim resolution paths.
  - Evidence: no production path created the `__override_` sentinel; the module
    existed only to preserve a private string filter in `ResolutionTrace`.
- `ResolutionTrace.record_claim_dependency` sentinel-prefix filter
  - Disposition: delete.
  - Owner after cleanup: `ResolutionTrace` records the claim id it is given;
    callers that resolve real claims already pass real claim ids.
- `tests/test_worldline_override_prefix_constant.py`
  - Disposition: delete.
  - Evidence: the test asserted the removed private sentinel behavior and did
    not describe current runtime semantics.

Gate results:
- Pass: `rg -n -F -- "OVERRIDE_CLAIM_PREFIX" propstore tests` returned zero
  hits.
- Pass: `rg -n -F -- "__override_" propstore tests` returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-override-constant-deletion tests/test_worldline.py
  tests/test_worldline_revision.py tests/test_capture_journal.py
  tests/test_worldline_hash_width.py
  tests/test_worldline_hash_excludes_transient_errors.py
  tests/test_worldline_praf.py tests/test_worldline_properties.py` returned
  `93 passed`.
- Log:
  `logs/test-runs/worldline-override-constant-deletion-20260522-033503.log`.

Commit:
- Delete worldline override sentinel constant.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/worldline/trace.py`.

## Iteration 20 - `propstore/worldline/trace.py`

Slice read:
- `propstore/worldline/trace.py`
- `propstore/worldline/result_types.py`
- current `ResolutionTrace` and `record_step` callers.

Surfaces:
- `ResolutionTrace.record_binding`, `record_override`, and `record_step`
  value parameters
  - Disposition: rewrite.
  - Owner after cleanup: `propstore.worldline.result_types` owns the scalar
    worldline value type once as `WorldlineScalarValue`.
  - Action: replace trace-local `Any` value parameters with the result-model
    scalar value alias, and use the same alias for `WorldlineInputSource`,
    `WorldlineTargetValue`, and `WorldlineStep` values.
  - Evidence: `WorldlineStep` already restricted persisted step values to
    `float | str | None`; trace accepted `Any`, weakening the typed runtime
    boundary before constructing the typed result object.

Gate results:
- Pass: `rg -n -F -- "value: Any" propstore/worldline/trace.py
  propstore/worldline/result_types.py` returned no trace hits; remaining hits
  are IO/helper payload functions in `result_types.py`.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-trace-scalar-value tests/test_worldline.py
  tests/test_worldline_revision.py tests/test_capture_journal.py
  tests/test_worldline_hash_width.py
  tests/test_worldline_hash_excludes_transient_errors.py
  tests/test_worldline_praf.py tests/test_worldline_properties.py` returned
  `93 passed`.
- Log: `logs/test-runs/worldline-trace-scalar-value-20260522-034019.log`.

Commit:
- Type worldline trace scalar values.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/worldline/runner.py`.

## Iteration 21 - `propstore/worldline/runner.py`

Slice read:
- `propstore/worldline/runner.py`
- `propstore/worldline/interfaces.py`
- `propstore/world/bound.py`
- current `_environment`, `_lifting_system`, and `Any` hits in runner and
  worldline interfaces.

Surfaces:
- runner helper `bound: Any`
  - Disposition: rewrite.
  - Owner after cleanup: `WorldlineBoundView` is the runner's bound-world type.
  - Action: type `_capture_sensitivity`, `_context_dependencies`, and
    `_lifting_dependencies` with `WorldlineBoundView`.
- `HasEnvironment._environment` and `HasLiftingSystem._lifting_system`
  - Disposition: delete.
  - Owner after cleanup: `BoundWorld.environment` and
    `BoundWorld.lifting_system` public properties expose the semantic state
    that worldline dependency capture needs.
  - Action: add those properties to `BoundWorld`, update worldline protocols,
    and update runner dependency capture to use public properties.
  - Evidence: the previous protocols made private attributes part of the
    worldline contract instead of asking the bound-world owner for the required
    semantic state.

Gate results:
- Pass: `rg -n -F -- "_environment"
  propstore/worldline/runner.py propstore/worldline/interfaces.py` returned
  zero hits.
- Pass: `rg -n -F -- "_lifting_system"
  propstore/worldline/runner.py propstore/worldline/interfaces.py` returned
  zero hits.
- Pass: `rg -n -F -- "Any" propstore/worldline/runner.py` returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-runner-bound-properties tests/test_worldline.py
  tests/test_worldline_revision.py tests/test_capture_journal.py
  tests/test_worldline_hash_width.py
  tests/test_worldline_hash_excludes_transient_errors.py
  tests/test_worldline_praf.py tests/test_worldline_properties.py
  tests/test_lifting_blocked_in_provenance.py` returned `95 passed`.
- Log: `logs/test-runs/worldline-runner-bound-properties-20260522-034611.log`.

Commit:
- Expose bound worldline dependency state through properties.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/worldline/revision_types.py`.

## Iteration 22 - `propstore/worldline/revision_types.py`

Slice read:
- `propstore/worldline/revision_types.py`
- `propstore/support_revision/state.py`
- `propstore/support_revision/input_normalization.py`
- `propstore/families/documents/worldlines.py`
- current `from_json_payload`, `Any`, `WorldlineRevisionResult`, and
  `to_revision_input` hits.

Surfaces:
- `RevisionAtomRef.value`
  - Disposition: rewrite.
  - Owner after cleanup: `WorldlineScalarValue` in
    `propstore.worldline.result_types` owns scalar worldline values.
  - Action: replace the repeated `float | str | None` union with the shared
    worldline scalar alias.
- `WorldlineRevisionResult.explanation` and `WorldlineRevisionState.state`
  - Disposition: rewrite.
  - Owner after cleanup: revision document boundary stores these as mappings;
    support-revision owner types still own the semantic explanation/event
    structures.
  - Action: replace arbitrary `Any | None` fields with
    `Mapping[str, Any] | None`, matching the existing boundary validation.
  - Evidence: `from_json_payload` already rejects non-mapping `explanation`,
    `result`, `state`, and `event` blocks.

Gate results:
- Pass: `rg -n -F -- "float | str | None"
  propstore/worldline/revision_types.py` returned zero hits.
- Pass: `rg -n -F -- "Any | None"
  propstore/worldline/revision_types.py` returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-revision-types-tightening tests/test_worldline_revision.py
  tests/test_worldline_revision_event_capture.py
  tests/test_worldline_revision_properties.py
  tests/test_worldline_revision_snapshot_boundary.py
  tests/test_mapping_boundary_failures.py tests/test_capture_journal.py
  tests/test_worldline.py` returned `86 passed`.
- Log: `logs/test-runs/worldline-revision-types-tightening-20260522-035120.log`.

Commit:
- Tighten worldline revision document value types.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/worldline/revision_capture.py`.

## Iteration 23 - `propstore/worldline/revision_capture.py`

Slice read:
- `propstore/worldline/revision_capture.py`
- `propstore/worldline/definition.py`
- `propstore/worldline/interfaces.py`
- `propstore/worldline/revision_types.py`
- `propstore/world/bound.py`
- revision capture, journal capture, and snapshot-boundary tests.

Surfaces:
- raw `revision_query: Any` and `Sequence[Any]` operation inputs
  - Disposition: rewrite.
  - Owner after cleanup: `WorldlineRevisionQuery` owns worldline revision query
    shape.
  - Action: type capture and journal operations with `WorldlineRevisionQuery`.
- raw revision-capable `bound: Any`
  - Disposition: rewrite.
  - Owner after cleanup: `WorldlineBoundView` owns the worldline runner's bound
    view contract, including revision methods used by revision capture.
  - Action: add the revision method surface to `WorldlineBoundView` and type
    revision capture helpers against that protocol.
- live iterated revision state object in `WorldlineRevisionState.state`
  - Disposition: delete.
  - Owner after cleanup: worldline revision state stores the snapshot payload
    mapping returned by the bound-world revision snapshot owner.
  - Action: `_revision_state_snapshot` now requires
    `bound.revision_state_snapshot(state)` and stores its `to_dict()` mapping,
    while still rejecting missing snapshot support with an explicit TypeError.
- support-revision explanation payload
  - Disposition: keep typed owner object.
  - Owner after cleanup: `RevisionExplanation` remains owned by
    `propstore.support_revision.explanation_types`; worldline result
    serialization calls its `to_dict()` through the existing plain-data path.

Gate results:
- Pass: `rg -n -F -- "bound: Any" propstore/worldline/revision_capture.py`
  returned zero hits.
- Pass: `rg -n -F -- "revision_query: Any"
  propstore/worldline/revision_capture.py` returned zero hits.
- Pass: `rg -n -F -- "result: Any"
  propstore/worldline/revision_capture.py` returned zero hits.
- Pass: `rg -n -F -- "state: Any"
  propstore/worldline/revision_capture.py` returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Failed then fixed: the first logged rerun exposed one stale test assertion
  expecting a state object with `to_dict()`; the second exposed the need to keep
  optional pre-state hash behavior for one-shot fake bounds and explicit
  snapshot TypeErrors.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-revision-capture-boundary-fixed tests/test_worldline_revision.py
  tests/test_worldline_revision_event_capture.py
  tests/test_worldline_revision_properties.py
  tests/test_worldline_revision_snapshot_boundary.py
  tests/test_mapping_boundary_failures.py tests/test_capture_journal.py
  tests/test_worldline.py` returned `86 passed`.
- Log:
  `logs/test-runs/worldline-revision-capture-boundary-fixed-20260522-035836.log`.

Commit:
- Type worldline revision capture boundaries.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/worldline/result_types.py`.

## Iteration 24 - `propstore/worldline/result_types.py`

Slice read:
- `propstore/worldline/result_types.py`
- `tests/test_worldline_result_boundaries.py`
- current `from_json_payload` and `Any` hits in result types.

Surfaces:
- `WorldlineInputSource.from_json_payload`, `WorldlineTargetValue.from_json_payload`,
  and `WorldlineStep.from_json_payload` raw `value` reads
  - Disposition: rewrite.
  - Owner after cleanup: `WorldlineScalarValue` owns worldline scalar values;
    `_worldline_scalar_value` enforces that boundary once.
  - Action: reject mapping/list/bool values before constructing typed result
    objects, and add focused boundary tests for all three value-bearing result
    types.
  - Evidence: the dataclass fields were already typed as scalar values, but the
    document loader passed raw `data.get("value")` through without checking the
    shape.
- remaining `Any` in this file
  - Disposition: keep for IO/document helpers and JSON serialization only.
  - Evidence: remaining hits are `from_json_payload` input mappings,
    `to_dict` JSON dictionaries, and `_json_native` serialization of nested
    typed reports.

Gate results:
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-result-types-scalar-boundary tests/test_worldline_result_boundaries.py
  tests/test_worldline.py tests/test_worldline_hash_excludes_transient_errors.py
  tests/test_worldline_revision.py` returned `68 passed`.
- Log:
  `logs/test-runs/worldline-result-types-scalar-boundary-20260522-040056.log`.

Commit:
- Validate worldline result scalar values.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/worldline/resolution.py`.

## Iteration 25 - `propstore/worldline/resolution.py`

Slice read:
- `propstore/worldline/resolution.py`
- `propstore/world/types.py`
- current `Any` and `getattr` hits in worldline resolution.

Surfaces:
- resolver helper `value_result: Any`
  - Disposition: rewrite.
  - Owner after cleanup: `ValueResult` from `propstore.world.types` owns the
    value-resolution result shape.
  - Action: type every target/input resolver helper with `ValueResult`.
- `_trace_derived_inputs(derived: Any)`
  - Disposition: rewrite.
  - Owner after cleanup: `DerivedResult` from `propstore.world.types` owns the
    derived-value result shape.
  - Action: type the helper with `DerivedResult`.
- `chain_bindings: dict[str, Any]`
  - Disposition: rewrite.
  - Owner after cleanup: chain-query keyword bindings are opaque objects at
    this pass-through boundary.
  - Action: use `dict[str, object]`.

Gate results:
- Pass: `rg -n -F -- "Any" propstore/worldline/resolution.py` returned zero
  hits.
- Pass: `rg -n -F -- "getattr" propstore/worldline/resolution.py` returned
  zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-resolution-typed-results tests/test_worldline.py
  tests/test_worldline_properties.py tests/test_worldline_praf.py
  tests/test_structured_projection.py tests/test_atms_engine.py
  tests/test_worldline_result_boundaries.py` returned `147 passed`.
- Log:
  `logs/test-runs/worldline-resolution-typed-results-20260522-040314.log`.

Commit:
- Type worldline resolution result flow.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/worldline/interfaces.py`.

## Iteration 26 - `propstore/worldline/interfaces.py`

Slice read:
- `propstore/worldline/interfaces.py`
- `propstore/worldline/resolution.py`
- current `HasBindings` and `_bindings` hits in worldline/world code.

Surfaces:
- `HasBindings` protocol exposing `_bindings`
  - Disposition: delete.
  - Owner after cleanup: `HasEnvironment.environment.bindings` exposes the
    binding data through the public bound-world environment surface.
  - Action: remove `HasBindings` and update worldline chain resolution to read
    `context.query_world.environment.bindings` when the bound view satisfies
    `HasEnvironment`.
  - Evidence: the protocol made a private `BoundWorld` attribute part of the
    worldline interface even though the environment property already owns that
    semantic state.

Gate results:
- Pass: `rg -n -F -- "HasBindings" propstore tests` returned zero hits.
- Pass: `rg -n -F -- "_bindings" propstore/worldline propstore/world` returned
  zero worldline private-binding hits; remaining world hits are owned by
  `BoundWorld` internals and unrelated binding helper code.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-interfaces-public-bindings tests/test_worldline.py
  tests/test_worldline_properties.py tests/test_worldline_praf.py
  tests/test_structured_projection.py` returned `99 passed`.
- Log:
  `logs/test-runs/worldline-interfaces-public-bindings-20260522-040811.log`.

Commit:
- Delete worldline private bindings protocol.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/worldline/hashing.py`.

## Iteration 27 - `propstore/worldline/hashing.py`

Slice read:
- `propstore/worldline/hashing.py`
- current `compute_worldline_content_hash` callers from literal search.

Surfaces:
- `compute_worldline_content_hash`
  - Disposition: keep.
  - Owner after cleanup: `propstore.worldline.hashing` owns the deterministic
    fingerprint over already-typed worldline content.
  - Evidence: the function receives typed `WorldlineTargetValue`,
    `WorldlineStep`, `WorldlineDependencies`, `WorldlineSensitivityReport`,
    `WorldlineArgumentationState`, and `WorldlineRevisionState` objects, then
    serializes through the owning objects' `to_dict()` methods for canonical
    RFC8785 hashing. It does not contain a shim, coercer, fallback reader,
    compatibility branch, `Any`, or duplicate field parser.

Gate results:
- Pass: `rg -n -F -- "Any" propstore/worldline/hashing.py` returned zero
  hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-hashing-keep tests/test_worldline_hash_width.py
  tests/test_worldline_hash_excludes_transient_errors.py
  tests/test_worldline_revision.py tests/test_policy_governance.py
  tests/test_worldline.py` returned `66 passed`.
- Log: `logs/test-runs/worldline-hashing-keep-20260522-041413.log`.

Commit:
- Record worldline hashing keep decision.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/worldline/definition.py`.

## Iteration 28 - `propstore/worldline/definition.py`

Slice read:
- `propstore/worldline/definition.py`
- `propstore/families/documents/worldlines.py`
- `propstore/contracts.py`
- `propstore/_resources/contract_manifests/semantic-contracts.yaml`
- current `WorldlineDefinition`, `WorldlineInputs`,
  `WorldlineRevisionQuery`, `WorldlineResult`, `merge_operator`, `Any`, and
  `_optional_mapping` hits.

Surfaces:
- `WorldlineInputs.from_document`
  - Disposition: rewrite.
  - Owner after cleanup: `WorldlineInputsDocument` owns the authored input
    shape; `Environment` owns environment parsing.
  - Action: replace hand-built environment field dictionaries with
    `to_document_builtins(data)` passed to `Environment.from_dict`.
- `WorldlineInputs.from_dict`, `WorldlineRevisionQuery.from_dict`,
  `WorldlineResult.from_dict`, and `WorldlineDefinition.from_dict`
  - Disposition: rewrite.
  - Owner after cleanup: Quire document conversion plus the
    `Worldline*Document` structs own decoded dict validation; runtime
    dataclasses receive typed domain objects.
  - Action: route dict payloads through `convert_document_value(...,
    Worldline*Document, ...)` and then through `from_document`.
- `_optional_mapping` and `_revision_profile_atom_ids`
  - Disposition: delete.
  - Evidence: after dict inputs use the document owner, these local parsing
    helpers are duplicate field-shape code.
- `WorldlineResult.__post_init__` conversion of dependencies, sensitivity,
  argumentation, and revision mappings
  - Disposition: delete.
  - Owner after cleanup: exact `from_dict`/`from_document` IO boundaries parse
    serialized mappings; runtime construction requires typed worldline result
    objects.
- `WorldlineRevisionQueryDocument.merge_operator` and runtime
  `merge_operator` fallback
  - Disposition: delete.
  - Owner after cleanup: revision queries use the single `operator` field.
  - Action: remove the duplicate document field, remove
    `data.merge_operator or data.operator` / `data.get("merge_operator") or
    data.get("operator")`, bump the document contract override to
    `2026.05.22`, and regenerate the checked-in contract manifest with
    `uv run pks contract-manifest --write`.
- `WorldlineDefinition.is_stale(world: Any)`
  - Disposition: rewrite.
  - Owner after cleanup: `WorldlineStore` protocol defines the worldline
    runner store surface.

Gate results:
- Pass: `rg -n -F -- "_optional_mapping"
  propstore/worldline/definition.py` returned zero hits.
- Pass: `rg -n -F -- "Any" propstore/worldline/definition.py` returned zero
  hits.
- Pass: `rg -n -F -- 'data.get("merge_operator")'
  propstore/worldline/definition.py
  propstore/families/documents/worldlines.py tests` returned zero hits.
- Pass: `uv run pks contract-manifest --write` regenerated
  `propstore/_resources/contract_manifests/semantic-contracts.yaml`; the
  `WorldlineRevisionQueryDocument` manifest entry is version `2026.05.22` and
  has no `merge_operator` field.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Failed then fixed: first logged pytest run
  `worldline-definition-document-boundary` passed 63 tests and failed one
  boundary assertion that still expected the old hand-built
  `values.target` message instead of the Quire/msgspec `$.values[...]` path.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-definition-document-boundary-contract
  tests/test_worldline.py::TestWorldlineDefinition
  tests/test_worldline.py::TestWorldlineCLIFlags tests/test_worldline_revision.py
  tests/test_worldline_result_boundaries.py tests/test_mapping_boundary_failures.py
  tests/test_capture_journal.py tests/test_cli_layout.py` returned
  `91 passed`.
- Log:
  `logs/test-runs/worldline-definition-document-boundary-contract-20260522-042213.log`.

Commit:
- Rewrite worldline definitions through documents.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/worldline/argumentation.py`.

## Iteration 29 - `propstore/worldline/argumentation.py`

Slice read:
- `propstore/worldline/argumentation.py`
- `propstore/worldline/interfaces.py`
- `propstore/world/bound.py`
- `propstore/world/overlay.py`
- active-graph fakes and direct argumentation tests.

Surfaces:
- `Any` active-graph and semantics parameters in worldline argumentation
  - Disposition: rewrite.
  - Owner after cleanup: `WorldActivationGraph` owns the active graph type;
    `ArgumentationSemantics` owns validated backend semantics.
  - Action: type `_capture_claim_graph`, `_capture_aspic`, `_capture_praf`,
    and `_worldline_inference_mode` with those owner types, and import
    `validate_backend_semantics` / `ReasoningBackend` from
    `propstore.core.reasoning`.
- `HasActiveGraph._active_graph` and `bound._active_graph` reads in worldline
  argumentation
  - Disposition: delete.
  - Owner after cleanup: bound-world objects expose `active_graph` as a public
    property.
  - Action: add `BoundWorld.active_graph`, `OverlayWorld.active_graph`, and
    change the worldline `HasActiveGraph` protocol plus argumentation capture
    to use the public property.
- Test fakes with only `_active_graph`
  - Disposition: rewrite.
  - Action: make fakes implement the same public `active_graph` protocol and
    pass typed `ArgumentationSemantics` / `WorldActivationGraph` in direct
    argumentation tests.

Gate results:
- Pass: `rg -n -F -- "Any" propstore/worldline/argumentation.py` returned
  zero hits.
- Pass: `rg -n -F -- "bound._active_graph"
  propstore/worldline/argumentation.py propstore/worldline/interfaces.py
  tests/test_worldline.py tests/test_worldline_praf.py
  tests/test_worldline_argumentation_multi_extension.py` returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Failed then fixed: first logged pytest run
  `worldline-argumentation-typed-active-graph` failed two graph-backed
  worldline tests because fakes still implemented only `_active_graph`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-argumentation-typed-active-graph-rerun
  tests/test_worldline.py::TestSemanticCorePhase7Worldlines
  tests/test_worldline.py::TestWorldlineDependencyLiveness
  tests/test_worldline_praf.py
  tests/test_worldline_argumentation_multi_extension.py
  tests/test_structured_projection.py tests/test_atms_engine.py` returned
  `75 passed`.
- Log:
  `logs/test-runs/worldline-argumentation-typed-active-graph-rerun-20260522-042639.log`.

Commit:
- Expose worldline active graph property.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/world/__init__.py`.

## Iteration 30 - `propstore/world/__init__.py`

Slice read:
- `propstore/world/__init__.py`
- current production `from propstore.world import ...` callers.

Surfaces:
- `propstore.world` package initializer
  - Disposition: keep as the public world API barrel.
  - Evidence: tests and external callers may import the public world surface
    from the package root.
- production imports through `propstore.world`
  - Disposition: delete.
  - Owner after cleanup: production modules import concrete owner modules:
    `WorldQuery` from `propstore.world.model`, `BoundWorld` from
    `propstore.world.bound`, `OverlayWorld` from `propstore.world.overlay`,
    `resolve` from `propstore.world.resolution`, core environment/reasoning
    types from `propstore.core.*`, and render/result types from
    `propstore.world.types`.
  - Action: update production imports in app, compiler, verification,
    graph-export, fragility, epistemic process, support revision, and world
    query modules. Tests may continue using the public API.

Gate results:
- Pass: `rg -n -F -- "from propstore.world import" propstore` returned zero
  hits.
- Pass: `rg -n -F -- "import propstore.world" propstore` returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Failed then fixed: first logged pytest command selected zero tests because
  the `TestWorldQueryBasics` node id did not exist.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-package-barrel-production-imports-rerun tests/test_cli_layout.py
  tests/test_world_query.py::TestWorldQueryConstruction
  tests/test_world_query.py::TestWorldQuerySidecarPath
  tests/test_worldline.py::TestWorldlineRunner tests/test_semantic_repairs.py
  tests/test_graph_export.py tests/test_claim_workflows.py
  tests/test_concept_workflows.py` returned `68 passed`.
- Log:
  `logs/test-runs/world-package-barrel-production-imports-rerun-20260522-043222.log`.

Commit:
- Remove production world barrel imports.

Next slice:
- Continue deterministic per-file cleanup-refactor review with the next
  `propstore/world` file.

## Iteration 31 - `propstore/world/actual_cause.py`

Slice read:
- `propstore/world/actual_cause.py`
- current `actual_cause` callers.

Surfaces:
- `actual_cause`, `ActualCauseVerdict`, `ActualCauseWitness`,
  `EnumerationExceeded`
  - Disposition: keep.
  - Owner after cleanup: `propstore.world.actual_cause` owns modified-HP
    actual-cause evaluation over `InterventionWorld` and
    `StructuralCausalModel`.
  - Evidence: the file uses typed SCM/intervention/value surfaces, has no
    `Any`, no dict/payload parser, no compatibility branch, no fallback
    reader, and no duplicate field metadata.

Gate results:
- Pass: `rg -n -F -- "Any" propstore/world/actual_cause.py` returned zero
  hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-actual-cause-keep tests/test_actual_cause_suzy_billy.py
  tests/test_actual_cause_minimality.py tests/test_actual_cause_forest_fire.py
  tests/test_actual_cause_witness_budget.py tests/test_actual_cause_voting.py
  tests/test_intervention_world_public_surface.py` returned `10 passed`.
- Log:
  `logs/test-runs/world-actual-cause-keep-20260522-043352.log`.

Commit:
- Record world actual-cause keep decision.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/world/assignment_selection_policy.py`.

## Iteration 32 - `propstore/world/assignment_selection_policy.py`

Slice read:
- `propstore/world/assignment_selection_policy.py`
- assignment-selection, condition-runtime, and resolution-helper tests.

Surfaces:
- external assignment-selection integration module
  - Disposition: keep.
  - Owner after cleanup: `propstore.world.assignment_selection_policy` owns the
    boundary between Propstore `Claim`/`RenderPolicy`/`WorldStore` semantics
    and the external `assignment_selection` solver package.
  - Evidence: this is an external package integration boundary, not a
    compatibility shim for an old Propstore path; tests explicitly assert the
    old `assignment_selection_merge` module path is deleted.
- local `Any` annotations in CEL/range binding dictionaries
  - Disposition: rewrite.
  - Owner after cleanup: object-valued assignment/condition bindings at the
    external solver boundary.
  - Action: use `dict[str, object]`, import `WorldStore` from
    `propstore.core.environment`, and explicitly narrow range metadata and
    scoped values before numeric conversion.

Gate results:
- Pass: `rg -n -F -- "Any"
  propstore/world/assignment_selection_policy.py` returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Failed then fixed: first Pyright run exposed one un-narrowed `float(value)`
  call after replacing `Any` with `object`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-assignment-selection-policy-typed-rerun
  tests/test_assignment_selection_merge.py
  tests/test_condition_runtime_no_reparse.py
  tests/test_resolution_helpers.py::test_assignment_selection_policy_adapter_surface_exists
  tests/test_resolution_helpers.py::test_assignment_selection_old_solver_module_is_deleted
  tests/test_policy_governance.py` returned `24 passed`.
- Log:
  `logs/test-runs/world-assignment-selection-policy-typed-rerun-20260522-043621.log`.

Commit:
- Type assignment-selection policy boundary.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/world/atms.py`.

## Iteration 33 - `propstore/world/atms.py`

Slice read:
- `propstore/world/atms.py`
- `propstore/world/bound.py`
- `tests/test_atms_engine.py`

Surfaces:
- `_ATMSBoundLike` private `BoundWorld` attribute protocol
  - Disposition: rewrite.
  - Owner after cleanup: public `BoundWorld` properties expose the typed
    runtime substrate needed by ATMS without making ATMS depend on private
    storage attributes.
  - Action: add `BoundWorld.store` and `BoundWorld.policy`, use existing
    `BoundWorld.environment`, `BoundWorld.lifting_system`, and
    `BoundWorld.active_graph`, and remove the `_ATMSRuntime` private
    compatibility properties.
  - Evidence: the ATMS runtime can be built from typed world surfaces; private
    `_environment`, `_store`, `_active_graph`, `_lifting_system`, and `_policy`
    access preserved an implementation-detail dependency.
- `Any` serializer and boundary annotations in `propstore/world/atms.py`
  - Disposition: rewrite.
  - Owner after cleanup: ATMS typed reports own their runtime fields; JSON-like
    presentation dictionaries are object-valued only at the serialization
    boundary.
  - Action: replace `dict[str, Any]` return types with `dict[str, object]` and
    delete the `Any` import from the ATMS module.
- ATMS tests patching the old `propstore.world.WorldQuery` package barrel and
  inspecting private `BoundWorld` attributes
  - Disposition: rewrite.
  - Owner after cleanup: tests target the concrete `propstore.world.model`
    owner for monkeypatching and the public `BoundWorld` substrate properties
    for runtime assertions.

Gate results:
- Pass: `rg -n -F -- "Any" propstore/world/atms.py` returned zero hits.
- Pass: `rg -n -F -- "bound._" propstore/world/atms.py
  tests/test_atms_engine.py` returned zero hits.
- Pass: `rg -n -F -- "propstore.world.WorldQuery"
  tests/test_atms_engine.py propstore/world/atms.py` returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-atms-public-bound-surface-rerun tests/test_atms_engine.py
  tests/test_atms_max_iterations_anytime.py
  tests/remediation/phase_8_dos_anytime/test_T8_4_atms_build_termination_guard.py
  tests/test_worldline.py::TestWorldlineRunner tests/test_worldline_revision.py`
  returned `57 passed`.
- Log:
  `logs/test-runs/world-atms-public-bound-surface-rerun-20260522-044242.log`.

Commit:
- Use public ATMS bound surface.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/world/bound.py`.

## Iteration 34 - `propstore/world/bound.py`

Slice read:
- `propstore/world/bound.py`
- `propstore/support_revision/input_normalization.py`
- `propstore/worldline/interfaces.py`
- `propstore/worldline/revision_capture.py`
- value collection and ATMS concept why-out callers.

Surfaces:
- bound-local `_normalize_revision_targets`
  - Disposition: move.
  - Owner after cleanup: `propstore.support_revision.input_normalization`
    owns revision input and target normalization.
  - Action: add `RevisionInput` and `normalize_revision_targets` in the
    support-revision input owner; update `BoundWorld.contract` to call that
    owner directly; delete the bound-local helper.
  - Evidence: the helper normalized support-revision atoms inside the world
    runtime file, while `normalize_revision_input` already owns the atomic
    input parsing.
- bound-local `_conflicts_for_revision_atom`
  - Disposition: delete.
  - Owner after cleanup: no separate owner; `BoundWorld.revise` reads the
    requested atom id and lowers conflict values inline once.
  - Evidence: the helper had one production caller and only wrapped
    `conflicts.get(atom_id, ())`.
- `BoundWorld.why_concept_out` dict payload
  - Disposition: rewrite.
  - Owner after cleanup: `propstore.world.types.ATMSConceptWhyOutReport` owns
    the typed world-runtime report; `propstore.app.world_atms` adapts that
    report for presentation.
  - Action: add the typed report, return it from `BoundWorld`, and update the
    sole app caller to use attributes instead of dictionary keys.
- remaining bound-local `Any` annotations
  - Disposition: rewrite.
  - Owner after cleanup: object-valued boundary inputs where arbitrary JSON or
    environment values are still accepted; float-valued known-value maps where
    the value resolver only stores numeric values.
  - Action: replace bound `Any` annotations, update `WorldQuery.bind`,
    `OverlayWorld.collect_known_values`, `ClaimValueResolver` known-value
    signatures, and the worldline bound protocol.
- worldline revision capture optional atom/target pass-through
  - Disposition: rewrite.
  - Owner after cleanup: `revision_capture` enforces operation-required atom
    and contract target values before calling the typed bound protocol.

Gate results:
- Pass: `rg -n -F -- "Any" propstore/world/bound.py
  propstore/worldline/interfaces.py` returned zero hits.
- Pass: `rg -n -F -- "_normalize_revision_targets" propstore tests` returned
  zero hits.
- Pass: `rg -n -F -- "_conflicts_for_revision_atom" propstore tests` returned
  zero hits.
- Failed then fixed: initial `uv run pyright propstore` exposed stale
  worldline protocol, optional revision-capture atom/target, app dict access,
  and iterated conflict input types after deleting the bound-local loose
  surfaces.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Initial logged pytest selector was invalid and ran zero tests; corrected
  gates below were used.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-bound-typed-revision-targets-final-rerun
  tests/test_world_query.py::TestDerivedValue
  tests/test_world_query.py::TestOverlayWorld
  tests/test_world_query.py::TestConflictResolution
  tests/test_revision_operators.py tests/test_revision_properties.py
  tests/test_worldline_revision.py tests/test_capture_journal.py
  tests/test_atms_engine.py` returned `116 passed, 12 warnings`.
- Log:
  `logs/test-runs/world-bound-typed-revision-targets-final-rerun-20260522-045122.log`.

Commit:
- Type bound revision and ATMS reports.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/world/bridge.py`.

## Iteration 35 - `propstore/world/bridge.py`

Slice read:
- `propstore/world/bridge.py`
- `propstore/world/model.py`
- `propstore/world/journal_replay.py`
- journal projection and capture tests.

Surfaces:
- `propstore.world.bridge`
  - Disposition: delete.
  - Owner after cleanup: `propstore.world.journal_projection` owns
    journal-step projection from `TransitionJournal` state to `ClaimView`.
  - Action: move `at_journal_step` and `BeliefSpaceQuery` to the semantic
    journal projection owner, delete `bridge.py`, and update production/test
    imports.
  - Evidence: this was not compatibility behavior, but the bridge-named module
    preserved transition terminology instead of naming the actual semantic
    operation.
- bridge wording in journal projection docs/tests
  - Disposition: rewrite.
  - Owner after cleanup: journal projection terminology in
    `WorldQuery.at_journal_step`, `ClaimView`, heavy replay docs, and tests.
- `BeliefSpaceQuery.bind_for_view` `Any` binding values
  - Disposition: rewrite.
  - Owner after cleanup: object-valued journal scope bindings at the projection
    boundary.

Gate results:
- Pass: `rg -n -F -- "propstore.world.bridge" propstore tests` returned zero
  hits.
- Pass: `rg -n -F -- "from propstore.world.bridge" propstore tests` returned
  zero hits.
- Pass: `rg --files propstore/world | rg -n "bridge.py$"` returned zero hits.
- Pass: `rg -n -F -- "Any" propstore/world/journal_projection.py` returned
  zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-journal-projection-bridge-deletion
  tests/test_world_query_at_journal_step.py
  tests/test_world_query_at_journal_step_method.py tests/test_p_heavy.py
  tests/test_p_mara_gate.py tests/test_scope_policy.py
  tests/test_capture_journal.py` returned `28 passed`.
- Log:
  `logs/test-runs/world-journal-projection-bridge-deletion-20260522-045520.log`.

Commit:
- Rename journal bridge projection owner.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/world/consistency.py`.

## Iteration 36 - `propstore/world/consistency.py`

Slice read:
- `propstore/world/consistency.py`
- `propstore/world/bound.py`
- `propstore/conflict_detector/collectors.py`
- conflict detector and world consistency callers/tests.

Surfaces:
- duplicated world-to-conflict-detector concept registry projection
  - Disposition: consolidate.
  - Owner after cleanup: `propstore.world.conflict_projection` owns the
    projection from world concept/parameterization rows into the conflict
    detector registry inputs.
  - Action: add `concept_registry_for_world` and
    `conflict_detector_inputs_for_world`; update transitive consistency and
    bound conflict recomputation to use the shared projection; delete the
    duplicated registry loops from `consistency.py` and `bound.py`.
  - Evidence: both files assembled `parameterization_relationships` from
    concept and parameterization rows by hand.
- `WorldConsistencyReport` owner API
  - Disposition: keep.
  - Owner after cleanup: `propstore.world.consistency` owns the app-facing
    consistency report and delegates conflict-detector input projection to the
    shared world projection owner.
  - Evidence: the file has no `Any`, no compatibility branch, no fallback
    reader, and no source-local shape.

Gate results:
- Pass: `rg -n -F -- "conflict_detector_payload"
  propstore/world/bound.py propstore/world/consistency.py` returned zero hits.
- Pass: `rg -n -F -- "parameterization_relationships"
  propstore/world/bound.py propstore/world/consistency.py` returned zero hits.
- Failed then fixed: initial `uv run pyright propstore` exposed
  `ConceptCatalogStore` as the wrong narrowing surface for the new projection
  protocol.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Initial logged pytest selectors were invalid and ran zero tests; corrected
  gate below was used.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-consistency-conflict-projection-final
  tests/test_cli.py::TestWorldOwnerReports
  tests/test_world_query.py::TestBoundConflicts
  tests/test_world_query.py::TestConflictResolution
  tests/test_world_query.py::TestTransitiveConsistency
  tests/test_world_query.py::TestConflictsCaching
  tests/test_conflict_detector.py` returned `118 passed, 6 warnings`.
- Log:
  `logs/test-runs/world-consistency-conflict-projection-final-20260522-045944.log`.

Commit:
- Consolidate world conflict projection.

Next slice:
- Continue deterministic per-file cleanup-refactor review with
  `propstore/world/intervention.py`.

## Iteration 1 - `propstore/world/types.py::coerce_value_status`

Slice read:
- `propstore/world/types.py`
- `propstore/world/atms.py`
- `propstore/app/world_atms.py`
- current `coerce_value_status` callers from literal search.

Surfaces:
- `coerce_value_status`
  - Disposition: delete.
  - Owner after cleanup: `ValueStatus` enum at runtime; app/CLI boundaries call
    `ValueStatus(raw_string)` when parsing user input.
  - Action: remove the runtime coercer, require `ValueStatus` in world result
    dataclasses, and update runtime/app callers.
  - Evidence: current helper accepts `object`, stringifies it, and lets raw
    status strings cross runtime object construction.

Gate results:
- Pass: `rg -n -F -- "coerce_value_status" propstore tests` returned zero
  hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-value-status-cleanup tests/test_worldline.py tests/test_labelled_core.py
  tests/test_worldline_praf.py tests/test_praf_integration.py
  tests/test_resolution_helpers.py tests/test_worldline_result_boundaries.py`
  returned `105 passed`.
- Log: `logs/test-runs/world-value-status-cleanup-20260522-020128.log`.

Commit:
- `6bfd7eb8 Delete value status coercer`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 7 - `propstore/world/atms.py::_coerce_queryables`

Slice read:
- `propstore/world/atms.py`
- current `_coerce_queryables` callers from literal search.

Surfaces:
- `_coerce_queryables`
  - Disposition: rewrite.
  - Owner after cleanup: typed ATMS future-query enumeration receives
    `QueryableAssumption` values and deduplicates/filter already-active
    queryables through a named future-query operation.
  - Action: replace the misleading coercer surface with `_future_queryables`
    and remove adjacent `legacy` wording.
  - Evidence: the helper does not parse old shapes; it filters typed
    `QueryableAssumption` objects. The `coerce` name is the wrong surface and
    should not remain as a search hit.

Gate results:
- Pass: `rg -n -F -- "_coerce_queryables" propstore tests` returned
  zero hits.
- Pass: `rg -n -F -- "legacy anytime-ceiling" propstore/world/atms.py`
  returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-atms-queryable-name-cleanup tests/test_atms_engine.py` returned
  `39 passed`.
- Log: `logs/test-runs/world-atms-queryable-name-cleanup-20260522-022454.log`.

Commit:
- `987912a4 Rename ATMS future query helper`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 15 - remaining broad `normalize_` hits classification

Slice read:
- `propstore/world/atms.py`
- `propstore/world/bound.py`
- `propstore/world/types.py`
- `propstore/world/value_resolver.py`
- `propstore/worldline/revision_capture.py`
- current `normalize_` hits from literal search.

Surfaces:
- `normalize_revision_input` / `_normalize_revision_targets` /
  `_normalize_query_atom`
  - Disposition: keep.
  - Owner after cleanup: support-revision input parsing and worldline revision
    capture boundaries.
  - Evidence: these functions convert revision query documents or CLI-shaped
    revision atoms into revision-domain atoms at the revision boundary; they
    are not old-data compatibility paths.
- `_normalize_claim_id_set`
  - Disposition: keep.
  - Owner after cleanup: `BoundWorld` active-graph set materialization.
  - Evidence: this converts already-typed active graph claim-id sequences into
    lookup sets for runtime membership checks.
- `_normalize_override_values`
  - Disposition: keep.
  - Owner after cleanup: `BoundWorld` resolves override keys through the world
    concept index before value resolution.
  - Evidence: this is concept-key resolution, not payload coercion; value
    parsing was deleted in Iteration 10.
- `normalize_queryable_cel`
  - Disposition: keep.
  - Owner after cleanup: `QueryableAssumption.from_cel` string/CEL boundary.
  - Evidence: queryable policy/app strings are parsed into typed
    `QueryableAssumption` objects at the boundary; runtime methods now require
    those typed objects.
- `ATMSEngine._normalize_value` and `ClaimValueResolver._normalize_value`
  - Disposition: keep.
  - Owner after cleanup: numeric value canonicalization for equality,
    fingerprints, and algorithm/direct-value comparison.
  - Evidence: these do not parse old shapes or accept loose payloads; they
    canonicalize `int` to `float` for stable numeric semantics.

Gate results:
- Pass: `rg -n -F -- "coerce" propstore/world propstore/worldline` returned
  zero hits.
- Pass: `rg -n -F -- "fallback" propstore/world propstore/worldline`
  returned zero hits.
- Pass: `rg -n -F -- "legacy" propstore/world propstore/worldline` returned
  zero hits.
- Pass: `rg -n -F -- "from_payload" propstore/world propstore/worldline`
  returned zero hits.
- Remaining broad `normalize_` hits are classified above.

Commit:
- Record-only classification commit for this iteration.

Next slice:
- Run full package gates for the world/worldline cleanup batch.

## Iteration 16 - full-gate regression fixes

Slice read:
- `propstore/world/types.py`
- `propstore/world/value_resolver.py`
- `tests/test_argumentation_package_track_e.py`
- `tests/test_value_resolver_failure_reasons.py`
- `tests/test_world_query.py`
- `tests/test_worldline.py`
- `tests/test_worldline_hash_excludes_transient_errors.py`
- `tests/test_structured_projection.py`
- failed full-suite log.

Surfaces:
- `RenderPolicy.from_dict` backend/semantics parsing
  - Disposition: rewrite.
  - Owner after cleanup: `RenderPolicy.from_dict` is the IO/document boundary
    parser; direct `RenderPolicy` construction remains typed-only.
  - Action: keep enum construction at runtime and map bad serialized backend or
    semantics values to field-specific `ValueError` messages at the document
    boundary.
  - Evidence: full suite failed tests expecting `Unknown reasoning_backend`
    for invalid worldline policy documents.
- stale test imports and runtime string semantics
  - Disposition: delete/rewrite.
  - Owner after cleanup: `propstore.core.reasoning` owns semantics helper
    exposure; runtime tests construct `RenderPolicy` with
    `ArgumentationSemantics`.
  - Action: remove the deleted `propstore.world.types` helper import from the
    package track test and update direct policy construction tests to pass typed
    semantics.
  - Evidence: full suite failed during collection on
    `normalize_argumentation_semantics` imported from `propstore.world.types`,
    and direct runtime policy construction rejected raw string semantics.
- `_coerce_override_value` stale test call
  - Disposition: delete.
  - Owner after cleanup: `_numeric_override_value` rejects non-numeric override
    values; old string parsing is gone.
  - Action: update the old failure-reason test to assert typed non-numeric
    rejection without naming the deleted coercer.
  - Evidence: full suite failed because the stale test called the deleted
    helper directly.

Gate results:
- Fail: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-worldline-cleanup-full` returned `6 failed, 3507 passed, 4 skipped,
  30 warnings, 1 error`.
- Log: `logs/test-runs/world-worldline-cleanup-full-20260522-030204.log`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-worldline-full-failure-fixes
  tests/test_value_resolver_failure_reasons.py::test_non_numeric_override_value_raises
  tests/test_worldline_hash_excludes_transient_errors.py::test_ws_j_equivalent_argumentation_failures_have_same_content_hash
  tests/test_structured_projection.py::test_worldline_policy_rejects_removed_structured_projection_alias
  tests/test_world_query.py::TestSemanticCorePhase6HypotheticalDeltas::test_claim_graph_overlay_uses_delta_backed_conflicts
  tests/test_world_query.py::TestSemanticCorePhase6HypotheticalDeltas::test_praf_overlay_keeps_delta_conflicts_unresolved_without_priors
  tests/test_worldline.py::TestWorldlineDefinition::test_worldline_definition_rejects_unknown_reasoning_backend
  tests/test_argumentation_package_track_e.py::test_track_e_package_semantics_are_exposed_by_propstore`
  returned `7 passed`.
- Log: `logs/test-runs/world-worldline-full-failure-fixes-20260522-030930.log`.
- Pass: `rg -n -F -- "_coerce_override_value(" propstore tests` returned
  zero hits.
- Pass: `rg -n -F -- "from propstore.world.types import"
  tests/test_argumentation_package_track_e.py` returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.

Commit:
- `ffd656d1 Fix world cleanup gate regressions`

Next slice:
- Rerun full package gates for the world/worldline cleanup batch.

## Iteration 17 - final package gates

Slice read:
- `propstore/world`
- `propstore/worldline`
- `workstreams/world-worldline-cleanup-2026-05-22.md`

Surfaces:
- final `world/worldline` forbidden-surface gates
  - Disposition: keep.
  - Owner after cleanup: typed runtime world/worldline APIs and exact
    IO/document/app parsing boundaries.
  - Evidence: old helper/coercion/fallback/payload search gates are clean
    inside the world/worldline runtime slice; remaining broad `normalize_`
    hits were classified in Iteration 15.
- full package runtime gate
  - Disposition: keep.
  - Owner after cleanup: package-level tests prove the changed runtime and
    document boundaries work with the rest of propstore.
  - Evidence: full logged pytest rerun passed after the full-gate regression
    fix slice.

Gate results:
- Pass: `rg -n -F -- "coerce" propstore/world propstore/worldline` returned
  zero hits.
- Pass: `rg -n -F -- "fallback" propstore/world propstore/worldline`
  returned zero hits.
- Pass: `rg -n -F -- "legacy" propstore/world propstore/worldline` returned
  zero hits.
- Pass: `rg -n -F -- "from_payload" propstore/world propstore/worldline`
  returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-worldline-cleanup-full-rerun` returned `3518 passed, 4 skipped,
  30 warnings`.
- Log: `logs/test-runs/world-worldline-cleanup-full-rerun-20260522-031125.log`.

Commit:
- Record-only final gate commit for this iteration.

Next slice:
- `world/worldline` cleanup workstream fixed point reached for this slice.

## Iteration 14 - duplicated merge-operator normalization

Slice read:
- `propstore/world/types.py`
- `propstore/policies.py`
- `../assignment-selection/src/assignment_selection/model.py`
- current `merge_operator` and `_normalize_merge_operator_value` hits from
  literal search.

Surfaces:
- `propstore/world/types.py::_normalize_merge_operator_value`
- `propstore/policies.py::_normalize_merge_operator_value`
  - Disposition: delete.
  - Owner after cleanup: `assignment_selection.MergeOperator` is the single
    typed owner for merge operator values; policy/document boundaries parse
    strings into that enum.
  - Action: type `RenderPolicy.merge_operator` and `MergePolicy.operator` as
    `MergeOperator`, remove duplicate normalizers, and serialize enum values
    at dict boundaries.
  - Evidence: both helpers repeat the same value set already defined by the
    assignment-selection package.

Gate results:
- Pass: `rg -n -F -- "_normalize_merge_operator_value" propstore tests`
  returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Initial logged gate failed because one policy-governance property test still
  constructed `MergePolicy` with raw strings; the test now generates
  `MergeOperator` values.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-merge-operator-cleanup
  tests/test_assignment_selection_merge.py::TestRenderPolicyIntegration
  tests/test_policy_governance.py` returned `10 passed`.
- Log: `logs/test-runs/world-merge-operator-cleanup-20260522-025738.log`.

Commit:
- `4f9726dd Use typed merge operators`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 13 - `RenderPolicy` backend/semantics normalization

Slice read:
- `propstore/world/types.py`
- `propstore/app/rendering.py`
- `propstore/core/reasoning.py`
- current `normalize_reasoning_backend` and
  `normalize_argumentation_semantics` hits from literal search.

Surfaces:
- `RenderPolicy.__post_init__` accepting raw semantics/backend strings.
- `world.types` importing normalization helpers as part of the runtime policy
  surface.
  - Disposition: rewrite.
  - Owner after cleanup: `RenderPolicy` stores typed `ReasoningBackend` and
    `ArgumentationSemantics`; `RenderPolicy.from_dict` and app request parsing
    are the string boundaries.
  - Action: remove runtime normalization imports from `world.types`, parse
    document/app strings before construction, and require typed enum values in
    `RenderPolicy.__post_init__`.
  - Evidence: direct runtime policy construction should not preserve a
    stringly backend/semantics path.

Gate results:
- Pass: `rg -n -F -- "normalize_reasoning_backend" propstore/world
  propstore/worldline` returned zero hits.
- Pass: `rg -n -F -- "normalize_argumentation_semantics" propstore/world
  propstore/worldline` returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Initial logged gate selected an invalid test node and ran zero tests;
  corrected file-level gate below was used.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-render-policy-normalize-cleanup tests/test_render_contracts.py
  tests/test_app_rendering.py tests/test_render_policy_opinions.py` returned
  `29 passed`.
- Log: `logs/test-runs/world-render-policy-normalize-cleanup-20260522-025249.log`.

Commit:
- `4a1ba12d Require typed render policy enums`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 12 - `propstore/world/bound.py::conflict_claim_from_payload`

Slice read:
- `propstore/world/bound.py`
- `propstore/conflict_detector/collectors.py`
- `propstore/conflict_detector/models.py`
- `propstore/families/claims/declaration.py`
- current `from_payload` hits from literal search.

Surfaces:
- `world.bound` calling `conflict_claim_from_payload(active_claim.to_source_claim_payload())`
  - Disposition: rewrite.
  - Owner after cleanup: conflict detector owns typed `Claim` to
    `ConflictClaim` collection; world passes `Claim` objects and does not
    round-trip through loose source payload dictionaries.
  - Action: add `conflict_claim_from_claim` in the conflict detector owner and
    update world conflict revalidation to use it.
  - Evidence: `world.bound` already has typed `Claim` rows. Building a source
    payload inside the runtime path only to parse it back into
    `ConflictClaim` is duplicate IO-shape plumbing.

Gate results:
- Pass: `rg -n -F -- "from_payload" propstore/world propstore/worldline`
  returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Initial logged gate failed with an import cycle from a runtime import of the
  `Claim` family declaration; the collector was changed to use a type-only
  import and claim type values.
- A second logged gate selected invalid test nodes and ran zero tests;
  corrected gate below was used.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-conflict-claim-typed-cleanup
  tests/test_world_query.py::TestUnboundQueries::test_conflicts
  tests/test_world_query.py::TestHypothesisProperties::test_bound_conflicts_remain_structured
  tests/test_world_query.py::TestConflictsCaching::test_conflicts_cached
  tests/test_conflict_detector.py::TestConflictRegistryProjection::test_conflict_same_conditions_different_values`
  returned `4 passed`.
- Log: `logs/test-runs/world-conflict-claim-typed-cleanup-20260522-024740.log`.

Commit:
- `12d28516 Use typed conflict claims in world`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 11 - `fallback` wording in world runtime

Slice read:
- `propstore/world/atms.py`
- `propstore/world/resolution.py`
- current `fallback` hits from literal search.

Surfaces:
- `ATMSEngine._future_node_inspection(..., fallback=...)`
- resolution comment phrase `raw confidence fallback`
  - Disposition: rewrite.
  - Owner after cleanup: ATMS future inspection names the current graph node
    metadata as `current_node`; resolution comment names the confidence-derived
    score without fallback wording.
  - Action: remove `fallback` wording from production world modules.
  - Evidence: these hits are not old-data compatibility paths, but keeping the
    word defeats the search gate and obscures the actual semantics.

Gate results:
- Pass: `rg -n -F -- "fallback" propstore/world propstore/worldline`
  returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Two initial logged gates selected invalid test nodes and ran zero tests;
  corrected gate below was used.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-fallback-wording-cleanup
  tests/test_atms_engine.py::test_atms_future_queryables_can_activate_exact_support_without_fabricating_current_support
  tests/test_atms_engine.py::test_atms_why_out_distinguishes_missing_support_from_nogood_and_future_activation
  tests/test_render_policy_opinions.py::test_missing_opinion_ignores_raw_confidence`
  returned `3 passed`.
- Log: `logs/test-runs/world-fallback-wording-cleanup-20260522-024304.log`.

Commit:
- `05ec4e97 Remove world fallback wording`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 10 - `propstore/world/value_resolver.py::_coerce_override_value`

Slice read:
- `propstore/world/value_resolver.py`
- `propstore/world/bound.py`
- current `override_values` callers from literal search.

Surfaces:
- `_coerce_override_value`
  - Disposition: rewrite.
  - Owner after cleanup: derivation uses numeric override values that already
    crossed their IO/app boundary; string parsing is not owned by the runtime
    resolver.
  - Action: replace the coercer with a numeric override reader that accepts
    `int | float` values, rejects bool/string/object values, and keeps `None`
    as no override.
  - Evidence: formula evaluation needs numeric inputs; parsing strings with
    `float(...)` inside the resolver silently preserves a loose payload path.

Gate results:
- Pass: `rg -n -F -- "coerce" propstore/world propstore/worldline`
  returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-override-value-cleanup tests/test_world_query.py::TestDerivedValue
  tests/test_labelled_core.py::test_derived_value_combines_input_labels`
  returned `10 passed`.
- Log: `logs/test-runs/world-override-value-cleanup-20260522-024009.log`.

Commit:
- `19510167 Delete override value coercer`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 9 - `propstore/world/types.py::DerivedResult.exactness`

Slice read:
- `propstore/world/types.py`
- `propstore/world/value_resolver.py`
- `propstore/core/exactness_types.py`
- current `coerce_exactness` callers from literal search.

Surfaces:
- `DerivedResult.__post_init__` exactness coercion.
  - Disposition: rewrite.
  - Owner after cleanup: `DerivedResult` receives `Exactness | None`;
    `ClaimValueResolver` parses the string stored on the `Parameterization`
    row while translating the row into a runtime result.
  - Action: remove the `coerce_exactness` import/use from `world.types` and
    construct typed exactness at the parameterization-row boundary.
  - Evidence: `DerivedResult` is a runtime result object; row strings should
    not be accepted by its constructor.

Gate results:
- Pass: `rg -n -F -- "coerce_exactness" propstore/world propstore/worldline`
  returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Initial logged gate selected a non-existent worldline test node and ran zero
  tests; corrected gate below was used.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-derived-exactness-cleanup
  tests/test_labelled_core.py::test_derived_value_combines_input_labels
  tests/test_world_query.py::TestDerivedValue
  tests/test_worldline.py::TestWorldlineRunner::test_derived_value_accuracy`
  returned `10 passed`.
- Log: `logs/test-runs/world-derived-exactness-cleanup-20260522-023715.log`.

Commit:
- `100f8bd2 Require typed derived exactness`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 8 - `propstore/world/types.py::coerce_queryable_assumptions`

Slice read:
- `propstore/world/types.py`
- `propstore/world/bound.py`
- `propstore/worldline/argumentation.py`
- `propstore/app/world_atms.py`
- `propstore/fragility_contributors.py`
- `propstore/families/documents/worldlines.py`
- `tests/test_atms_engine.py`
- current `coerce_queryable_assumptions`, `QueryableInput`, and
  `future_queryables` callers from literal search.

Surfaces:
- `coerce_queryable_assumptions`
- `QueryableInput`
  - Disposition: delete.
  - Owner after cleanup: runtime APIs receive `QueryableAssumption` objects;
    serialized policy/app request strings are parsed at the IO/app boundary.
  - Action: remove the object/string coercer and mixed input alias, type
    `RenderPolicy.future_queryables` and `BoundWorld` queryable APIs as
    `QueryableAssumption`, and parse document/app queryable strings with
    `QueryableAssumption.from_cel`.
  - Evidence: ATMS already requires `Sequence[QueryableAssumption]`; the
    helper only preserves a raw string path through bound runtime methods and
    worldline argumentation capture.

Gate results:
- Pass: `rg -n -F -- "coerce_queryable_assumptions" propstore tests`
  returned zero hits.
- Pass: `rg -n -F -- "QueryableInput" propstore tests` returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Initial logged gate failed because two ATMS tests still called runtime
  methods with raw string queryables.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-queryable-assumption-cleanup tests/test_atms_engine.py
  tests/test_render_contracts.py tests/test_fragility.py` returned
  `79 passed`.
- Log: `logs/test-runs/world-queryable-assumption-cleanup-20260522-023353.log`.

Commit:
- `bf846a23 Delete queryable assumption coercer`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 6 - `propstore/world/atms.py::_coerce_environment_key`

Slice read:
- `propstore/world/atms.py`
- `propstore/world/bound.py`
- current environment-key callers from literal search.

Surfaces:
- `_coerce_environment_key`
  - Disposition: delete.
  - Owner after cleanup: ATMS environment APIs require typed `EnvironmentKey`;
    callers construct keys at their boundary.
  - Action: narrow ATMS and bound-world method signatures and remove
    tuple/list conversion.
  - Evidence: tests and current callers already pass `EnvironmentKey`; the
    tuple/list path is a helper-shaped alternate runtime representation.

Gate results:
- Pass: `rg -n -F -- "_coerce_environment_key" propstore tests` returned
  zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings` after
  moving the remaining tuple-to-`EnvironmentKey` conversion to
  `propstore/app/world_atms.py`.
- Initial logged gate selected a non-existent test class and ran zero tests;
  corrected gate below was used.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-atms-environment-key-cleanup tests/test_atms_engine.py
  tests/test_atms_environment_context_serialisation.py` returned `40 passed`.
- Log: `logs/test-runs/world-atms-environment-key-cleanup-20260522-022228.log`.

Commit:
- `db8507f8 Delete ATMS environment key coercer`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 5 - `propstore/world/resolution.py::_coerce_resolution_claim`

Slice read:
- `propstore/world/resolution.py`
- current `_coerce_resolution_claim` callers from literal search.

Surfaces:
- `_coerce_resolution_claim`
  - Disposition: delete.
  - Owner after cleanup: `resolve()` constructs `_ResolutionClaimView` once at
    the resolution boundary; internal helper functions receive only typed
    views.
  - Action: remove union parameters and generator coercion inside resolution
    helpers.
  - Evidence: `resolve()` already computes `active_views` and
    `active_claim_views`; the helper preserves a mixed `Claim |
    _ResolutionClaimView` path inside runtime resolution.

Gate results:
- Pass: `rg -n -F -- "_coerce_resolution_claim" propstore tests`
  returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Initial logged gate failed because direct private-helper tests still passed
  `Claim` rows; tests were updated to construct `_ResolutionClaimView`
  explicitly.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-resolution-claim-view-cleanup tests/test_resolution_helpers.py
  tests/test_praf_integration.py tests/test_world_query.py::TestConflictResolution
  tests/test_semantic_repairs.py` returned `59 passed`.
- Log: `logs/test-runs/world-resolution-claim-view-cleanup-20260522-021716.log`.

Commit:
- `142ff9ab Delete resolution claim coercer`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 4 - `propstore/worldline/result_types.py::_coerce_variable_refs`

Slice read:
- `propstore/worldline/result_types.py`
- current `_coerce_variable_refs` callers from literal search.

Surfaces:
- `_coerce_variable_refs`
  - Disposition: delete.
  - Owner after cleanup: `WorldlineTargetValue.from_json_payload`, the exact IO
    boundary that owns parsing serialized variable references.
  - Action: inline the variable-reference payload parser into
    `WorldlineTargetValue.from_json_payload`; keep hard failures for wrong
    variable shapes.
  - Evidence: there is one caller, and a private coercer helper creates a
    reusable-looking surface for a single field parser.

Gate results:
- Pass: `rg -n -F -- "_coerce_variable_refs" propstore tests` returned
  zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-variable-ref-cleanup tests/test_worldline_result_boundaries.py
  tests/test_worldline.py::TestWorldlineDefinition::test_worldline_result_from_yaml`
  returned `7 passed`.
- Log: `logs/test-runs/worldline-variable-ref-cleanup-20260522-021151.log`.

Commit:
- `533db62f Delete worldline variable ref coercer`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 3 - `WorldlineResult` value/step coercers

Slice read:
- `propstore/worldline/result_types.py`
- `propstore/worldline/definition.py`
- current `WorldlineResult(` construction sites from literal search.

Surfaces:
- `coerce_worldline_target_value`
- `coerce_worldline_step`
  - Disposition: delete.
  - Owner after cleanup: `WorldlineResult.from_document` and
    `WorldlineResult.from_dict` parse serialized mappings; direct
    `WorldlineResult` construction receives typed `WorldlineTargetValue` and
    `WorldlineStep` objects.
  - Action: remove the coercers and make runtime construction reject mapping
    values/steps.
  - Evidence: `WorldlineResult.__post_init__` currently accepts mapping payloads
    and converts them, duplicating the existing explicit IO constructors.

Gate results:
- Pass: `rg -n -F -- "coerce_worldline_target_value" propstore tests`
  returned zero hits.
- Pass: `rg -n -F -- "coerce_worldline_step" propstore tests` returned
  zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-result-coercer-cleanup tests/test_worldline.py
  tests/test_worldline_result_boundaries.py tests/test_capture_journal.py
  tests/test_worldline_revision.py` returned `75 passed`.
- Log: `logs/test-runs/worldline-result-coercer-cleanup-20260522-020908.log`.

Commit:
- `8b786db4 Delete worldline result coercers`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 2 - `propstore/worldline/result_types.py::coerce_worldline_capture_error`

Slice read:
- `propstore/worldline/result_types.py`
- `propstore/worldline/revision_types.py`
- current `coerce_worldline_capture_error` callers from literal search.

Surfaces:
- `coerce_worldline_capture_error`
  - Disposition: delete.
  - Owner after cleanup: `WorldlineCaptureError` enum in runtime objects;
    `from_json_payload` methods parse serialized strings at the worldline IO
    boundary.
  - Action: remove the coercer, require typed enum values in dataclass
    construction, and parse raw payload strings only inside JSON payload
    readers.
  - Evidence: the helper accepts strings through runtime `__post_init__`
    paths, preserving a coercion surface beyond the IO boundary.

Gate results:
- Pass: `rg -n -F -- "coerce_worldline_capture_error" propstore tests`
  returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-capture-error-cleanup tests/test_worldline_error_visibility.py
  tests/test_worldline_hash_excludes_transient_errors.py
  tests/test_worldline_revision.py tests/test_worldline_revision_event_capture.py
  tests/test_worldline_result_boundaries.py tests/test_capture_journal.py`
  returned `27 passed`.
- Log: `logs/test-runs/worldline-capture-error-cleanup-20260522-020548.log`.

Commit:
- `777ea1c6 Delete worldline capture error coercer`

Next slice:
- Continue world/worldline fixed-point search after this gate.
