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
