# Value Resolver Domain Model Cleanup Workstream - 2026-05-24

## Purpose

Move claim-local and parameterization-local value semantics out of
`propstore.world.value_resolver` and onto the owning domain models/types.

This is a deletion-first cleanup. The resolver remains the world-level
orchestrator for active claim sets, recursive lookup, parameterization
compatibility, overrides, and algorithm equivalence under current known values.
It must not keep private DTOs, helper views, or model-local field extraction.

## Governing Principles

- Domain facts live on the domain model that owns them.
- The resolver orchestrates world-specific lookup and comparison; it does not
  reinterpret `Claim` and `Parameterization` fields through private helper
  models.
- No wrappers, adapters, compatibility aliases, fallback readers, or renamed
  helpers replace deleted resolver-private surfaces.
- No duplicate field-name lists or hand-written DTOs restate family model
  fields in `propstore.world.value_resolver`.
- Runtime APIs receive typed domain objects past the IO boundary.
- Dicts and decoded payloads remain at document/IO boundaries.

## Current Evidence

Current `propstore.world.value_resolver` surfaces:

- `_ClaimValueView`: private resolver DTO over `Claim`.
- `_claim_value`: resolver-local claim numeric/string value extraction.
- `_claim_value_view`: resolver-local conversion from `Claim` to the private
  DTO.
- `_parameterization_concept_ids`: resolver-local JSON parsing of
  `Parameterization.concept_ids`.
- `ClaimValueResolver._normalize_value`: resolver-local canonical equality key
  for numeric values.
- `ClaimValueResolver._numeric_override_value`: resolver-local override
  validation that depends on world-level override mapping.
- `ClaimValueResolver`: world-level orchestration surface.
- `collect_known_values`: shared world-level helper currently using
  resolver-local claim value extraction.

Existing domain owners:

- `propstore.families.claims.declaration.Claim` already owns algorithm variable
  parsing through `variables`, `variable_bindings()`, and
  `variable_concept_ids()`.
- `Claim` already exposes `numeric_payload` and `algorithm_payload` through the
  family model.
- `propstore.families.concepts.declaration.Parameterization` already owns
  `concept_ids`, `formula`, `sympy`, `exactness`, and condition payload fields.
- `propstore.world.types` owns `ValueResult`, `DerivedResult`, `ValueStatus`,
  and value-result failure reasons.

## Target Architecture

- `Claim` owns claim-local value semantics:
  - `Claim.value_resolution_value -> float | str | None`
  - `Claim.algorithm_body -> str | None`
  - `Claim.is_algorithm_claim -> bool`
- `Parameterization` owns parameterization-local typed fields:
  - `Parameterization.input_concept_ids -> tuple[ConceptId, ...]`
  - `Parameterization.exactness_value -> Exactness | None`
- `propstore.world.types` owns canonical world-value equality:
  - `canonical_value_key(value: float | str | None) -> float | str | None`
- `ClaimValueResolver` owns only world-level orchestration:
  - selecting active claims;
  - invoking `value_of`;
  - checking parameterization compatibility;
  - applying override mappings;
  - resolving known values for algorithm equivalence;
  - mapping comparison outcomes into `ValueResult` and `DerivedResult`.

## Forbidden Surfaces

These production symbols must be deleted, not renamed:

- `_ClaimValueView`
- `_claim_value`
- `_claim_value_view`
- `_parameterization_concept_ids`
- `ClaimValueResolver._normalize_value`

These patterns must not be introduced:

- a replacement private resolver DTO for `Claim`;
- a resolver helper that restates claim field extraction;
- a resolver helper that parses `Parameterization.concept_ids`;
- a compatibility alias for any deleted symbol;
- a broad `object` or `Any` value path in the resolver;
- a `from_payload`, `coerce`, `normalize`, `legacy`, or `fallback` helper in the
  resolver;
- test imports of resolver-private claim view/extraction helpers.

## Ordered Execution

### Phase 0 - Baseline

Read:

