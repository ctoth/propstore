"""Shared utilities for walking parameterization graphs.

Used by worldline resolution (pre-resolve conflicts) and param_conflicts
(transitive conflict detection). Both need to find all concepts
reachable via parameterization edges from a set of starting concepts.
"""

from __future__ import annotations

import json
from typing import Any, Callable


def reachable_concepts(
    start: set[str],
    parameterizations_for: Callable[[str], list[dict]],
) -> set[str]:
    """Find all concepts reachable via parameterization inputs from start.

    Walks the parameterization graph breadth-first from the starting
    concepts, following input edges. Returns all visited concept IDs
    including the starting set.

    Parameters
    ----------
    start : set[str]
        Concept IDs to start from.
    parameterizations_for : callable
        Given a concept ID, returns its parameterization rows
        (each with a 'concept_ids' JSON field listing input concept IDs).
    """
    visited: set[str] = set()
    queue = list(start)

    while queue:
        cid = queue.pop()
        if cid in visited:
            continue
        visited.add(cid)

        for param in parameterizations_for(cid):
            concept_ids_json = param.get("concept_ids")
            if not concept_ids_json:
                continue
            input_ids = json.loads(concept_ids_json) if isinstance(concept_ids_json, str) else concept_ids_json
            for iid in input_ids:
                if iid != cid and iid not in visited:
                    queue.append(iid)

    return visited


def parameterization_edges_from_registry(
    concept_registry: dict[str, dict],
    *,
    exactness_filter: set[str] | None = None,
) -> dict[str, list[dict]]:
    """Build a parameterization edge map from a concept registry.

    Returns a dict mapping output concept ID to a list of parameterization
    dicts, each with 'inputs', 'sympy', and 'conditions' fields.

    Parameters
    ----------
    concept_registry : dict
        Concept ID → concept data dict.
    exactness_filter : set[str] or None
        If provided, only include parameterizations with exactness in
        this set. Pass {"exact"} for strict, {"exact", "approximate"}
        for relaxed, or None for all.
    """
    edges: dict[str, list[dict]] = {}
    for cid, cdata in concept_registry.items():
        for rel in cdata.get("parameterization_relationships", []):
            exactness = rel.get("exactness", "")
            if exactness_filter is not None and exactness not in exactness_filter:
                continue
            inputs = rel.get("inputs", [])
            sympy_expr = rel.get("sympy")
            if not inputs or not sympy_expr:
                continue
            if cid not in edges:
                edges[cid] = []
            edges[cid].append({
                "inputs": inputs,
                "sympy": sympy_expr,
                "conditions": rel.get("conditions", []),
                "exactness": exactness,
            })
    return edges
