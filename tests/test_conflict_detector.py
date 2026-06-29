"""Conflict detector behavioral contracts.

Ported from the reference suite (test_conflict_detector / _orchestrator_isolation /
_equation_conflict_status / _parameter_conflict_error_preservation /
_parameter_conflict_unit_aware / _algorithm_sympy_tier_not_conflict), translated to
the rewrite's substrate-direct construction: claims are built as ``ConflictClaim``
values and CEL registries as ``condition_ir.ConceptInfo`` maps, with no stale
``propstore.core.conditions`` / claim-file-ingestion / conftest fixtures.

The SymPy-backed parameterization-derivation (transitive) detector is deferred
(see reports/p6a-blocked.md); those reference tests are not ported here.
"""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock

import pytest
from condition_ir import ConceptInfo, KindType, Z3TranslationError

from propstore.conflict_detector import (
    ConflictClass,
    ConflictRecord,
    detect_conflicts,
)
from propstore.conflict_detector import orchestrator
from propstore.conflict_detector.algorithms import detect_algorithm_conflicts
from propstore.conflict_detector.condition_classifier import classify_conditions
from propstore.conflict_detector.collectors import conflict_claim_from_payload
from propstore.conflict_detector.equations import detect_equation_conflicts
from propstore.conflict_detector.measurements import detect_measurement_conflicts
from propstore.conflict_detector.models import (
    ConflictClaim,
    ConflictClaimVariable,
    coerce_conflict_class,
)
from propstore.conflict_detector.parameter_claims import detect_parameter_conflicts
from propstore.dimensions import UnitConversion
from propstore.families.forms import FormDefinition


# ── models / payload parse ───────────────────────────────────────────


def test_conflict_claim_from_payload_maps_stored_keys() -> None:
    claim = ConflictClaim.from_payload(
        {
            "id": "c1",
            "type": "parameter",
            "output_concept": "out",
            "target_concept": "tgt",
            "value": 12.0,
            "unit": "Hz",
            "conditions": ["x > 1"],
            "context": {"id": "ctx_a"},
            "variables": [{"concept": "k", "symbol": "x", "role": "independent"}],
        }
    )
    assert claim is not None
    assert claim.claim_id == "c1"
    assert claim.claim_type == "parameter"
    assert claim.output_concept_id == "out"
    assert claim.target_concept_id == "tgt"
    assert claim.context_id == "ctx_a"
    assert [str(condition) for condition in claim.conditions] == ["x > 1"]
    assert claim.variables == (
        ConflictClaimVariable(concept_id="k", symbol="x", role="independent"),
    )


def test_conflict_claim_from_payload_requires_id() -> None:
    assert ConflictClaim.from_payload({"value": 1.0}) is None


def test_conflict_claim_from_payload_folds_source_condition() -> None:
    claim = conflict_claim_from_payload({"id": "c1", "value": 1.0}, source_paper="paperA")
    assert claim is not None
    assert claim.source_paper == "paperA"
    assert "source == 'paperA'" in [str(condition) for condition in claim.conditions]


def test_coerce_conflict_class_round_trips_and_uppercases() -> None:
    assert coerce_conflict_class(None) is None
    assert coerce_conflict_class(ConflictClass.CONFLICT) is ConflictClass.CONFLICT
    assert coerce_conflict_class("PHI_NODE") is ConflictClass.PHI_NODE
    assert coerce_conflict_class("phi_node") is ConflictClass.PHI_NODE


# ── condition classifier (the Z3 dispatch) ───────────────────────────


def _quantity_registry() -> dict[str, ConceptInfo]:
    return {"x": ConceptInfo("x", "x", KindType.QUANTITY)}


def test_classify_identical_conditions_is_conflict() -> None:
    registry = _quantity_registry()
    assert (
        classify_conditions(["x > 10"], ["x > 10"], registry) is ConflictClass.CONFLICT
    )


def test_classify_equivalent_spellings_is_conflict() -> None:
    registry = _quantity_registry()
    assert (
        classify_conditions(["x > 10"], ["10 < x"], registry) is ConflictClass.CONFLICT
    )


def test_classify_disjoint_conditions_is_phi_node() -> None:
    registry = _quantity_registry()
    assert (
        classify_conditions(["x > 10"], ["x < 5"], registry) is ConflictClass.PHI_NODE
    )