- `propstore/world/value_resolver.py`
- `propstore/world/types.py`
- `propstore/families/claims/declaration.py`
- `propstore/families/concepts/declaration.py`
- `propstore/world/bound.py`
- `tests/test_value_resolver_failure_reasons.py`
- `tests/test_value_resolver_consensus_with_abstention.py`
- `tests/test_semantic_repairs.py`
- `tests/test_world_query.py`
- `tests/test_labelled_core.py`
- `tests/test_worldline.py`

Run baseline gates:

- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label value-resolver-domain-baseline tests/test_world_query.py::TestDerivedValue tests/test_world_query.py::TestAlgorithmWorldQuery tests/test_value_resolver_failure_reasons.py tests/test_value_resolver_consensus_with_abstention.py tests/test_semantic_repairs.py tests/test_labelled_core.py tests/test_worldline.py::TestWorldlineRunner::test_derived_value_accuracy`

Phase 0 execution evidence, 2026-05-24:

- Read the named resolver/domain/test surfaces for Phase 0.
- `uv run pyright propstore` failed before any value-resolver edits with 49
  errors outside the owned scope, including unresolved
  `propstore.derived_build` imports and optional-derived-store errors in
  `propstore/world/model.py`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label value-resolver-domain-baseline tests/test_world_query.py::TestDerivedValue tests/test_world_query.py::TestAlgorithmWorldQuery tests/test_value_resolver_failure_reasons.py tests/test_value_resolver_consensus_with_abstention.py tests/test_semantic_repairs.py tests/test_labelled_core.py tests/test_worldline.py::TestWorldlineRunner::test_derived_value_accuracy`
  failed during collection with
  `ModuleNotFoundError: No module named 'propstore.derived_build'`.
- Local evidence for the baseline blocker: `git status --short -- logs
  propstore tests workstreams reports` showed tracked deletions
  `D  propstore/derived_build.py` and
  `D  propstore/derived_build_plan.py`, which are outside this workstream's
  owned scope.
- No implementation phase started. Phase 1 remains unchecked because Phase 0
  required gates are blocked by the unrelated shared-worktree deletions above.

### Phase 1 - Move Claim-Local Value Semantics To `Claim`

Delete first:

- `_ClaimValueView`
- `_claim_value`
- `_claim_value_view`

Add the domain-owned methods/properties to `Claim`:

- `value_resolution_value`
- `algorithm_body`
- `is_algorithm_claim`

Update resolver and tests to use those `Claim` APIs directly.

Required search gates:

- `rg -n -F -- "_ClaimValueView" propstore tests`
- `rg -n -F -- "_claim_value(" propstore tests`
- `rg -n -F -- "_claim_value_view" propstore tests`
- `rg -n -F -- "from propstore.world.value_resolver import ClaimValueResolver, _claim_value_view" tests`

All four gates must return zero hits.

Runtime gates:

- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label value-resolver-claim-domain tests/test_value_resolver_failure_reasons.py tests/test_value_resolver_consensus_with_abstention.py tests/test_semantic_repairs.py tests/test_world_query.py::TestAlgorithmWorldQuery`

Commit this phase before Phase 2.

### Phase 2 - Move Parameterization-Local Parsing To `Parameterization`

Delete first:

- `_parameterization_concept_ids`

Add the domain-owned methods/properties to `Parameterization`:

- `input_concept_ids`
- `exactness_value`

Update `ClaimValueResolver` to call those domain APIs directly.

Required search gates:

- `rg -n -F -- "_parameterization_concept_ids" propstore tests`
- `rg -n -F -- "json.loads(param.concept_ids)" propstore/world/value_resolver.py`
- `rg -n -F -- "Exactness(str(param.exactness))" propstore/world/value_resolver.py`

All three gates must return zero hits.

Runtime gates:

- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label value-resolver-parameterization-domain tests/test_world_query.py::TestDerivedValue tests/test_labelled_core.py tests/test_worldline.py::TestWorldlineRunner::test_derived_value_accuracy tests/test_semantic_repairs.py`

Commit this phase before Phase 3.

### Phase 3 - Move Canonical Value Equality To `world.types`

Delete first:

- `ClaimValueResolver._normalize_value`

Add:

- `canonical_value_key(value: float | str | None) -> float | str | None` in
  `propstore.world.types`.

Update resolver code to use `canonical_value_key`.

