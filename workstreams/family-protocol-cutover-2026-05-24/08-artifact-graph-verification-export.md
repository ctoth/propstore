# 08 Artifact Graph Verification Export

## Prerequisites

- `01-deleted-file-fallout-repair.md`
- `02-quire-generated-family-protocols.md`
- `03-generic-family-lookup-cleanup.md`
- `04-family-document-deletion.md`
- `05-registry-contracts-batch-specs.md`
- `06-source-lifecycle-state-machines.md`
- `07-proposal-lifecycle-state-machines.md`

## Target

Artifact payload/dependency policy, verification traversal, and graph
discovery are driven by charter metadata and typed family relationships.
Rendering remains presentation only.

## Deletion Targets

- Concrete document imports in `propstore/artifact_codes.py`
- `_stamp_source_doc`, `_stamp_source_claim`, `_stamp_source_justification`,
  `_stamp_justification`, `_stamp_source_stance`, and `_stamp_stance`
- family-specific artifact verification loaders in
  `propstore/artifact_verification.py`
- manual claim/source/justification/stance verification walk
- `propstore/graph_export.py::build_knowledge_graph` hardcoded discovery
- `_claim_concept_id`
- `_display_claim_id_from_store`
- `json.loads(row.concept_ids)` in graph export

## Kept Behavior

- Canonical artifact hashing with `canonical_json_sha256`.
- Source and canonical artifact stamping as lifecycle transitions.
- User-visible artifact verification reports.
- `GraphNode`, `GraphEdge`, `KnowledgeGraph.to_json`, and
  `KnowledgeGraph.to_dot` rendering.
- App/CLI request/report shells when they remain presentation boundary objects.

## Execution

1. Delete concrete artifact-code document imports and payload rewrite helpers.
2. Replace stamping with family artifact payload/dependency APIs.
3. Delete artifact verification family-specific loaders and manual walk.
4. Replace verification traversal with generic artifact dependency traversal.
5. Delete graph discovery in `build_knowledge_graph`.
6. Feed rendering from generic family graph projection records.

## Search Gates

```powershell
rg -n -F -- "propstore.artifact_codes" propstore tests
rg -n -F -- "propstore.artifact_verification" propstore tests
rg -n -F -- "build_knowledge_graph" propstore tests
rg -n -F -- "_claim_concept_id" propstore tests
rg -n -F -- "_display_claim_id_from_store" propstore tests
rg -n -F -- "json.loads(row.concept_ids)" propstore/graph_export.py
rg -n -F -- "select_concept_ids_for_group" propstore tests
rg -n -F -- "search_concept_ids" propstore tests
rg -n -F -- "resolve_sidecar_concept_id" propstore tests
```

## Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label artifact-graph-verification tests/test_graph_export.py tests/test_verify_cli.py tests/test_world_query.py
```

## Completion

- Artifact and graph traversal are generic relationship/reference projection.
- Graph export is rendering, not semantic graph discovery.
