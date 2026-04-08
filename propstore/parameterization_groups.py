"""Connected-component analysis for parameterization relationships.

Builds an adjacency graph from concepts' parameterization_relationships
and finds connected components using union-find. Each component represents
a "parameter space group" — a set of concepts that are linked by algebraic
or functional relationships.
"""

from __future__ import annotations


def build_groups(concepts: list[dict]) -> list[set[str]]:
    """Find connected components among concepts via parameterization relationships.

    For each concept with parameterization_relationships, the concept is
    connected to all its inputs. The result is a list of sets of concept IDs,
    where each set is one connected component.

    Concepts with no parameterization links appear as singleton groups.

    Args:
        concepts: List of concept data dicts (must have 'artifact_id' field).

    Returns:
        List of sets of concept IDs, one per connected component.
    """
    if not concepts:
        return []

    def concept_candidates(concept: dict) -> set[str]:
        candidates: set[str] = set()
        artifact_id = concept.get("artifact_id")
        if isinstance(artifact_id, str) and artifact_id:
            candidates.add(artifact_id)
        canonical_name = concept.get("canonical_name")
        if isinstance(canonical_name, str) and canonical_name:
            candidates.add(canonical_name)
        for logical_id in concept.get("logical_ids", []) or []:
            if not isinstance(logical_id, dict):
                continue
            namespace = logical_id.get("namespace")
            value = logical_id.get("value")
            if isinstance(namespace, str) and isinstance(value, str) and namespace and value:
                candidates.add(f"{namespace}:{value}")
                candidates.add(value)
        for alias in concept.get("aliases", []) or []:
            if not isinstance(alias, dict):
                continue
            alias_name = alias.get("name")
            if isinstance(alias_name, str) and alias_name:
                candidates.add(alias_name)
        return candidates

    # Collect all concept IDs
    all_ids: set[str] = set()
    alias_to_id: dict[str, str] = {}
    for c in concepts:
        cid = c.get("artifact_id")
        if isinstance(cid, str) and cid:
            all_ids.add(cid)
            for candidate in concept_candidates(c):
                alias_to_id.setdefault(candidate, cid)

    # Union-Find data structure
    parent: dict[str, str] = {cid: cid for cid in all_ids}
    rank: dict[str, int] = {cid: 0 for cid in all_ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path compression
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        # Union by rank
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1

    # Build edges from parameterization relationships
    for c in concepts:
        cid = c.get("artifact_id")
        if not isinstance(cid, str) or not cid:
            continue
        for param in c.get("parameterization_relationships", []) or []:
            for input_id in param.get("inputs", []) or []:
                resolved_input_id = alias_to_id.get(str(input_id), str(input_id))
                if resolved_input_id in all_ids:
                    union(cid, resolved_input_id)

    # Collect connected components
    components: dict[str, set[str]] = {}
    for cid in all_ids:
        root = find(cid)
        if root not in components:
            components[root] = set()
        components[root].add(cid)

    return list(components.values())
