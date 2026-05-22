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
- Pending.

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
