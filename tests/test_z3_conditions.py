"""Tests for Z3-based condition reasoning and the soundness bug fix.

Tests the Z3 translation of CEL ASTs and the disjointness/equivalence
queries. Also includes regression tests for the fallback path soundness
bug where string-set disjointness was incorrectly treated as region
disjointness.
"""

from __future__ import annotations

import pytest

from compiler.conflict_detector import (
    ConflictClass,
    _classify_conditions,
    detect_conflicts,
)
from compiler.validate_claims import LoadedClaimFile


# ── Helpers ──────────────────────────────────────────────────────────


def make_parameter_claim(id, concept_id, value, unit="Hz", conditions=None):
    return {
        "id": id,
        "type": "parameter",
        "concept": concept_id,
        "value": value if isinstance(value, list) else [value],
        "unit": unit,
        "conditions": conditions or [],
        "provenance": {"paper": "test", "page": 1},
    }


def make_claim_file(claims, filename="test_paper"):
    from pathlib import Path
    return LoadedClaimFile(
        filename=filename,
        filepath=Path(f"/fake/{filename}.yaml"),
        data={"source": {"paper": filename}, "claims": claims},
    )


def make_concept_registry():
    return {
        "concept1": {
            "id": "concept1",
            "canonical_name": "fundamental_frequency",
            "form": "frequency",
            "status": "accepted",
            "definition": "F0",
        },
        "concept2": {
            "id": "concept2",
            "canonical_name": "subglottal_pressure",
            "form": "pressure",
            "status": "accepted",
            "definition": "Ps",
        },
        "concept3": {
            "id": "concept3",
            "canonical_name": "task",
            "form": "category",
            "form_parameters": {"values": ["speech", "singing"], "extensible": True},
            "status": "accepted",
            "definition": "Task type",
        },
    }


# ── Soundness bug regression ─────────────────────────────────────────


