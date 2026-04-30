from __future__ import annotations

import pytest

from argumentation.epistemic import (
    EpistemicLabel,
    LabelledArc,
    LabelledEpistemicGraph,
    LinearAtomicConstraint,
    LinearRelation,
    ProbabilityFunction,
    coherence_attack_constraint,
    constraints_entail,
    induced_probability_labelling,
    least_squares_update_labelling,
    parse_epistemic_formula,
    parse_term,
    term_probability,
)


def test_argumentation_pin_exposes_epistemic_language_and_belief_distribution() -> None:
    distribution = ProbabilityFunction(
        arguments=frozenset({"a", "b"}),
        probabilities={
            frozenset(): 0.1,
            frozenset({"a"}): 0.2,
            frozenset({"b"}): 0.3,
            frozenset({"a", "b"}): 0.4,
        },
    )

    assert term_probability(parse_term("a & b"), distribution) == pytest.approx(0.4)
    assert induced_probability_labelling(distribution) == pytest.approx({"a": 0.6, "b": 0.7})
    assert parse_epistemic_formula("p(a & b) - p(b) < 0") is not None


def test_argumentation_pin_exposes_labelled_epistemic_graphs() -> None:
    graph = LabelledEpistemicGraph(
        arguments=frozenset({"a", "b"}),
        arcs=frozenset({
            LabelledArc("a", "b", frozenset({EpistemicLabel.POSITIVE, EpistemicLabel.DEPENDENT})),
        }),
    )

    assert graph.parents_by_label("b", EpistemicLabel.POSITIVE) == frozenset({"a"})
    assert graph.parents_by_label("b", EpistemicLabel.DEPENDENT) == frozenset({"a"})


def test_argumentation_pin_exposes_epistemic_linear_reasoning_and_update() -> None:
    constraints = (
        LinearAtomicConstraint({"a": 1.0}, LinearRelation.GE, 0.6),
        coherence_attack_constraint("a", "b"),
    )
    updated = least_squares_update_labelling(
        frozenset({"a", "b"}),
        {"a": 0.6, "b": 0.7},
        (LinearAtomicConstraint({"a": 1.0, "b": 1.0}, LinearRelation.LE, 1.0),),
    )

    assert constraints_entail(
        frozenset({"a", "b"}),
        constraints,
        LinearAtomicConstraint({"b": 1.0}, LinearRelation.LE, 0.4),
    )
    assert updated is not None
    assert updated["a"] == pytest.approx(0.45)
    assert updated["b"] == pytest.approx(0.55)
