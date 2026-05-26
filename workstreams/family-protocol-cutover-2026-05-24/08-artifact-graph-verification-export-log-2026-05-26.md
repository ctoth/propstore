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
