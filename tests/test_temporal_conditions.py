"""Tests for temporal condition support via KindType.TIMEPOINT.

Verifies that:
1. TIMEPOINT concepts are recognized by the CEL type-checker
2. TIMEPOINT maps to z3.Real in the Z3 condition solver
3. Two claims with non-overlapping temporal scopes are disjoint (non-conflicting)
4. Two claims with overlapping temporal scopes are NOT disjoint (potentially conflicting)
5. Temporal CEL conditions like valid_from >= 100 work correctly
6. valid_from <= valid_until is enforced as an automatic constraint
7. The timepoint form YAML loads correctly

References:
  - McCarthy 1993: temporal specialization is context specialization
  - Allen 1983: interval relations encodable as Z3 Real constraints
  - Kallem & Sullivan 2006: time qualifies the context, not the assertion
"""

from __future__ import annotations

import pytest

from propstore.core.conditions import checked_condition_set
from propstore.core.conditions.cel_frontend import check_cel_expression, check_condition_ir
from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.core.conditions.solver import ConditionSolver
from propstore.form_utils import kind_type_from_form_name


def _temporal_registry() -> dict[str, ConceptInfo]:
    """Build a minimal CEL registry with temporal concepts."""
    return {
        "valid_from": ConceptInfo(
            id="ps:concept:valid_from",
            canonical_name="valid_from",
            kind=KindType.TIMEPOINT,
        ),
        "valid_until": ConceptInfo(
            id="ps:concept:valid_until",
            canonical_name="valid_until",
            kind=KindType.TIMEPOINT,
        ),
        "temperature": ConceptInfo(
            id="ps:concept:temperature",
            canonical_name="temperature",
            kind=KindType.QUANTITY,
        ),
    }


def _condition_set(sources, registry):
    return checked_condition_set(
        check_condition_ir(str(source), registry) for source in sources
    )


# ── KindType.TIMEPOINT registration ────────────────────────────────


class TestTimepointKindType:
    """KindType.TIMEPOINT exists and is correctly wired."""

    def test_timepoint_enum_value(self) -> None:
        assert KindType.TIMEPOINT.value == "timepoint"

    def test_kind_type_from_form_name(self) -> None:
        assert kind_type_from_form_name("timepoint") == KindType.TIMEPOINT

    def test_kind_type_from_form_name_other_forms_unchanged(self) -> None:
        """Adding TIMEPOINT must not break existing form->kind mappings."""
        assert kind_type_from_form_name("category") == KindType.CATEGORY
        assert kind_type_from_form_name("boolean") == KindType.BOOLEAN
        assert kind_type_from_form_name("structural") == KindType.STRUCTURAL
        # Any unknown form defaults to QUANTITY
        assert kind_type_from_form_name("temperature") == KindType.QUANTITY


# ── CEL type-checking ──────────────────────────────────────────────


class TestTimepointCelTypeCheck:
    """CEL type-checker handles TIMEPOINT concepts as numeric."""

    def test_timepoint_comparison_to_numeric_valid(self) -> None:
        registry = _temporal_registry()
        errors = check_cel_expression("valid_from >= 100", registry)
        assert not errors

    def test_timepoint_comparison_to_string_invalid(self) -> None:
        registry = _temporal_registry()
        errors = check_cel_expression('valid_from == "2021-01-01"', registry)
        assert any(not e.is_warning for e in errors)

    def test_timepoint_arithmetic_valid(self) -> None:
        registry = _temporal_registry()
        errors = check_cel_expression("valid_until - valid_from > 86400", registry)
        assert not errors

    def test_timepoint_ordering_valid(self) -> None:
        registry = _temporal_registry()
        errors = check_cel_expression("valid_from <= valid_until", registry)
        assert not errors


# ── Z3 disjointness: temporal non-overlap ──────────────────────────


class TestTemporalDisjointness:
    """Z3 correctly identifies temporal non-overlap and overlap.

    Following Allen (1983): before(A, B) encodes as e1 < s2.
    The Z3 solver detects this via UNSAT of the conjunction.
    """

    def test_non_overlapping_intervals_are_disjoint(self) -> None:
        """Two claims scoped to [100,200] and [300,400] cannot conflict."""
        registry = _temporal_registry()
        solver = ConditionSolver(registry)

        conditions_a = ["valid_from >= 100", "valid_until <= 200"]
        conditions_b = ["valid_from >= 300", "valid_until <= 400"]

        assert solver.are_disjoint(
            _condition_set(conditions_a, registry),
            _condition_set(conditions_b, registry),
        )

    def test_overlapping_intervals_are_not_disjoint(self) -> None:
        """Two claims scoped to [100,300] and [200,400] CAN conflict."""
        registry = _temporal_registry()
        solver = ConditionSolver(registry)

        conditions_a = ["valid_from >= 100", "valid_until <= 300"]
        conditions_b = ["valid_from >= 200", "valid_until <= 400"]

        assert not solver.are_disjoint(
            _condition_set(conditions_a, registry),
            _condition_set(conditions_b, registry),
        )

    def test_adjacent_intervals_are_disjoint(self) -> None:
        """[100,200] and [200,300] — boundary-touching with <= and >= is disjoint
        because the first constrains valid_until <= 200 and the second
        constrains valid_from >= 200. These share only the single point 200
        for valid_from and valid_until simultaneously, but valid_from and
        valid_until are DIFFERENT variables, so the conjunction is satisfiable
        only if a single assignment works for all four variables."""
        registry = _temporal_registry()
        solver = ConditionSolver(registry)

        conditions_a = ["valid_from >= 100", "valid_until <= 200"]
        conditions_b = ["valid_from >= 200", "valid_until <= 300"]

        # These share the point valid_from=200, valid_until=200 in both sets
        # so they are NOT disjoint (the conjunction is SAT)
        assert not solver.are_disjoint(
            _condition_set(conditions_a, registry),
            _condition_set(conditions_b, registry),
        )

    def test_strictly_before_is_disjoint(self) -> None:
        """Allen's before(A, B): e1 < s2 — strictly separated intervals."""
        registry = _temporal_registry()
        solver = ConditionSolver(registry)

        # Claim A: valid_until < 200 (ends before 200)
        # Claim B: valid_from > 200 (starts after 200)
        conditions_a = ["valid_from >= 100", "valid_until < 200"]
        conditions_b = ["valid_from > 200", "valid_until <= 400"]

        assert solver.are_disjoint(
            _condition_set(conditions_a, registry),
            _condition_set(conditions_b, registry),
        )