Required search gates:

- `rg -n -F -- "_normalize_value" propstore tests`
- `rg -n -F -- "canonical_value_key" propstore/world/value_resolver.py propstore/world/types.py tests`

The first gate must return zero hits. The second gate must show the single
owner in `world.types` and resolver call sites only.

Runtime gates:

- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label value-resolver-canonical-value-key tests/test_world_query.py::TestDerivedValue tests/test_value_resolver_failure_reasons.py tests/test_value_resolver_consensus_with_abstention.py tests/test_render_contracts.py`

Commit this phase before Phase 4.

### Phase 4 - Keep Resolver As Orchestrator Only

Read the final `propstore/world/value_resolver.py` and classify every remaining
private symbol.

Required final disposition:

- `_AlgorithmComparison`: keep as the typed outcome of `ast_equiv` comparison.
- `_comparison_from_equivalence`: keep only as the local adapter from
  `ast_equiv` result object to `_AlgorithmComparison`.
- `_numeric_override_value`: keep in resolver because override maps are
  world-level call parameters, not claim or parameterization fields.
- `_algorithm_matches_direct_value`: keep in resolver because it combines
  current known values, active claim context, and `ast_equiv`.
- `_all_algorithms_equivalent`: keep in resolver because it compares active
  algorithm claims under current known values.
- `_constant_algorithm_body`: keep as resolver-local input to direct-value
  algorithm comparison.

Required search gates:

- `rg -n -F -- "Any" propstore/world/value_resolver.py`
- `rg -n -F -- "object" propstore/world/value_resolver.py`
- `rg -n -F -- "coerce" propstore/world/value_resolver.py`
- `rg -n -F -- "normalize" propstore/world/value_resolver.py`
- `rg -n -F -- "from_payload" propstore/world/value_resolver.py`
- `rg -n -F -- "fallback" propstore/world/value_resolver.py`
- `rg -n -F -- "legacy" propstore/world/value_resolver.py`

All gates must return zero hits except documented occurrences in comments from
the current phase must be removed before completion.

Runtime gates:

- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label value-resolver-orchestrator-final tests/test_world_query.py::TestDerivedValue tests/test_world_query.py::TestAlgorithmWorldQuery tests/test_value_resolver_failure_reasons.py tests/test_value_resolver_consensus_with_abstention.py tests/test_semantic_repairs.py tests/test_labelled_core.py tests/test_worldline.py::TestWorldlineRunner::test_derived_value_accuracy`

Commit this phase before final gates.

### Phase 5 - Final Gates

Run:

- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label value-resolver-domain-final tests/test_world_query.py::TestDerivedValue tests/test_world_query.py::TestAlgorithmWorldQuery tests/test_value_resolver_failure_reasons.py tests/test_value_resolver_consensus_with_abstention.py tests/test_semantic_repairs.py tests/test_labelled_core.py tests/test_worldline.py::TestWorldlineRunner::test_derived_value_accuracy`

Run full package gate:

- `powershell -File scripts/run_logged_pytest.ps1 -Label value-resolver-domain-full`

Final search gates:

- `rg -n -F -- "_ClaimValueView" propstore tests`
- `rg -n -F -- "_claim_value(" propstore tests`
- `rg -n -F -- "_claim_value_view" propstore tests`
- `rg -n -F -- "_parameterization_concept_ids" propstore tests`
- `rg -n -F -- "_normalize_value" propstore tests`
- `rg -n -F -- "Any" propstore/world/value_resolver.py`
- `rg -n -F -- "coerce" propstore/world/value_resolver.py`
- `rg -n -F -- "from_payload" propstore/world/value_resolver.py`

All final search gates must return zero hits.

## Completion State

This workstream is complete only when:

- deleted resolver-private surfaces have zero literal hits in production and
  tests;
- claim-local value semantics live on `Claim`;
- parameterization-local typed parsing lives on `Parameterization`;
- canonical value equality lives in `propstore.world.types`;
- `ClaimValueResolver` contains only world-level orchestration and algorithm
  comparison under current known values;
- targeted gates, pyright, and full logged pytest pass;
- every phase is committed and this workstream records the final evidence.