class TestSoundnessBugRegression:
    """Regression tests for the fallback path bug where string-set
    disjointness was treated as region disjointness."""

    def test_unparseable_string_disjoint_but_overlapping_regions(self):
        """Conditions with F1/F0 (division in name) can't be parsed by
        the simple regex. The old code returned PHI_NODE because the
        condition strings were different. But F1/F0 > 3.0 is a subset
        of F1/F0 > 2.0 — they OVERLAP, not disjoint."""
        result = _classify_conditions(
            ["F1/F0 > 3.0"],
            ["F1/F0 > 2.0"],
        )
        assert result == ConflictClass.OVERLAP

    def test_unparseable_conditions_no_common_strings(self):
        """When conditions are unparseable and have no common strings,
        the fallback should return OVERLAP (conservative), not PHI_NODE."""
        result = _classify_conditions(
            ["some_complex_expr(a, b) > 1"],
            ["other_complex_expr(c, d) < 5"],
        )
        assert result == ConflictClass.OVERLAP

    def test_unparseable_conditions_identical_strings(self):
        """Identical unparseable conditions should still be CONFLICT."""
        result = _classify_conditions(
            ["F1/F0 > 3.0"],
            ["F1/F0 > 3.0"],
        )
        assert result == ConflictClass.CONFLICT

    def test_soundness_via_detect_conflicts(self):
        """End-to-end: two claims with overlapping unparseable conditions
        should be OVERLAP, not PHI_NODE."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["F1/F0 > 3.0"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["F1/F0 > 2.0"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.OVERLAP


# ── Z3 module tests ──────────────────────────────────────────────────

try:
    import z3 as _z3  # noqa: F401
    from compiler.cel_checker import ConceptInfo, KindType
    from compiler.z3_conditions import Z3ConditionSolver
    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False

z3_only = pytest.mark.skipif(not HAS_Z3, reason="z3-solver not installed")


def _make_cel_registry():
    """Build a ConceptInfo registry for Z3 tests."""
    return {
        "fundamental_frequency": ConceptInfo(
            id="concept1",
            canonical_name="fundamental_frequency",
            kind=KindType.QUANTITY,
        ),
        "subglottal_pressure": ConceptInfo(
            id="concept2",
            canonical_name="subglottal_pressure",
            kind=KindType.QUANTITY,
        ),
        "task": ConceptInfo(
            id="concept3",
            canonical_name="task",
            kind=KindType.CATEGORY,
            category_values=["speech", "singing", "whisper"],
        ),
        "voiced": ConceptInfo(
            id="concept4",
            canonical_name="voiced",
            kind=KindType.BOOLEAN,
        ),
    }


@z3_only
class TestZ3Disjointness:
    """Test that Z3 correctly determines disjointness of condition sets."""

    def test_simple_numeric_disjoint(self):
        """F0 < 100 vs F0 > 200 are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["fundamental_frequency < 100"],
            ["fundamental_frequency > 200"],
        )

    def test_simple_numeric_overlapping(self):
        """F0 > 100 vs F0 > 200 overlap (everything > 200 satisfies both)."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["fundamental_frequency > 100"],
            ["fundamental_frequency > 200"],
        )

    def test_category_disjoint(self):
        """task == 'speech' vs task == 'singing' are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["task == 'speech'"],
            ["task == 'singing'"],
        )

    def test_category_same_value_not_disjoint(self):
        """task == 'speech' vs task == 'speech' are not disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["task == 'speech'"],
            ["task == 'speech'"],
        )

    def test_boolean_disjoint(self):
        """voiced == true vs voiced == false are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["voiced == true"],
            ["voiced == false"],
        )

    def test_boolean_same_not_disjoint(self):
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["voiced == true"],
            ["voiced == true"],
        )

    def test_mixed_concepts_disjoint(self):
        """Different category values make them disjoint even with same numeric."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["task == 'speech'", "fundamental_frequency > 100"],
            ["task == 'singing'", "fundamental_frequency > 100"],
        )


@z3_only
class TestZ3CompoundConditions:
    """Test &&, ||, and combinations."""

    def test_and_conditions_disjoint(self):
        """(F0 > 100 && F0 < 150) vs (F0 > 200 && F0 < 250) are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["fundamental_frequency > 100 && fundamental_frequency < 150"],
            ["fundamental_frequency > 200 && fundamental_frequency < 250"],
        )

    def test_and_conditions_overlapping(self):
        """(F0 > 100 && F0 < 250) vs (F0 > 200 && F0 < 350) overlap."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["fundamental_frequency > 100 && fundamental_frequency < 250"],
            ["fundamental_frequency > 200 && fundamental_frequency < 350"],
        )

    def test_or_condition(self):
        """(task == 'speech' || task == 'whisper') vs task == 'singing' are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["task == 'speech' || task == 'whisper'"],
            ["task == 'singing'"],
        )

    def test_or_condition_overlapping(self):
        """(task == 'speech' || task == 'singing') vs task == 'singing' overlap."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["task == 'speech' || task == 'singing'"],
            ["task == 'singing'"],
        )


@z3_only
class TestZ3InOperator:
    """Test the 'in' operator translation."""

    def test_in_list_disjoint(self):
        """task in ['speech', 'whisper'] vs task == 'singing' are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["task in ['speech', 'whisper']"],
            ["task == 'singing'"],
        )

    def test_in_list_overlapping(self):
        """task in ['speech', 'singing'] vs task == 'singing' overlap."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["task in ['speech', 'singing']"],
            ["task == 'singing'"],
        )


@z3_only
class TestZ3CrossConceptArithmetic:
    """Test arithmetic expressions across concepts (e.g. F0 / Ps > 2.0)."""

    def test_ratio_disjoint(self):
        """F0 / Ps > 3.0 vs F0 / Ps < 1.0 are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["fundamental_frequency / subglottal_pressure > 3.0"],
            ["fundamental_frequency / subglottal_pressure < 1.0"],
        )

    def test_ratio_overlapping(self):
        """F0 / Ps > 2.0 vs F0 / Ps > 3.0 overlap."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_disjoint(
            ["fundamental_frequency / subglottal_pressure > 2.0"],
            ["fundamental_frequency / subglottal_pressure > 3.0"],
        )


@z3_only
class TestZ3Negation:
    """Test negation (!) translation."""

    def test_negation_disjoint(self):
        """voiced == true vs !(voiced == true) are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["voiced == true"],
            ["!(voiced == true)"],
        )

    def test_negation_of_category(self):
        """task == 'speech' vs !(task == 'speech') are disjoint."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_disjoint(
            ["task == 'speech'"],
            ["!(task == 'speech')"],
        )


@z3_only
class TestZ3Equivalence:
    """Test equivalence detection (both A∧¬B and B∧¬A are UNSAT)."""

    def test_identical_conditions_equivalent(self):
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_equivalent(
            ["fundamental_frequency > 100"],
            ["fundamental_frequency > 100"],
        )

    def test_different_conditions_not_equivalent(self):
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert not solver.are_equivalent(
            ["fundamental_frequency > 100"],
            ["fundamental_frequency > 200"],
        )

    def test_reordered_conditions_equivalent(self):
        """Order shouldn't matter — conditions are conjuncted."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_equivalent(
            ["fundamental_frequency > 100", "task == 'speech'"],
            ["task == 'speech'", "fundamental_frequency > 100"],
        )

    def test_logically_equivalent_different_form(self):
        """!(F0 <= 100) is equivalent to F0 > 100."""
        registry = _make_cel_registry()
        solver = Z3ConditionSolver(registry)
        assert solver.are_equivalent(
            ["!(fundamental_frequency <= 100)"],
            ["fundamental_frequency > 100"],
        )


@z3_only
class TestZ3IntegrationWithConflictDetector:
    """Test that Z3 is wired into _classify_conditions properly."""

    def test_z3_detects_numeric_overlap(self):
        """Two claims with F0>100 and F0>200 should be OVERLAP, not PHI_NODE."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["fundamental_frequency > 100"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["fundamental_frequency > 200"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.OVERLAP

    def test_z3_detects_category_phi_node(self):
        """task == 'speech' vs task == 'singing' -> PHI_NODE."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["task == 'speech'"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["task == 'singing'"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.PHI_NODE

    def test_z3_detects_compound_overlap(self):
        """Compound conditions with partial overlap."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["fundamental_frequency > 100 && fundamental_frequency < 300"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["fundamental_frequency > 200 && fundamental_frequency < 400"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.OVERLAP

    def test_z3_detects_equivalent_as_conflict(self):
        """Logically equivalent conditions -> CONFLICT."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["!(fundamental_frequency <= 100)"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["fundamental_frequency > 100"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT
