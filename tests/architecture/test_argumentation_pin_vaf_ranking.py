from __future__ import annotations

from argumentation.dung import ArgumentationFramework
from argumentation.practical_reasoning import (
    ActionBasedAlternatingTransitionSystem,
    PracticalArgument,
    critical_question_objections,
)
from argumentation.ranking import (
    RankingResult,
    burden_numbers,
    categoriser_scores,
    counting_ranking,
    discussion_based_ranking,
    h_categoriser_ranking,
    iterated_graded_ranking,
    tuples_ranking,
)
from argumentation.ranking_axioms import (
    abstraction,
    cardinality_precedence,
    counter_transitivity,
    defense_precedence,
    distributed_defense_precedence,
    independence,
    quality_precedence,
    self_contradiction,
    strict_addition_of_defense_branch,
    strict_counter_transitivity,
    strict_preference_transitive,
    void_precedence,
)
from argumentation.vaf import ValueBasedArgumentationFramework


def test_argumentation_pin_exposes_vaf_objective_and_subjective_acceptance() -> None:
    vaf = ValueBasedArgumentationFramework(
        arguments=frozenset({"A", "B", "C"}),
        attacks=frozenset({("A", "B"), ("B", "C")}),
        values=frozenset({"red", "blue"}),
        valuation={"A": "red", "B": "blue", "C": "blue"},
    )

    assert vaf.preferred_extensions_for_audience(("red", "blue")) == [frozenset({"A", "C"})]
    assert vaf.preferred_extensions_for_audience(("blue", "red")) == [frozenset({"A", "B"})]
    assert vaf.objectively_acceptable() == frozenset({"A"})
    assert vaf.subjectively_acceptable() == frozenset({"A", "B", "C"})


def test_argumentation_pin_ranking_non_convergence_is_typed_result() -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset({("a", "b"), ("b", "a")}),
    )

    result = categoriser_scores(framework, max_iterations=1, tolerance=1e-30)

    assert isinstance(result, RankingResult)
    assert result.converged is False
    assert result.iterations == 1
    assert set(result.scores) == {"a", "b"}


def test_argumentation_pin_exposes_complete_ranking_and_axiom_surface() -> None:
    framework = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c"}),
        defeats=frozenset({("a", "b"), ("b", "c")}),
    )

    for semantic in (
        categoriser_scores,
        discussion_based_ranking,
        counting_ranking,
        tuples_ranking,
        h_categoriser_ranking,
        iterated_graded_ranking,
    ):
        assert isinstance(semantic(framework), RankingResult)
    assert isinstance(burden_numbers(framework, iterations=2), RankingResult)

    result = categoriser_scores(framework)
    assert abstraction(categoriser_scores, framework)
    assert independence(categoriser_scores, framework)
    assert strict_preference_transitive(result)
    assert void_precedence(framework, result)
    assert cardinality_precedence(framework, result)
    for predicate in (
        counter_transitivity,
        defense_precedence,
        distributed_defense_precedence,
        quality_precedence,
        self_contradiction,
        strict_addition_of_defense_branch,
        strict_counter_transitivity,
    ):
        assert predicate(framework, result) in {True, False}


def test_argumentation_pin_exposes_atkinson_cq11_objection_generation() -> None:
    system = ActionBasedAlternatingTransitionSystem(
        states=frozenset({"q0", "q1", "q2"}),
        initial_state="q0",
        agents=frozenset({"agent"}),
        actions=frozenset({"proposed", "alternative"}),
        preconditions={
            "proposed": frozenset({"q0"}),
            "alternative": frozenset({"q0"}),
        },
        transitions={
            ("q0", "proposed"): "q1",
            ("q0", "alternative"): "q2",
        },
        propositions=frozenset({"goal"}),
        interpretation={
            "q0": frozenset(),
            "q1": frozenset({"goal"}),
            "q2": frozenset(),
        },
        values=frozenset({"progress", "friendship"}),
        valuation={
            ("q0", "q1", "progress"): "+",
            ("q0", "q2", "friendship"): "+",
        },
    )
    argument = PracticalArgument("agent", "q0", "proposed", "q1", "goal", "progress")

    objections = critical_question_objections(system, argument, "CQ11")

    assert [(objection.alternative_action, objection.promoted_value) for objection in objections] == [
        ("alternative", "friendship")
    ]
