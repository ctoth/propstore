# 08 Artifact Graph Verification Export Log

## Current State

- Quire now provides generic charter projection records for artifact payloads,
  artifact dependencies, graph nodes, and graph edges.
- Propstore is pinned to Quire commit
  `389f09edcaffd052d5a843d77f0dee1ed6d4acda`.
- Phase 08 is now executable against the new Quire projection API.

## Target State

- Artifact code computation is owned by family projection policy, not the old
  root `propstore.artifact_codes` module.
- Verification traversal uses family/artifact dependency indexes instead of
  family-specific loader functions and a hardcoded claim walk.
- Graph export keeps `GraphNode`, `GraphEdge`, `KnowledgeGraph.to_json`, and
  `KnowledgeGraph.to_dot` as rendering surfaces while graph discovery is fed
  from family graph projection records.
- The old root artifact/verification modules and forbidden graph discovery
  symbols are gone from production and tests.

## Evidence Log

- Started on `master` with clean tracked status; only unrelated untracked
  diagnostic files/directories were present.
- Quire projection payloads now normalize enum values; Propstore is pinned to
  pushed Quire commit `46cf1c2a84f385a62c39cea272f9590a43b4ee5e`.
- Deleted the old root artifact code and artifact verification modules from
  the production path. Search gates for `propstore.artifact_codes`,
  `propstore.artifact_verification`, `stamp_source_artifact_codes`, and
  `stamp_canonical_artifact_codes` are clean.
- Focused type gate passed:
  `uv run pyright propstore\families\artifacts.py propstore\source\finalize.py propstore\source\promote.py propstore\app\verify.py`.
- Quire graph projection now supports typed graph-edge source fields; Propstore
  is pinned to pushed Quire commit
  `df5732f48e28fa108bda7b0a5fd540aafc93e992`.
- Deleted `build_knowledge_graph` discovery from `propstore/graph_export.py`;
  graph rendering now consumes projection records from
  `propstore.world.graph_projection`.
- Search gates for `build_knowledge_graph`, `_claim_concept_id`,
  `_display_claim_id_from_store`, and `json.loads(row.concept_ids)` in graph
  export are clean.
- Focused graph type gate passed:
  `uv run pyright propstore\graph_export.py propstore\world\graph_projection.py propstore\app\world_reasoning.py propstore\support_revision\af_adapter.py propstore\world\assignment_selection_policy.py`.
- Focused graph pytest passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label graph-family-projection tests/test_graph_export.py`;
  10 passed, log `logs\test-runs\graph-family-projection-20260526-122501.log`.
