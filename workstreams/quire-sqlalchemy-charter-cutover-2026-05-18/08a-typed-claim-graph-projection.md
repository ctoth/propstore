# 08a - Typed Claim To Graph Projection Workstream

Date: 2026-05-20

## Refactor Zen

This workstream succeeds only if claim graph projection has one typed owner and
the project shrinks. Field and schema shape is written once in Quire charters
or in the exact Propstore semantic owner. Do not restate claim payload,
condition, source, identity, or concept-link shape in overlay helpers, graph
helpers, kwargs builders, row DTOs, normalizers, compatibility aliases, or
test stores. After IO parsing, the type system carries meaning. Delete old
production hardcoding first, then use type, test, and search failures as the
work queue.

## Goal

Replace scattered claim-to-graph field projection with one typed claim graph
projection owned by the claim/graph boundary.

End state:

- Real claims and synthetic overlay claims lower to `ClaimNode` through the
  same typed projection path.
- Claim graph projection reads typed `Claim` fields and Quire-declared
  relationships: `Claim.id`, `Claim.type`, `Claim.numeric_payload`,
  `Claim.text_payload`, `Claim.algorithm_payload`, `Claim.concept_links`,
  `Claim.source_assertions`, and source/provenance fields.
- `OverlayWorld` does not mutate `ClaimNode.attributes` with hardcoded claim
  payload keys such as `conditions_cel` or `sample_size`.
- `ClaimNode.attributes` is not a second claim payload schema. Any remaining
  attributes are graph-only metadata that is not already represented as typed
  `ClaimNode` fields or typed payload relationships.
- Synthetic overlays preserve existing semantics by constructing typed claim
  models/payloads/links, then using the same projection path as persisted
  claims.

