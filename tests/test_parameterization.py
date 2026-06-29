"""Phase 3 parameterization: connected-component groups and the reachability walk."""

from __future__ import annotations

from propstore.parameterization import build_parameterization_groups, reachable_concepts


def test_groups_are_connected_components() -> None:
    # speed <- distance, time ; distance <- (none) ; mass standalone
    edges = {
        "speed": ("distance", "time"),
        "distance": (),
        "time": (),
        "mass": (),
    }
    groups = build_parameterization_groups(edges)
    frozen = {frozenset(g) for g in groups}
    assert frozenset({"speed", "distance", "time"}) in frozen
    assert frozenset({"mass"}) in frozen
    assert len(groups) == 2


def test_groups_ignore_inputs_outside_the_known_node_set() -> None:
    # "external" is not itself a node (no key), so it is not unioned in; "distance"
    # is a node, so it joins "speed".
    edges = {"speed": ("distance", "external"), "distance": ()}
    groups = build_parameterization_groups(edges)
    assert {frozenset(g) for g in groups} == {frozenset({"speed", "distance"})}


def test_walk_reaches_transitive_inputs() -> None:
    edges = {
        "speed": ("distance", "time"),
        "distance": ("length_unit",),
        "time": (),
        "length_unit": (),
    }

    def inputs_for(concept_id: str) -> tuple[str, ...]:
        return edges.get(concept_id, ())

    reached = reachable_concepts({"speed"}, inputs_for)
    assert reached == {"speed", "distance", "time", "length_unit"}


def test_walk_includes_start_and_terminates_on_cycles() -> None:
    edges = {"a": ("b",), "b": ("a",)}

    def inputs_for(concept_id: str) -> tuple[str, ...]:
        return edges.get(concept_id, ())

    assert reachable_concepts({"a"}, inputs_for) == {"a", "b"}