def test_classify_overlapping_conditions_is_overlap() -> None:
    registry = _quantity_registry()
    assert (
        classify_conditions(["x > 10"], ["x > 5"], registry) is ConflictClass.OVERLAP
    )


# ── equation detector (eq-equiv) ─────────────────────────────────────


def _equation_claim(claim_id: str, expression: str) -> ConflictClaim:
    return ConflictClaim(
        claim_id=claim_id,
        claim_type="equation",
        expression=expression,
        variables=(
            ConflictClaimVariable(concept_id="output", symbol="y", role="dependent"),
            ConflictClaimVariable(concept_id="factor_a", symbol="x", role="independent"),
            ConflictClaimVariable(concept_id="factor_b", symbol="z", role="independent"),
        ),
    )


def test_equation_detector_skips_equivalent_orientations() -> None:
    records = detect_equation_conflicts(
        [_equation_claim("left", "y = x + z"), _equation_claim("right", "x + z = y")],
        {},
    )
    assert records == []


def test_equation_detector_reports_proven_difference() -> None:
    records = detect_equation_conflicts(
        [_equation_claim("linear", "y = x + z"), _equation_claim("scaled", "y = 2*x + z")],
        {},
    )
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.CONFLICT


def test_equation_detector_reports_undecidable_domain_sensitive_pair() -> None:
    records = detect_equation_conflicts(
        [
            _equation_claim("log_sum", "y = log(x * z)"),
            _equation_claim("sum_logs", "y = log(x) + log(z)"),
        ],
        {},
    )
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.UNKNOWN


# ── algorithm detector (ast-equiv) ───────────────────────────────────


def _algorithm_claim(claim_id: str, body: str) -> ConflictClaim:
    return ConflictClaim(
        claim_id=claim_id,
        claim_type="algorithm",
        output_concept_id="out",
        body=body,
        variables=(ConflictClaimVariable(concept_id="in", symbol="x"),),
    )


def _algorithm_registry() -> dict[str, ConceptInfo]:
    return {"x": ConceptInfo("in", "x", KindType.QUANTITY)}


def test_algorithm_equivalent_bodies_do_not_conflict() -> None:
    records = detect_algorithm_conflicts(
        [
            _algorithm_claim("a", "def f(x):\n    return x + x\n"),
            _algorithm_claim("b", "def f(x):\n    return 2 * x\n"),
        ],
        _algorithm_registry(),
    )
    assert records == []


def test_algorithm_non_equivalent_bodies_conflict() -> None:
    records = detect_algorithm_conflicts(
        [
            _algorithm_claim("a", "def f(x):\n    return x\n"),
            _algorithm_claim("b", "def f(x):\n    return x + 1\n"),
        ],
        _algorithm_registry(),
    )
    assert len(records) == 1


def test_algorithm_partial_eval_equivalence_suppresses_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    from propstore.conflict_detector import algorithms

    class _Result:
        equivalent = True
        similarity = 1.0

    monkeypatch.setattr(algorithms, "ast_compare", lambda *args, **kwargs: _Result())
    records = algorithms.detect_algorithm_conflicts(
        [
            _algorithm_claim("a", "def f(x):\n    return x\n"),
            _algorithm_claim("b", "def f(x):\n    return x\n"),
        ],
        _algorithm_registry(),
    )
    assert records == []


# ── measurement detector (value_comparison) ──────────────────────────


def _measurement_claim(
    claim_id: str, value: float, *, population: str | None = None
) -> ConflictClaim:
    return ConflictClaim(
        claim_id=claim_id,
        claim_type="measurement",
        target_concept_id="concept",
        measure="mean",
        value=value,
        listener_population=population,
    )


def test_measurement_population_mismatch_is_phi_node() -> None:
    records = detect_measurement_conflicts(
        [
            _measurement_claim("m1", 10.0, population="adults"),
            _measurement_claim("m2", 20.0, population="children"),
        ],
        {},
    )
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.PHI_NODE


def test_measurement_same_population_identical_conditions_is_conflict() -> None:
    records = detect_measurement_conflicts(
        [
            _measurement_claim("m1", 10.0, population="adults"),
            _measurement_claim("m2", 20.0, population="adults"),
        ],
        {},
    )
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.CONFLICT