## Prerequisites

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`, `03-quire-fts-vector.md`,
`04-propstore-build-orchestration.md`, `05-source-and-diagnostics.md`,
`06-forms-concepts-parameterizations.md`, `07-contexts-lifting.md`,
`08-claims-active-claims.md`.

This workstream is part of Phase 10 and must complete before Phase 10 can be
closed. It may touch Phase 14 world/graph callers only to delete duplicate
claim-field projection and route those callers through the typed owner.

## Deletion Targets

Delete these production hardcodings first:

- `propstore/world/overlay.py::_claim_node_for_synthetic` mutation of
  `attributes["conditions_cel"]`;
- `propstore/world/overlay.py::_claim_node_for_synthetic` mutation of
  `attributes["sample_size"]`;
- any overlay-local list of claim payload fields;
- any graph-builder-local duplicate list of claim payload fields once the
  typed projection owner exists.

Do not replace them with a renamed helper, a generic-looking wrapper around the
same hardcoded keys, or a compatibility fallback.

## Required Implementation Shape

1. Create or move one production function at the claim/graph boundary that
   lowers a typed `Claim` plus concept-link/payload/source/provenance
   relationships to `ClaimNode`.
2. Make `propstore/core/graph_build.py` use that projection for persisted
   claims.
3. Make `propstore/world/overlay.py` construct typed synthetic claim objects
   and call the same projection.
4. If `ClaimNode` lacks typed fields needed by graph/runtime consumers, add
   typed fields to `ClaimNode` and update every caller. Do not hide those
   fields in `attributes`.
5. Keep IO-boundary tests and fixtures separate from runtime typed claim
   projection. Runtime tests must not use dict-shaped claims as substitutes for
   typed claim models.

## Search Gates

These searches must pass before completion:

```powershell
rg -n -F -- 'attributes["conditions_cel"]' propstore tests
rg -n -F -- 'attributes["sample_size"]' propstore tests
rg -n -F -- "conditions_cel" propstore/world/overlay.py propstore/core/graph_build.py
rg -n -F -- "sample_size" propstore/world/overlay.py propstore/core/graph_build.py
rg -n -F -- "ClaimNode(" propstore/core propstore/world tests/test_world_query.py
```

Allowed remaining hits:

- `conditions_cel` and `sample_size` may remain in charter declarations,
  typed payload models, IO-boundary fixtures, and tests explicitly exercising
  storage schema.
- `conditions_cel` may remain in `propstore/world/overlay.py` and
  `propstore/core/graph_build.py` only for parameterization condition fields,
  not for claim projection.
- `ClaimNode(` may remain only where the caller is the single typed projection
  owner or where the test is directly testing `ClaimNode` itself.

## Verification Gates

Run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label typed-claim-graph-projection tests/test_world_query.py::TestSemanticCorePhase6HypotheticalDeltas tests/test_world_query.py::TestWorldQueryConstruction::test_construct_from_repo tests/test_world_query.py::TestUnboundQueries::test_get_claim tests/test_world_query.py::TestUnboundQueries::test_claims_for tests/test_world_query.py::TestConflictResolution::test_resolve_sample_size
powershell -File scripts/run_logged_pytest.ps1 -Label claim-charter-phase10-gate tests/test_world_query.py tests/test_resolution_helpers.py tests/test_render_policy_filtering.py
```

If a gate exposes a missing generic Quire capability, stop and add it in Quire
first. If a gate exposes another duplicate claim-field projection, delete that
projection rather than normalizing around it.

## Completion Criteria

- All deletion targets are gone.
- Persisted and synthetic claims share one typed projection path.
- Phase 6 overlay identity/inverse tests pass without accepting duplicate
  `attributes` shape.
- Search gates pass with only the allowed IO/schema/test exceptions above.
- Verification gates pass or record an exact blocker in this file.

## Execution Record

- Created 2026-05-20 after Phase 6 overlay verification exposed duplicate
  hardcoded projection of `conditions_cel` and `sample_size` in
  `propstore/world/overlay.py`.
- Executed 2026-05-20. `propstore/families/claims/graph.py` now owns typed
  `Claim` to `ClaimNode` projection and typed synthetic-claim lowering.
  `propstore/core/graph_build.py`, `propstore/core/analyzers.py`, and
  `propstore/world/overlay.py` route through that owner. `ClaimNode` now has
  typed fields for claim context, source, and numeric payload evidence instead
  of requiring those values in `attributes`.
- Deleted the overlay-local mutations of `attributes["conditions_cel"]` and
  `attributes["sample_size"]`. `rg -n -F -- 'attributes["conditions_cel"]'
  propstore tests` and `rg -n -F -- 'attributes["sample_size"]' propstore
  tests` returned no hits. `rg -n -F -- "sample_size"
  propstore/world/overlay.py propstore/core/graph_build.py` returned no hits.
  `rg -n -F -- "ClaimNode(" propstore/core propstore/world
  tests/test_world_query.py` returns only `propstore/world/atms.py`'s
  `ATMSClaimNode` construction, not a `ClaimNode` projection.
- Remaining `conditions_cel` hits in `propstore/world/overlay.py` and
  `propstore/core/graph_build.py` are parameterization condition handling:
  `_ParameterizationCatalogAdapter` and parameterization graph edges. They are
  outside this claim-projection deletion target.
- Verification passed: `uv run pyright propstore` reported 0 errors, and
  logged pytest `powershell -File scripts/run_logged_pytest.ps1 -Label
  typed-claim-graph-projection tests/test_world_query.py::TestSemanticCorePhase6HypotheticalDeltas
  tests/test_world_query.py::TestWorldQueryConstruction::test_construct_from_repo
  tests/test_world_query.py::TestUnboundQueries::test_get_claim
  tests/test_world_query.py::TestUnboundQueries::test_claims_for
  tests/test_world_query.py::TestConflictResolution::test_resolve_sample_size`
  passed with 8 tests and log
  `logs\test-runs\typed-claim-graph-projection-20260520-211640.log`.
- Phase 10 broad gate failed on 2026-05-20:
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  claim-charter-phase10-gate tests/test_world_query.py
  tests/test_resolution_helpers.py tests/test_render_policy_filtering.py`
  produced 4 failures and 169 passes in
  `logs\test-runs\claim-charter-phase10-gate-20260520-211829.log`.
  Two failures are stale test assertions against the deleted `Claim.value`
  surface. Two failures show `OverlayWorld(remove=[...])` does not resolve
  claim logical ids such as `algo_claim3` before computing semantic and graph
  removals.
- Required repair: remove the nonexistent/private `_store.resolve_claim`
  expectation from overlay construction. Claim lookup by id, primary logical
  id, and logical id belongs to the generic world query surface backed by the
  typed `claim_core` table, not to an overlay shim or claim-specific string
  rewrite in `OverlayWorld`.
