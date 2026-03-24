"""Tests for the conflict detector.

Tests the classification of same-concept claim pairs:
- COMPATIBLE: same value (within tolerance) or overlapping ranges
- PHI_NODE: different values with different conditions
- CONFLICT: different values with identical conditions
- OVERLAP: different values with partially overlapping conditions
- PARAM_CONFLICT: conflict detected via parameterization chain
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st, settings

from propstore.conflict_detector import (
    ConflictClass,
    detect_conflicts,
)
from propstore.cel_checker import ConceptInfo, KindType
from propstore.validate_claims import LoadedClaimFile
from tests.conftest import make_concept_registry


# ── Test helpers ─────────────────────────────────────────────────────


def make_parameter_claim(id, concept_id, value, unit="Hz", conditions=None):
    """Build a minimal parameter claim dict for testing."""
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
    """Wrap claims in a LoadedClaimFile."""
    from pathlib import Path
    return LoadedClaimFile(
        filename=filename,
        filepath=Path(f"/fake/{filename}.yaml"),
        data={"source": {"paper": filename}, "claims": claims},
    )


# ── Conflict classification ─────────────────────────────────────────


class TestConflictClassification:
    def test_compatible_same_value(self):
        """Two claims, same concept, same value -> COMPATIBLE (not in output)."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0),
            make_parameter_claim("claim2", "concept1", 200.0),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        # COMPATIBLE pairs are not returned
        assert len(records) == 0

    def test_compatible_same_value_different_conditions(self):
        """Same value even with different conditions -> COMPATIBLE."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["task == 'speech'"]),
            make_parameter_claim("claim2", "concept1", 200.0,
                                 conditions=["task == 'singing'"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0

    def test_conflict_same_conditions_different_values(self):
        """Same concept, same conditions, different values -> CONFLICT."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["task == 'speech'"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["task == 'speech'"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT

    def test_conflict_both_unconditional(self):
        """Same concept, both unconditional, different values -> CONFLICT."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0),
            make_parameter_claim("claim2", "concept1", 350.0),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT

    def test_phi_node_different_conditions(self):
        """Same concept, different conditions, different values -> PHI_NODE."""
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

    def test_phi_node_disjoint_conditions(self):
        """Fully disjoint condition sets -> PHI_NODE."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["task == 'speech'", "fundamental_frequency > 100"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["task == 'singing'", "subglottal_pressure < 500"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.PHI_NODE

    def test_overlap_partial_conditions(self):
        """Partially overlapping conditions -> OVERLAP."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["task == 'speech'", "fundamental_frequency > 100"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["task == 'speech'", "subglottal_pressure < 500"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.OVERLAP

    def test_no_conflicts_different_concepts(self):
        """Claims for different concepts -> no conflicts."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0),
            make_parameter_claim("claim2", "concept2", 350.0),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0

    def test_multiple_claims_pairwise(self):
        """3+ claims for same concept -> all pairs checked."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0),
            make_parameter_claim("claim2", "concept1", 350.0),
            make_parameter_claim("claim3", "concept1", 500.0),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        # 3 claims, all unconditional, all different values -> 3 CONFLICT pairs
        # (0001,0002), (0001,0003), (0002,0003)
        assert len(records) == 3
        assert all(r.warning_class == ConflictClass.CONFLICT for r in records)


# ── Value comparison ─────────────────────────────────────────────────


class TestValueComparison:
    def test_scalar_equal_within_tolerance(self):
        """200.0 vs 200.0000000001 -> compatible."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0),
            make_parameter_claim("claim2", "concept1", 200.0000000001),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0

    def test_scalar_different(self):
        """200.0 vs 350.0 -> different."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0),
            make_parameter_claim("claim2", "concept1", 350.0),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1

    def test_range_overlap(self):
        """[100, 300] vs [200, 400] -> compatible (overlap)."""
        claims = [
            make_parameter_claim("claim1", "concept1", [100.0, 300.0]),
            make_parameter_claim("claim2", "concept1", [200.0, 400.0]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0

    def test_range_no_overlap(self):
        """[100, 200] vs [300, 400] -> different."""
        claims = [
            make_parameter_claim("claim1", "concept1", [100.0, 200.0]),
            make_parameter_claim("claim2", "concept1", [300.0, 400.0]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1


# ── Parameterization conflict ───────────────────────────────────────


class TestParameterizationConflict:
    def _make_param_registry(self):
        """Registry with a parameterization relationship: ra = ta / T0."""
        return {
            "concept10": {
                "id": "concept10",
                "canonical_name": "open_quotient",
                "form": "duration_ratio",
                "status": "accepted",
                "definition": "ra = ta / T0",
                "parameterization_relationships": [
                    {
                        "inputs": ["concept11", "concept12"],
                        "sympy": "concept11 / concept12",
                        "exactness": "exact",
                    }
                ],
            },
            "concept11": {
                "id": "concept11",
                "canonical_name": "return_time",
                "form": "time",
                "status": "accepted",
                "definition": "ta",
            },
            "concept12": {
                "id": "concept12",
                "canonical_name": "period",
                "form": "time",
                "status": "accepted",
                "definition": "T0",
            },
        }

    def test_param_conflict_detected(self):
        """Derived value from parameterization conflicts with direct claim -> PARAM_CONFLICT."""
        pytest.importorskip("sympy")
        registry = self._make_param_registry()
        claims = [
            # Direct claim: ra = 5%
            make_parameter_claim("claim1", "concept10", 5.0, unit="%"),
            # Inputs: ta = 0.001, T0 = 0.01 => ra = 0.001/0.01 = 0.1 = 10%... wait
            # Let's use simpler numbers: ta=1, T0=10 => ra = 0.1, but claim says 5.0
            make_parameter_claim("claim2", "concept11", 1.0, unit="s"),
            make_parameter_claim("claim3", "concept12", 10.0, unit="s"),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], registry)
        # Should find PARAM_CONFLICT: derived ra = 1/10 = 0.1, but claimed ra = 5.0
        param_conflicts = [r for r in records if r.warning_class == ConflictClass.PARAM_CONFLICT]
        assert len(param_conflicts) >= 1
        assert param_conflicts[0].concept_id == "concept10"
        assert param_conflicts[0].derivation_chain is not None

    def test_param_no_conflict_approximate(self):
        """Approximate parameterization -> skip, no PARAM_CONFLICT."""
        pytest.importorskip("sympy")
        registry = {
            "concept10": {
                "id": "concept10",
                "canonical_name": "open_quotient",
                "form": "duration_ratio",
                "status": "accepted",
                "definition": "ra ~ ta / T0",
                "parameterization_relationships": [
                    {
                        "inputs": ["concept11", "concept12"],
                        "sympy": "concept11 / concept12",
                        "exactness": "approximate",
                    }
                ],
            },
            "concept11": {
                "id": "concept11",
                "canonical_name": "return_time",
                "form": "time",
                "status": "accepted",
                "definition": "ta",
            },
            "concept12": {
                "id": "concept12",
                "canonical_name": "period",
                "form": "time",
                "status": "accepted",
                "definition": "T0",
            },
        }
        claims = [
            make_parameter_claim("claim1", "concept10", 5.0, unit="%"),
            make_parameter_claim("claim2", "concept11", 1.0, unit="s"),
            make_parameter_claim("claim3", "concept12", 10.0, unit="s"),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], registry)
        param_conflicts = [r for r in records if r.warning_class == ConflictClass.PARAM_CONFLICT]
        assert len(param_conflicts) == 0


# ── Symmetry (Hypothesis property tests) ────────────────────────────


class TestSymmetry:
    @given(
        val_a=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        val_b=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_classification_symmetric(self, val_a, val_b):
        """If classify(A, B) = X then classify(B, A) = X."""
        registry = make_concept_registry()

        claims_ab = [
            make_parameter_claim("claim1", "concept1", val_a),
            make_parameter_claim("claim2", "concept1", val_b),
        ]
        cf_ab = make_claim_file(claims_ab)
        records_ab = detect_conflicts([cf_ab], registry)

        claims_ba = [
            make_parameter_claim("claim2", "concept1", val_b),
            make_parameter_claim("claim1", "concept1", val_a),
        ]
        cf_ba = make_claim_file(claims_ba)
        records_ba = detect_conflicts([cf_ba], registry)

        assert len(records_ab) == len(records_ba)
        if records_ab:
            assert records_ab[0].warning_class == records_ba[0].warning_class

    @given(
        val=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_compatible_is_reflexive(self, val):
        """classify(A, A) is always COMPATIBLE."""
        registry = make_concept_registry()
        claims = [
            make_parameter_claim("claim1", "concept1", val),
            make_parameter_claim("claim2", "concept1", val),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], registry)
        # Same value -> COMPATIBLE -> not in output
        assert len(records) == 0


# ── Record fields ────────────────────────────────────────────────────


class TestRecordFields:
    def test_conflict_record_has_correct_fields(self):
        """ConflictRecord should have all expected fields."""
        claims = [
            make_parameter_claim("claim1", "concept1", 200.0,
                                 conditions=["task == 'speech'"]),
            make_parameter_claim("claim2", "concept1", 350.0,
                                 conditions=["task == 'speech'"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        r = records[0]
        assert r.concept_id == "concept1"
        assert r.claim_a_id == "claim1"
        assert r.claim_b_id == "claim2"
        assert r.warning_class == ConflictClass.CONFLICT
        assert r.conditions_a == ["task == 'speech'"]
        assert r.conditions_b == ["task == 'speech'"]
        assert r.derivation_chain is None

    def test_cross_file_conflicts(self):
        """Conflicts detected across different claim files."""
        cf1 = make_claim_file(
            [make_parameter_claim("claim1", "concept1", 200.0)],
            filename="paper_a",
        )
        cf2 = make_claim_file(
            [make_parameter_claim("claim2", "concept1", 350.0)],
            filename="paper_b",
        )
        records = detect_conflicts([cf1, cf2], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT


# ── Named value field conflict detection ─────────────────────────────


def _make_named_claim(id, concept_id, unit="Hz", conditions=None, **fields):
    """Build a parameter claim with named value fields (value, lower_bound, upper_bound)."""
    c = {
        "id": id,
        "type": "parameter",
        "concept": concept_id,
        "unit": unit,
        "conditions": conditions or [],
        "provenance": {"paper": "test", "page": 1},
    }
    c.update(fields)
    return c


class TestNamedValueConflicts:
    def test_point_vs_range_compatible(self):
        """value: 0.7 vs lower_bound: 0.5, upper_bound: 0.9 -> COMPATIBLE (0.7 in range)."""
        claims = [
            _make_named_claim("claim1", "concept1", value=0.7),
            _make_named_claim("claim2", "concept1", lower_bound=0.5, upper_bound=0.9),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0

    def test_point_vs_point_conflict(self):
        """value: 0.7 vs value: 0.8 -> CONFLICT (different point values)."""
        claims = [
            _make_named_claim("claim1", "concept1", value=0.7),
            _make_named_claim("claim2", "concept1", value=0.8),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT

    def test_point_vs_point_compatible(self):
        """value: 0.7 vs value: 0.7 -> COMPATIBLE."""
        claims = [
            _make_named_claim("claim1", "concept1", value=0.7),
            _make_named_claim("claim2", "concept1", value=0.7),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0

    def test_range_vs_range_compatible_overlap(self):
        """[0.5, 0.9] vs [0.6, 1.0] -> COMPATIBLE (overlap)."""
        claims = [
            _make_named_claim("claim1", "concept1", lower_bound=0.5, upper_bound=0.9),
            _make_named_claim("claim2", "concept1", lower_bound=0.6, upper_bound=1.0),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0

    def test_range_vs_range_conflict_no_overlap(self):
        """[0.5, 0.6] vs [0.8, 1.0] -> CONFLICT (no overlap)."""
        claims = [
            _make_named_claim("claim1", "concept1", lower_bound=0.5, upper_bound=0.6),
            _make_named_claim("claim2", "concept1", lower_bound=0.8, upper_bound=1.0),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT


# ── Measurement claim conflict detection ─────────────────────────────


def _make_measurement_claim(id, target_concept, measure, value, unit="ratio",
                            conditions=None, **fields):
    """Build a measurement claim dict for testing."""
    c = {
        "id": id,
        "type": "measurement",
        "target_concept": target_concept,
        "measure": measure,
        "value": value,
        "unit": unit,
        "conditions": conditions or [],
        "provenance": {"paper": "test", "page": 1},
    }
    c.update(fields)
    return c


def _make_equation_claim(id, expression, variables, conditions=None, **fields):
    c = {
        "id": id,
        "type": "equation",
        "expression": expression,
        "variables": variables,
        "conditions": conditions or [],
        "provenance": {"paper": "test", "page": 1},
    }
    c.update(fields)
    return c


class TestMeasurementConflicts:
    def test_measurement_vs_parameter_never_compared(self):
        """Measurement claim vs parameter claim for same concept -> NEVER compared."""
        claims = [
            make_parameter_claim("claim1", "concept2", 100.0, unit="Pa"),
            _make_measurement_claim("claim2", "concept2", "jnd_absolute", 0.14),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        # No conflicts: different types are grouped separately
        assert len(records) == 0

    def test_measurement_same_target_measure_different_value_conflict(self):
        """Two measurements: same target_concept + measure, different value -> CONFLICT."""
        claims = [
            _make_measurement_claim("claim1", "concept2", "jnd_absolute", 0.14),
            _make_measurement_claim("claim2", "concept2", "jnd_absolute", 0.25),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT

    def test_measurement_different_listener_population_phi_node(self):
        """Two measurements: same target + measure, different listener_population -> PHI_NODE."""
        claims = [
            _make_measurement_claim("claim1", "concept2", "jnd_absolute", 0.14,
                                    listener_population="native_english"),
            _make_measurement_claim("claim2", "concept2", "jnd_absolute", 0.25,
                                    listener_population="native_mandarin"),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.PHI_NODE

    def test_measurement_same_target_measure_same_value_compatible(self):
        """Two measurements: same target + measure, same value -> COMPATIBLE."""
        claims = [
            _make_measurement_claim("claim1", "concept2", "jnd_absolute", 0.14),
            _make_measurement_claim("claim2", "concept2", "jnd_absolute", 0.14),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0


class TestSemanticConditionClassification:
    def test_numeric_subset_conditions_overlap(self):
        claims = [
            make_parameter_claim(
                "claim1",
                "concept1",
                200.0,
                conditions=["fundamental_frequency > 100"],
            ),
            make_parameter_claim(
                "claim2",
                "concept1",
                350.0,
                conditions=["fundamental_frequency > 200"],
            ),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.OVERLAP

    def test_numeric_disjoint_conditions_phi_node(self):
        claims = [
            make_parameter_claim(
                "claim1",
                "concept1",
                200.0,
                conditions=["fundamental_frequency < 100"],
            ),
            make_parameter_claim(
                "claim2",
                "concept1",
                350.0,
                conditions=["fundamental_frequency > 200"],
            ),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.PHI_NODE


class TestEquationConflicts:
    def test_equation_conflict_same_relation_detected(self):
        claims = [
            _make_equation_claim(
                "claim1",
                "log(Ps) = 1.00 + 0.88 * log(F0)",
                [
                    {"symbol": "Ps", "concept": "concept2", "role": "dependent"},
                    {"symbol": "F0", "concept": "concept1", "role": "independent"},
                ],
                conditions=["task == 'speech'"],
            ),
            _make_equation_claim(
                "claim2",
                "log(Ps) = 1.10 + 0.90 * log(F0)",
                [
                    {"symbol": "Ps", "concept": "concept2", "role": "dependent"},
                    {"symbol": "F0", "concept": "concept1", "role": "independent"},
                ],
                conditions=["task == 'speech'"],
            ),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].concept_id == "concept2"
        assert records[0].warning_class == ConflictClass.CONFLICT

    def test_equation_conflict_uses_condition_classification(self):
        claims = [
            _make_equation_claim(
                "claim1",
                "log(Ps) = 1.00 + 0.88 * log(F0)",
                [
                    {"symbol": "Ps", "concept": "concept2", "role": "dependent"},
                    {"symbol": "F0", "concept": "concept1", "role": "independent"},
                ],
                conditions=["task == 'speech'"],
            ),
            _make_equation_claim(
                "claim2",
                "log(Ps) = 1.10 + 0.90 * log(F0)",
                [
                    {"symbol": "Ps", "concept": "concept2", "role": "dependent"},
                    {"symbol": "F0", "concept": "concept1", "role": "independent"},
                ],
                conditions=["task == 'singing'"],
            ),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.PHI_NODE


# ── Algorithm claim conflict detection ────────────────────────────────


def _make_algorithm_claim(id, body, variables, conditions=None, **fields):
    """Build an algorithm claim dict for testing."""
    claim = {
        "id": id,
        "type": "algorithm",
        "body": body,
        "variables": variables,
        "conditions": conditions or [],
        "provenance": {"paper": "test", "page": 1},
    }
    claim.update(fields)
    return claim


class TestAlgorithmConflicts:
    def test_algorithm_conflict_uses_declared_output_concept(self):
        claims = [
            _make_algorithm_claim(
                "algo1",
                "def compute(x):\n    return x * 2 + 1",
                [{"name": "x", "concept": "concept_in"}],
                concept="concept_out",
            ),
            _make_algorithm_claim(
                "algo2",
                "def calc(val):\n    return val ** 3 - 10",
                [{"name": "val", "concept": "concept_in"}],
                concept="concept_out",
            ),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        algo_records = [r for r in records if r.value_a.startswith("algorithm:")]
        assert len(algo_records) == 1
        assert algo_records[0].concept_id == "concept_out"

    def test_algorithm_equivalent_no_conflict(self):
        """Two equivalent algorithm claims (same logic, different var names) -> no conflict."""
        claims = [
            _make_algorithm_claim(
                "algo1",
                "def compute(x):\n    return x * 2 + 1",
                [
                    {"name": "x", "concept": "concept1"},
                ],
                concept="concept1",
            ),
            _make_algorithm_claim(
                "algo2",
                "def calc(val):\n    return val * 2 + 1",
                [
                    {"name": "val", "concept": "concept1"},
                ],
                concept="concept1",
            ),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        algo_records = [r for r in records if r.concept_id == "concept1"]
        assert len(algo_records) == 0

    def test_algorithm_different_conflict(self):
        """Two genuinely different algorithm claims for same concept -> conflict detected."""
        claims = [
            _make_algorithm_claim(
                "algo1",
                "def compute(x):\n    return x * 2 + 1",
                [
                    {"name": "x", "concept": "concept1"},
                ],
                concept="concept1",
            ),
            _make_algorithm_claim(
                "algo2",
                "def calc(val):\n    return val ** 3 - 10",
                [
                    {"name": "val", "concept": "concept1"},
                ],
                concept="concept1",
            ),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        algo_records = [r for r in records if r.value_a.startswith("algorithm:")]
        assert len(algo_records) == 1
        assert algo_records[0].concept_id == "concept1"
        assert algo_records[0].value_a == "algorithm:algo1"
        assert algo_records[0].value_b == "algorithm:algo2"
        assert "similarity:" in algo_records[0].derivation_chain

    def test_algorithm_different_concepts_no_conflict(self):
        """Algorithm claims for different concepts -> no conflict (not compared)."""
        claims = [
            _make_algorithm_claim(
                "algo1",
                "def compute(x):\n    return x * 2 + 1",
                [
                    {"name": "x", "concept": "concept1"},
                ],
                concept="concept1",
            ),
            _make_algorithm_claim(
                "algo2",
                "def calc(val):\n    return val ** 3 - 10",
                [
                    {"name": "val", "concept": "concept2"},
                ],
                concept="concept2",
            ),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        algo_records = [r for r in records if r.value_a.startswith("algorithm:")]
        assert len(algo_records) == 0

    @given(
        var_a=st.sampled_from(["x", "signal", "sample"]),
        var_b=st.sampled_from(["value", "frame", "obs"]),
    )
    @settings(max_examples=20)
    def test_algorithm_output_ownership_independent_of_variable_names(self, var_a, var_b):
        """Output-concept ownership survives variable renaming."""
        claims = [
            _make_algorithm_claim(
                "algo1",
                f"def compute({var_a}):\n    return {var_a} * 2 + 1",
                [{"name": var_a, "concept": "concept_in"}],
                concept="concept_out",
            ),
            _make_algorithm_claim(
                "algo2",
                f"def calc({var_b}):\n    return {var_b} ** 3 - 10",
                [{"name": var_b, "concept": "concept_in"}],
                concept="concept_out",
            ),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        algo_records = [r for r in records if r.value_a.startswith("algorithm:")]
        assert len(algo_records) == 1
        assert algo_records[0].concept_id == "concept_out"

    def test_algorithm_conditional_overlap(self):
        """Two algorithm claims with overlapping conditions -> appropriate classification."""
        claims = [
            _make_algorithm_claim(
                "algo1",
                "def compute(x):\n    return x * 2 + 1",
                [
                    {"name": "x", "concept": "concept1"},
                ],
                conditions=["task == 'speech'", "fundamental_frequency > 100"],
                concept="concept1",
            ),
            _make_algorithm_claim(
                "algo2",
                "def calc(val):\n    return val ** 3 - 10",
                [
                    {"name": "val", "concept": "concept1"},
                ],
                conditions=["task == 'speech'", "subglottal_pressure < 500"],
                concept="concept1",
            ),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        algo_records = [r for r in records if r.value_a.startswith("algorithm:")]
        assert len(algo_records) == 1
        assert algo_records[0].warning_class == ConflictClass.OVERLAP


class TestTransitiveContextSemantics:
    def test_transitive_conflicts_in_unrelated_contexts_not_suppressed(self):
        """Unrelated contexts no longer suppress transitive conflicts.

        Previously, unrelated contexts fell through to CONTEXT_PHI_NODE,
        silently suppressing real conflicts. Now condition analysis runs,
        revealing the actual PARAM_CONFLICT.
        """
        from propstore.conflict_detector import detect_transitive_conflicts
        from propstore.validate_contexts import ContextHierarchy, LoadedContext

        registry = {
            "concept_out": {
                "id": "concept_out",
                "canonical_name": "concept_out",
                "form": "frequency",
                "status": "accepted",
                "definition": "output",
                "parameterization_relationships": [
                    {
                        "inputs": ["concept_mid"],
                        "sympy": "concept_mid * 2",
                        "exactness": "exact",
                    }
                ],
            },
            "concept_mid": {
                "id": "concept_mid",
                "canonical_name": "concept_mid",
                "form": "frequency",
                "status": "accepted",
                "definition": "middle",
                "parameterization_relationships": [
                    {
                        "inputs": ["concept_in"],
                        "sympy": "concept_in * 3",
                        "exactness": "exact",
                    }
                ],
            },
            "concept_in": {
                "id": "concept_in",
                "canonical_name": "concept_in",
                "form": "frequency",
                "status": "accepted",
                "definition": "input",
            },
        }
        claims = [
            make_parameter_claim(
                "direct_out",
                "concept_out",
                100.0,
                conditions=["task == 'speech'"],
            ) | {"context": "ctx_root"},
            make_parameter_claim(
                "source_in",
                "concept_in",
                10.0,
                conditions=["task == 'speech'"],
            ) | {"context": "ctx_other"},
        ]
        cf = make_claim_file(claims)
        hierarchy = ContextHierarchy([
            LoadedContext("root", None, {"id": "ctx_root", "name": "Root"}),
            LoadedContext("other", None, {"id": "ctx_other", "name": "Other"}),
        ])

        records = detect_transitive_conflicts(
            [cf],
            registry,
            context_hierarchy=hierarchy,
        )

        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.PARAM_CONFLICT
        assert records[0].concept_id == "concept_out"

    def test_unrelated_contexts_do_not_suppress_direct_conflicts(self):
        """Claims in unrelated contexts should NOT be suppressed as CONTEXT_PHI_NODE.

        Two contexts with no hierarchy relationship (not excluded, not visible)
        should let condition analysis decide, not silently classify as phi-node.
        """
        from propstore.validate_contexts import ContextHierarchy, LoadedContext

        claims = [
            make_parameter_claim(
                "claim_a", "concept1", 200.0,
                conditions=["task == 'speech'"],
            ) | {"context": "ctx_alpha"},
            make_parameter_claim(
                "claim_b", "concept1", 350.0,
                conditions=["task == 'speech'"],
            ) | {"context": "ctx_beta"},
        ]
        cf = make_claim_file(claims)
        hierarchy = ContextHierarchy([
            LoadedContext("alpha", None, {"id": "ctx_alpha", "name": "Alpha"}),
            LoadedContext("beta", None, {"id": "ctx_beta", "name": "Beta"}),
        ])

        records = detect_conflicts(
            [cf],
            make_concept_registry(),
            context_hierarchy=hierarchy,
        )

        # Unrelated contexts must NOT suppress the conflict as CONTEXT_PHI_NODE.
        # The pair has same conditions + different values = real CONFLICT.
        phi_records = [r for r in records if r.warning_class == ConflictClass.CONTEXT_PHI_NODE]
        assert len(phi_records) == 0, (
            f"Expected no CONTEXT_PHI_NODE for unrelated contexts, got {phi_records}"
        )
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT


# ── Exception-handling tests (Group 2) ──────────────────────────────


class TestAlgorithmExceptionHandling:
    def test_value_error_skipped(self):
        """ValueError from ast_compare should skip the pair, not crash."""
        from unittest.mock import patch
        from propstore.conflict_detector.algorithms import detect_algorithm_conflicts

        cf = make_claim_file([
            {
                "id": "alg1",
                "type": "algorithm",
                "concept": "concept_algo",
                "body": "x + 1",
                "variables": {"x": "input"},
            },
            {
                "id": "alg2",
                "type": "algorithm",
                "concept": "concept_algo",
                "body": "x + 2",
                "variables": {"x": "input"},
            },
        ])
        registry = {"concept_algo": ConceptInfo(
            id="concept_algo", canonical_name="concept_algo", kind=KindType.QUANTITY,
        )}

        with patch(
            "propstore.conflict_detector.algorithms.ast_compare",
            side_effect=ValueError("bad parse"),
        ):
            records = detect_algorithm_conflicts([cf], registry)

        # Pair was skipped — no crash, no records from this pair
        assert isinstance(records, list)

    def test_unexpected_error_propagates(self):
        """RuntimeError from ast_compare should propagate."""
        from unittest.mock import patch
        from propstore.conflict_detector.algorithms import detect_algorithm_conflicts

        cf = make_claim_file([
            {
                "id": "alg1",
                "type": "algorithm",
                "concept": "concept_algo",
                "body": "x + 1",
                "variables": {"x": "input"},
            },
            {
                "id": "alg2",
                "type": "algorithm",
                "concept": "concept_algo",
                "body": "x + 2",
                "variables": {"x": "input"},
            },
        ])
        registry = {"concept_algo": ConceptInfo(
            id="concept_algo", canonical_name="concept_algo", kind=KindType.QUANTITY,
        )}

        with patch(
            "propstore.conflict_detector.algorithms.ast_compare",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError, match="unexpected"):
                detect_algorithm_conflicts([cf], registry)


class TestParameterZ3FallbackHandling:
    def test_z3_partition_error_falls_back_to_pairwise(self):
        """Z3 partition failure should fall back to pairwise detection."""
        from unittest.mock import patch
        from propstore.z3_conditions import Z3TranslationError, Z3ConditionSolver
        from propstore.conflict_detector.parameters import detect_parameter_conflicts

        cel_registry = {"freq": ConceptInfo(
            id="freq", canonical_name="freq", kind=KindType.QUANTITY,
        )}
        solver = Z3ConditionSolver(cel_registry)

        # 3 claims triggers the Z3 partition path
        cf = make_claim_file([
            {"id": "p1", "type": "parameter", "concept": "freq", "body": "100", "conditions": ["freq > 50"]},
            {"id": "p2", "type": "parameter", "concept": "freq", "body": "200", "conditions": ["freq > 50"]},
            {"id": "p3", "type": "parameter", "concept": "freq", "body": "300", "conditions": ["freq > 50"]},
        ])

        with patch.object(
            solver,
            "partition_equivalence_classes",
            side_effect=Z3TranslationError("partition failed"),
        ):
            records, _ = detect_parameter_conflicts([cf], cel_registry, solver=solver)

        # Should not crash — falls back to pairwise
        assert isinstance(records, list)

    def test_z3_partition_unexpected_error_propagates(self):
        """RuntimeError in partition should propagate."""
        from unittest.mock import patch
        from propstore.z3_conditions import Z3ConditionSolver
        from propstore.conflict_detector.parameters import detect_parameter_conflicts

        cel_registry = {"freq": ConceptInfo(
            id="freq", canonical_name="freq", kind=KindType.QUANTITY,
        )}
        solver = Z3ConditionSolver(cel_registry)

        cf = make_claim_file([
            {"id": "p1", "type": "parameter", "concept": "freq", "body": "100", "conditions": ["freq > 50"]},
            {"id": "p2", "type": "parameter", "concept": "freq", "body": "200", "conditions": ["freq > 50"]},
            {"id": "p3", "type": "parameter", "concept": "freq", "body": "300", "conditions": ["freq > 50"]},
        ])

        with patch.object(
            solver,
            "partition_equivalence_classes",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError, match="unexpected"):
                detect_parameter_conflicts([cf], cel_registry, solver=solver)

    def test_z3_disjoint_unexpected_error_propagates(self):
        """RuntimeError in are_disjoint should propagate, not be swallowed."""
        from unittest.mock import patch
        from propstore.z3_conditions import Z3ConditionSolver
        from propstore.conflict_detector.parameters import detect_parameter_conflicts

        cel_registry = {"freq": ConceptInfo(
            id="freq", canonical_name="freq", kind=KindType.QUANTITY,
        )}
        solver = Z3ConditionSolver(cel_registry)

        cf = make_claim_file([
            {"id": "p1", "type": "parameter", "concept": "freq", "body": "100", "conditions": ["freq > 50"]},
            {"id": "p2", "type": "parameter", "concept": "freq", "body": "200", "conditions": ["freq > 50"]},
            {"id": "p3", "type": "parameter", "concept": "freq", "body": "300", "conditions": ["freq < 10"]},
        ])

        with patch.object(
            solver,
            "partition_equivalence_classes",
            return_value=[[0, 1], [2]],
        ), patch.object(
            solver,
            "are_disjoint",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError, match="unexpected"):
                detect_parameter_conflicts([cf], cel_registry, solver=solver)
