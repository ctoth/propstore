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
from condition_ir import (
    ConceptInfo,
    KindType,
    Z3TranslationError,
    synthetic_category_concept,
    to_cel_exprs,
)

from propstore.conflict_detector import (
    ConflictClass,
    ConflictRecord,
    detect_conflicts,
)
from propstore.conflict_detector import orchestrator
from propstore.conflict_detector.algorithms import detect_algorithm_conflicts
from propstore.conflict_detector.condition_classifier import classify_conditions
from propstore.conflict_detector.equations import detect_equation_conflicts
from propstore.conflict_detector.measurements import detect_measurement_conflicts
from propstore.conflict_detector.models import (
    ConflictClaim,
    coerce_conflict_class,
)
from propstore.conflict_detector.parameter_claims import detect_parameter_conflicts
from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
)
from propstore.dimensions import UnitConversion
from propstore.families.claims import Claim, ClaimType, ClaimVariable
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition


# ── models / charter view ────────────────────────────────────────────


def test_conflict_claim_from_claim_maps_charter_fields() -> None:
    claim = Claim(
        claim_id="c1",
        context_id="ctx_a",
        claim_type=ClaimType.PARAMETER,
        output_concept="out",
        target_concept="tgt",
        value=12.0,
        unit="Hz",
        conditions=("x > 1",),
        variables=(ClaimVariable(concept="k", symbol="x", role="independent"),),
    )
    view = ConflictClaim.from_claim(claim)
    assert view.claim_id == "c1"
    assert view.claim_type is ClaimType.PARAMETER
    assert view.output_concept_id == "out"
    assert view.target_concept_id == "tgt"
    assert view.context_id == "ctx_a"
    assert [str(condition) for condition in view.conditions] == ["x > 1"]
    assert view.variables == (
        ClaimVariable(concept="k", symbol="x", role="independent"),
    )


def test_conflict_claim_from_claim_folds_source_condition() -> None:
    view = ConflictClaim.from_claim(
        Claim(claim_id="c1", value=1.0), source_paper="paperA"
    ).with_source_condition()
    assert view.source_paper == "paperA"
    assert "source == 'paperA'" in [str(condition) for condition in view.conditions]


def test_conflict_claim_without_source_adds_no_condition() -> None:
    view = ConflictClaim.from_claim(Claim(claim_id="c1", value=1.0)).with_source_condition()
    assert view.source_paper is None
    assert view.conditions == ()


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
        claim_type=ClaimType.EQUATION,
        expression=expression,
        variables=(
            ClaimVariable(concept="output", symbol="y", role="dependent"),
            ClaimVariable(concept="factor_a", symbol="x", role="independent"),
            ClaimVariable(concept="factor_b", symbol="z", role="independent"),
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
        claim_type=ClaimType.ALGORITHM,
        output_concept_id="out",
        body=body,
        variables=(ClaimVariable(concept="in", symbol="x"),),
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
    conditions = (
        () if population is None else (f"population == '{population}'",)
    )
    return ConflictClaim(
        claim_id=claim_id,
        claim_type=ClaimType.MEASUREMENT,
        target_concept_id="concept",
        measure="mean",
        value=value,
        conditions=to_cel_exprs(conditions),
    )


def _population_registry() -> dict[str, ConceptInfo]:
    return {
        "population": synthetic_category_concept(
            concept_id="population",
            canonical_name="population",
            values=["adults", "children"],
            extensible=False,
        )
    }


def test_measurement_population_mismatch_is_phi_node() -> None:
    records = detect_measurement_conflicts(
        [
            _measurement_claim("m1", 10.0, population="adults"),
            _measurement_claim("m2", 20.0, population="children"),
        ],
        _population_registry(),
    )
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.PHI_NODE


def test_measurement_same_population_identical_conditions_is_conflict() -> None:
    records = detect_measurement_conflicts(
        [
            _measurement_claim("m1", 10.0, population="adults"),
            _measurement_claim("m2", 20.0, population="adults"),
        ],
        _population_registry(),
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
            claim_type=ClaimType.PARAMETER,
            output_concept_id="outcome",
            value=float(i),
            unit="",
            conditions=to_cel_exprs(("intention_to_treat == true",)),
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


def _frequency_concept() -> Concept:
    return Concept(
        concept_id="c1",
        canonical_name="c1",
        lexical_entry=LexicalEntry(
            identifier="entry:c1",
            canonical_form=LexicalForm(written_rep="c1", language="en"),
            senses=(LexicalSense(reference=OntologyReference(uri="u:c1")),),
            physical_dimension_form="frequency",
        ),
    )


def _parameter_claim(claim_id: str, value: float, unit: str) -> ConflictClaim:
    return ConflictClaim(
        claim_id=claim_id,
        claim_type=ClaimType.PARAMETER,
        output_concept_id="c1",
        value=value,
        unit=unit,
    )


def test_detect_conflicts_unit_aware_same_value_no_conflict() -> None:
    records = detect_conflicts(
        [_parameter_claim("a", 200.0, "Hz"), _parameter_claim("b", 0.2, "kHz")],
        {"c1": _frequency_concept()},
        {},
        forms={"frequency": _frequency_form()},
    )
    assert records == []


def test_detect_conflicts_unit_aware_real_difference_reports_conflict() -> None:
    records = detect_conflicts(
        [_parameter_claim("a", 200.0, "Hz"), _parameter_claim("b", 300.0, "Hz")],
        {"c1": _frequency_concept()},
        {},
        forms={"frequency": _frequency_form()},
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