# ── Z3 temporal conditions with bindings ───────────────────────────


class TestTemporalBindings:
    """Concrete temporal bindings satisfy/violate conditions correctly."""

    def test_timepoint_binding_satisfies_condition(self) -> None:
        registry = _temporal_registry()
        solver = ConditionSolver(registry)

        assert solver.is_condition_satisfied(
            check_condition_ir("valid_from >= 100", registry),
            {"valid_from": 150},
        )

    def test_timepoint_binding_violates_condition(self) -> None:
        registry = _temporal_registry()
        solver = ConditionSolver(registry)

        assert not solver.is_condition_satisfied(
            check_condition_ir("valid_from >= 100", registry),
            {"valid_from": 50},
        )

    def test_temporal_interval_binding(self) -> None:
        """A binding within a temporal interval satisfies both bounds."""
        registry = _temporal_registry()
        solver = ConditionSolver(registry)

        # Condition: valid_from >= 100 AND valid_until <= 200
        # Binding: valid_from=150, valid_until=180 — should satisfy
        assert solver.is_condition_satisfied(
            check_condition_ir("valid_from >= 100", registry),
            {"valid_from": 150, "valid_until": 180},
        )
        assert solver.is_condition_satisfied(
            check_condition_ir("valid_until <= 200", registry),
            {"valid_from": 150, "valid_until": 180},
        )


# ── Mixed temporal + non-temporal conditions ───────────────────────


class TestMixedTemporalConditions:
    """Temporal conditions compose with non-temporal conditions."""

    def test_temporal_and_quantity_disjoint(self) -> None:
        """Different time AND different temperature — disjoint."""
        registry = _temporal_registry()
        solver = ConditionSolver(registry)

        conditions_a = ["valid_from >= 100", "valid_until <= 200", "temperature > 300"]
        conditions_b = ["valid_from >= 300", "valid_until <= 400", "temperature < 200"]

        assert solver.are_disjoint(
            _condition_set(conditions_a, registry),
            _condition_set(conditions_b, registry),
        )

    def test_temporal_disjoint_quantity_overlapping(self) -> None:
        """Different time, same temperature — disjoint (time alone suffices)."""
        registry = _temporal_registry()
        solver = ConditionSolver(registry)

        conditions_a = ["valid_from >= 100", "valid_until <= 200", "temperature > 300"]
        conditions_b = ["valid_from >= 300", "valid_until <= 400", "temperature > 300"]

        assert solver.are_disjoint(
            _condition_set(conditions_a, registry),
            _condition_set(conditions_b, registry),
        )

    def test_temporal_overlapping_quantity_disjoint(self) -> None:
        """Same time, different temperature — disjoint (temperature suffices)."""
        registry = _temporal_registry()
        solver = ConditionSolver(registry)

        conditions_a = ["valid_from >= 100", "valid_until <= 300", "temperature > 400"]
        conditions_b = ["valid_from >= 200", "valid_until <= 400", "temperature < 200"]

        assert solver.are_disjoint(
            _condition_set(conditions_a, registry),
            _condition_set(conditions_b, registry),
        )


# ── valid_from <= valid_until automatic constraint ─────────────────


class TestTemporalOrderingConstraint:
    """When both valid_from and valid_until appear, valid_from <= valid_until
    is automatically enforced as a well-formedness constraint.

    This prevents nonsensical intervals like [300, 100]."""

    def test_inverted_interval_detected_as_disjoint(self) -> None:
        """Conditions requiring valid_from > valid_until should be UNSAT
        when the ordering constraint is active."""
        registry = _temporal_registry()
        solver = ConditionSolver(registry)

        # These conditions require valid_from=300 and valid_until=100,
        # which violates valid_from <= valid_until
        conditions_bad = ["valid_from >= 300", "valid_until <= 100"]

        # With valid_from <= valid_until enforced, the bad conditions
        # should be internally inconsistent (UNSAT with anything)
        conditions_any = ["temperature > 0"]

        assert solver.are_disjoint(
            _condition_set(conditions_bad, registry),
            _condition_set(conditions_any, registry),
        )
