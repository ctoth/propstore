"""Parameterization groups and reachability walk over concept edges.

A parameterization relates an output concept to the input concepts it is
computed from (e.g. a derived quantity parameterized by its factors). Two
analyses over those edges:

* :func:`build_parameterization_groups` — the connected components of the
  parameterization graph (union-find): concepts that are transitively related by
  parameterization belong to one group.
* :func:`reachable_concepts` — the set of concepts reachable from a starting set
  by following parameterization input edges (a directed walk).

Both are thin graph routines over an explicit ``output -> inputs`` edge mapping;
there are no DTO shells. Callers supply the edges already resolved to concept ids
(the resolution from authored claims/concepts lives at the call site).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping


def build_parameterization_groups(edges: Mapping[str, Iterable[str]]) -> list[set[str]]:
    """Return the connected components of the parameterization graph.

    Every concept that appears as a key (an output) is a node; an output is
    unioned with each of its input concepts that is itself a known node. The
    result is the list of component sets. Order within and across components is
    not significant.
    """

    parent: dict[str, str] = {}

    def find(node: str) -> str:
        parent.setdefault(node, node)
        root = node
        while parent[root] != root:
            root = parent[root]
        # path-halving compression
        while parent[node] != root:
            parent[node], node = root, parent[node]
        return root

    def union(a: str, b: str) -> None:
        parent[find(a)] = find(b)

    nodes = set(edges)
    for output, inputs in edges.items():
        find(output)
        for input_id in inputs:
            if input_id in nodes:
                union(output, input_id)

    components: dict[str, set[str]] = {}
    for node in nodes:
        components.setdefault(find(node), set()).add(node)
    return list(components.values())


def reachable_concepts(
    start: Iterable[str],
    parameterizations_for: Callable[[str], Iterable[str]],
) -> set[str]:
    """Return all concepts reachable from ``start`` via parameterization inputs.

    Performs a breadth-first walk: from each concept, ``parameterizations_for``
    yields the input concept ids it is parameterized by; those are enqueued. The
    returned set includes the starting concepts.
    """

    visited: set[str] = set()
    frontier: list[str] = list(start)
    while frontier:
        current = frontier.pop()
        if current in visited:
            continue
        visited.add(current)
        for input_id in parameterizations_for(current):
            if input_id not in visited:
                frontier.append(input_id)
    return visited
