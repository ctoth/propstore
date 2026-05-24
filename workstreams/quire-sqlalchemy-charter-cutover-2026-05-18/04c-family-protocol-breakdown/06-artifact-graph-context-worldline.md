# 06 Artifact, Graph, Context, And Worldline

## Final State

Artifact codes, artifact verification, graph export, context lifting, and
worldline result projection use generic family relationship/reference/artifact
metadata and typed family/domain methods. Root modules do not hardcode family
document classes, graph-discovery loops, source/claim/justification/stance
trees, context document shape, or worldline resolver chains.

## Delete First

Delete these old production surfaces before repairing callers:

- Concrete document imports and `_stamp_*` payload rewrite helpers in
  `propstore/artifact_codes.py`.
- Family-specific loaders and manual claim-tree walk in
  `propstore/artifact_verification.py`.
- Hardcoded graph discovery in `propstore/graph_export.py::build_knowledge_graph`,
  `_claim_concept_id`, and `_display_claim_id_from_store`.
- Root persisted-shape ownership in `propstore/context_lifting.py`; semantic
  lifting behavior moves under the context family owner.
- Resolver-chain helper family in `propstore/worldline/resolution.py`.
- Handwritten worldline document structs after generated documents exist.

## Repair Owners

- Quire/family metadata: artifact payload fields, dependency edges, graph
  projection records, relationship traversal.
- Claim/concept/context/worldline family models: display, scalar value,
  target-value, lifting, and graph semantics.
- Worldline family artifact policy: fingerprint/content-hash semantics.
- Presentation modules: JSON/DOT rendering only.

## Search Gates

```powershell
rg -n -F -- "propstore.artifact_codes" propstore tests
rg -n -F -- "propstore.artifact_verification" propstore tests
rg -n -F -- "build_knowledge_graph" propstore tests
rg -n -F -- "_claim_concept_id" propstore tests
rg -n -F -- "json.loads(row.concept_ids)" propstore/graph_export.py
rg -n -F -- "propstore.context_lifting" propstore tests
rg -n -F -- "CONTEXT_LIFTING_RULE_TABLE" propstore tests
rg -n -F -- "CONTEXT_LIFTING_MATERIALIZATION_TABLE" propstore tests
rg -n -F -- "propstore.worldline.resolution" propstore tests
rg -n -F -- "_resolve_claim_target" propstore/worldline propstore tests
rg -n -F -- "_resolve_claim_input" propstore/worldline propstore tests
rg -n -F -- "def _claim_value" propstore/world propstore/worldline tests
rg -n -F -- "WorldlineDefinitionDocument" propstore tests
rg -n -F -- "propstore.families.documents.worldlines" propstore tests
```

All gates are zero-hit gates outside notes, workstreams, docs, and reports.

## Type And Test Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label artifact-graph-worldline tests/test_verify_cli.py tests/test_graph_export.py tests/test_contexts.py tests/test_context_lifting_ws5.py tests/test_worldline.py tests/test_worldline_result_boundaries.py tests/test_world_query.py
```

## Completion

- [ ] Artifact stamping and verification traverse declared family metadata.
- [ ] Graph export discovery is generic family graph projection.
- [ ] Context lifting semantics live under the context family owner.
- [ ] Worldline resolution projection uses typed world/worldline protocols.
- [ ] Search, type, and test gates pass.