def test_measurement_compatible_values_no_conflict() -> None:
    records = detect_measurement_conflicts(
        [_measurement_claim("m1", 10.0), _measurement_claim("m2", 10.0)],
        {},
    )
    assert records == []


# ── direct parameter detector (Z3 partition + error preservation) ────


def _three_parameter_claims() -> tuple[ConflictClaim, ...]:
    return tuple(
        ConflictClaim(
            claim_id=f"c{i}",
            claim_type="parameter",
            output_concept_id="outcome",
            value=float(i),
            unit="",
            conditions=("intention_to_treat == true",),
        )
        for i in range(3)
    )


def _boolean_registry() -> dict[str, ConceptInfo]:
    return {
        "intention_to_treat": ConceptInfo(
            "intention_to_treat", "intention_to_treat", KindType.BOOLEAN
        )
    }


def test_partitioning_runtime_error_preserves_cause_text() -> None:
    stub = MagicMock()
    underlying = "Structural concept 'intention_to_treat' cannot appear in CEL expressions"
    stub.partition_equivalence_classes.side_effect = Z3TranslationError(underlying)

    with pytest.raises(RuntimeError) as info:
        detect_parameter_conflicts(
            _three_parameter_claims(),
            cel_registry=_boolean_registry(),
            solver=stub,
        )
    message = str(info.value)
    assert "Z3 partitioning failed" in message
    assert underlying in message


def test_disjointness_runtime_error_preserves_cause_text() -> None:
    stub = MagicMock()
    stub.partition_equivalence_classes.return_value = [[0], [1, 2]]
    underlying = "Structural concept 'intention_to_treat' cannot appear in CEL expressions"
    stub.are_disjoint_result.side_effect = Z3TranslationError(underlying)

    with pytest.raises(RuntimeError) as info:
        detect_parameter_conflicts(
            _three_parameter_claims(),
            cel_registry=_boolean_registry(),
            solver=stub,
        )
    message = str(info.value)
    assert "Z3 disjointness check failed" in message
    assert underlying in message


# ── orchestrator end-to-end + isolation ──────────────────────────────


def _frequency_form() -> FormDefinition:
    return FormDefinition(
        name="frequency",
        kind=KindType.QUANTITY,
        unit_symbol="Hz",
        allowed_units=("Hz", "kHz"),
        conversions={
            "kHz": UnitConversion(unit="kHz", type="multiplicative", multiplier=1000.0)
        },
    )


def _frequency_concept_registry() -> dict[str, dict[str, object]]:
    return {
        "c1": {
            "artifact_id": "c1",
            "canonical_name": "c1",
            "form": "frequency",
            "_form_definition": _frequency_form(),
        }
    }


def _parameter_claim(claim_id: str, value: float, unit: str) -> ConflictClaim:
    return ConflictClaim(
        claim_id=claim_id,
        claim_type="parameter",
        output_concept_id="c1",
        value=value,
        unit=unit,
    )


def test_detect_conflicts_unit_aware_same_value_no_conflict() -> None:
    records = detect_conflicts(
        [_parameter_claim("a", 200.0, "Hz"), _parameter_claim("b", 0.2, "kHz")],
        _frequency_concept_registry(),
        {},
    )
    assert records == []


def test_detect_conflicts_unit_aware_real_difference_reports_conflict() -> None:
    records = detect_conflicts(
        [_parameter_claim("a", 200.0, "Hz"), _parameter_claim("b", 300.0, "Hz")],
        _frequency_concept_registry(),
        {},
    )
    assert len(records) == 1
    assert isinstance(records[0], ConflictRecord)
    assert records[0].warning_class == ConflictClass.CONFLICT


def test_detect_conflicts_synthetic_source_collision_is_loud() -> None:
    with pytest.raises(orchestrator.SyntheticConceptCollision):
        detect_conflicts(
            [],
            {},
            {"source": ConceptInfo("real-source", "source", KindType.CATEGORY)},
        )


def test_orchestrator_lifting_decision_cache_is_explicit() -> None:
    assert hasattr(orchestrator, "LiftingDecisionCache")


def test_orchestrator_lifted_seen_key_includes_derivation_chain() -> None:
    source = inspect.getsource(orchestrator._expand_lifted_conflict_claims)
    assert "derivation_chain" in source
