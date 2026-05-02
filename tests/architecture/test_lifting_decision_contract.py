from __future__ import annotations

from dataclasses import fields, is_dataclass

import propstore.context_lifting as context_lifting


def test_lifting_decision_status_has_lifted_blocked_and_unknown() -> None:
    """Guha 1991 pngs/page-033/page-034 pins explicit, blockable lifting.
    Bozzato 2018 pngs/page-009 pins contextual defeasible exceptions.
    Garcia and Simari 2004 pngs/page-025 pins UNKNOWN as a first-class query
    answer, not a boolean false.
    """

    assert hasattr(context_lifting, "LiftingDecisionStatus")
    status_type = getattr(context_lifting, "LiftingDecisionStatus")

    assert {status.value for status in status_type} == {
        "lifted",
        "blocked",
        "unknown",
    }


def test_lifting_decision_is_typed_evidence_carrier() -> None:
    """McCarthy/Guha lifting rules and Bozzato justified exceptions require
    preserving rule, support, provenance, exception, and solver witness data.
    Page anchors: McCarthy pngs/page-000, Guha pngs/page-033/page-034,
    Bozzato pngs/page-009, Garcia pngs/page-025.
    """

    assert hasattr(context_lifting, "LiftingDecision")
    decision_type = getattr(context_lifting, "LiftingDecision")
    assert is_dataclass(decision_type)

    field_names = {field.name for field in fields(decision_type)}
    assert {
        "source_context",
        "target_context",
        "proposition_id",
        "status",
        "mode",
        "rule_id",
        "rule_conditions",
        "support",
        "provenance",
        "exception",
        "solver_witness",
    }.issubset(field_names)


def test_boolean_can_lift_is_not_the_semantic_contract() -> None:
    """The lifting semantic API must expose decisions, not just True/False."""

    assert hasattr(context_lifting, "LiftingDecision")
    assert not hasattr(context_lifting, "LiftingMaterializationStatus")
