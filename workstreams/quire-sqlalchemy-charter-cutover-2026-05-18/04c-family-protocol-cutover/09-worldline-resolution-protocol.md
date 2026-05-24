# 09 Worldline Resolution Protocol

## Prerequisites

- `01-deleted-file-fallout-repair.md`
- `02-quire-generated-family-protocols.md`
- `03-generic-family-lookup-cleanup.md`
- `04-family-document-deletion.md`
- `05-registry-contracts-batch-specs.md`
- `06-source-lifecycle-state-machines.md`
- `07-proposal-lifecycle-state-machines.md`
- `08-artifact-graph-verification-export.md`

## Target

Worldline resolution records typed world/family results. It does not own claim
field extraction, display lookup, target/input resolution, derived input
tracing, conflict resolution, or result document shape.

## Deletion Targets

- resolver-chain helper family in `propstore/worldline/resolution.py`
- duplicate `_claim_value` implementations across world and worldline modules
- claim display/value/variable extraction inside worldline code
- concept display extraction inside worldline code
- derived input tracing duplicated outside `ClaimValueResolver` or generic
  parameterization graph protocol
- handwritten worldline document structs in
  `propstore/families/documents/worldlines.py`
- worldline document class paths in registry and contracts

## Kept Behavior

- `propstore/world/resolution.py::resolve`
- `propstore/world/value_resolver.py::ClaimValueResolver`, after scalar
  semantics are owned by typed claim/family behavior
- `propstore/worldline/runner.py::run_worldline`
- `propstore/worldline/argumentation.py::capture_argumentation_state`
- `propstore/worldline/hashing.py::compute_worldline_content_hash`, rehomed as
  worldline artifact/content-hash policy when needed
- typed boundary result objects in `result_types.py` and `revision_types.py`

## Execution

1. Delete worldline resolver-chain helpers first.
2. Move claim scalar/display/variable semantics onto claim family/model
   behavior.
3. Move concept display semantics onto concept family/model behavior.
4. Let value resolver or generic graph protocol supply typed derivation trees.
5. Replace worldline result document classes with generated worldline family
   documents after Quire generated documents exist.
6. Verify worldline hash includes only declared artifact fields and declared
   dependency edges.

## Search Gates

```powershell
rg -n -F -- "propstore.worldline.resolution" propstore tests
rg -n -F -- "_resolve_claim_target" propstore/worldline propstore tests
rg -n -F -- "_resolve_claim_input" propstore/worldline propstore tests
rg -n -F -- "def _claim_value" propstore/world propstore/worldline tests
rg -n -F -- "WorldlineDefinitionDocument" propstore tests
rg -n -F -- "propstore.families.documents.worldlines" propstore tests
```

## Gates

```powershell
uv run pyright propstore/world/model.py propstore/world/resolution.py propstore/world/value_resolver.py propstore/worldline/runner.py propstore/worldline/definition.py propstore/worldline/result_types.py propstore/worldline/revision_types.py propstore/worldline/argumentation.py
powershell -File scripts/run_logged_pytest.ps1 -Label worldline-resolution-protocol tests/test_worldline.py tests/test_worldline_result_boundaries.py tests/test_worldline_error_visibility.py tests/test_worldline_hash_excludes_transient_errors.py tests/test_worldline_revision.py tests/test_world_query.py
```

## Completion

- Worldline result projection is typed protocol behavior over world/family
  models.
- Worldline document shape is generated from worldline family charter fields.
