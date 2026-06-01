"""Shared utilities for walking parameterization graphs.

Used by worldline resolution (pre-resolve conflicts) and
conflict_detector.parameterization_conflicts
(transitive conflict detection). Both need to find all concepts
reachable via parameterization edges from a set of starting concepts.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence

from propstore.families.concepts.declaration import Parameterization


def reachable_concepts(
    start: set[str],
    parameterizations_for: Callable[[str], Sequence[Parameterization]],
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
            concept_ids_json = param.concept_ids
            if not concept_ids_json:
                continue
            input_ids = (
                json.loads(concept_ids_json)
                if isinstance(concept_ids_json, str)
                else concept_ids_json
            )
            for iid in input_ids:
                if iid != cid and iid not in visited:
                    queue.append(iid)

    return visited
