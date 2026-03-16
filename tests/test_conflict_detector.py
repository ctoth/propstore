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

from compiler.conflict_detector import (
    ConflictClass,
    ConflictRecord,
    detect_conflicts,
)
from compiler.validate_claims import LoadedClaimFile


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


def make_concept_registry():
    """Build a mock concept registry for testing."""
    return {
        "speech_0001": {
            "id": "speech_0001",
            "canonical_name": "fundamental_frequency",
            "kind": {"quantity": {"unit": "Hz"}},
            "status": "accepted",
            "definition": "F0",
        },
        "speech_0002": {
            "id": "speech_0002",
            "canonical_name": "subglottal_pressure",
            "kind": {"quantity": {"unit": "Pa"}},
            "status": "accepted",
            "definition": "Ps",
        },
        "speech_0003": {
            "id": "speech_0003",
            "canonical_name": "task",
            "kind": {"category": {"values": ["speech", "singing"], "extensible": True}},
            "status": "accepted",
            "definition": "Task type",
        },
    }


# ── Conflict classification ─────────────────────────────────────────


class TestConflictClassification:
    def test_compatible_same_value(self):
        """Two claims, same concept, same value -> COMPATIBLE (not in output)."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", 200.0),
            make_parameter_claim("claim_0002", "speech_0001", 200.0),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        # COMPATIBLE pairs are not returned
        assert len(records) == 0

    def test_compatible_same_value_different_conditions(self):
        """Same value even with different conditions -> COMPATIBLE."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", 200.0,
                                 conditions=["task == 'speech'"]),
            make_parameter_claim("claim_0002", "speech_0001", 200.0,
                                 conditions=["task == 'singing'"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0

    def test_conflict_same_conditions_different_values(self):
        """Same concept, same conditions, different values -> CONFLICT."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", 200.0,
                                 conditions=["task == 'speech'"]),
            make_parameter_claim("claim_0002", "speech_0001", 350.0,
                                 conditions=["task == 'speech'"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT

    def test_conflict_both_unconditional(self):
        """Same concept, both unconditional, different values -> CONFLICT."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", 200.0),
            make_parameter_claim("claim_0002", "speech_0001", 350.0),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT

    def test_phi_node_different_conditions(self):
        """Same concept, different conditions, different values -> PHI_NODE."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", 200.0,
                                 conditions=["task == 'speech'"]),
            make_parameter_claim("claim_0002", "speech_0001", 350.0,
                                 conditions=["task == 'singing'"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.PHI_NODE

    def test_phi_node_disjoint_conditions(self):
        """Fully disjoint condition sets -> PHI_NODE."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", 200.0,
                                 conditions=["task == 'speech'", "fundamental_frequency > 100"]),
            make_parameter_claim("claim_0002", "speech_0001", 350.0,
                                 conditions=["task == 'singing'", "subglottal_pressure < 500"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.PHI_NODE

    def test_overlap_partial_conditions(self):
        """Partially overlapping conditions -> OVERLAP."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", 200.0,
                                 conditions=["task == 'speech'", "fundamental_frequency > 100"]),
            make_parameter_claim("claim_0002", "speech_0001", 350.0,
                                 conditions=["task == 'speech'", "subglottal_pressure < 500"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.OVERLAP

    def test_no_conflicts_different_concepts(self):
        """Claims for different concepts -> no conflicts."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", 200.0),
            make_parameter_claim("claim_0002", "speech_0002", 350.0),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0

    def test_multiple_claims_pairwise(self):
        """3+ claims for same concept -> all pairs checked."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", 200.0),
            make_parameter_claim("claim_0002", "speech_0001", 350.0),
            make_parameter_claim("claim_0003", "speech_0001", 500.0),
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
            make_parameter_claim("claim_0001", "speech_0001", 200.0),
            make_parameter_claim("claim_0002", "speech_0001", 200.0000000001),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0

    def test_scalar_different(self):
        """200.0 vs 350.0 -> different."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", 200.0),
            make_parameter_claim("claim_0002", "speech_0001", 350.0),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1

    def test_range_overlap(self):
        """[100, 300] vs [200, 400] -> compatible (overlap)."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", [100.0, 300.0]),
            make_parameter_claim("claim_0002", "speech_0001", [200.0, 400.0]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 0

    def test_range_no_overlap(self):
        """[100, 200] vs [300, 400] -> different."""
        claims = [
            make_parameter_claim("claim_0001", "speech_0001", [100.0, 200.0]),
            make_parameter_claim("claim_0002", "speech_0001", [300.0, 400.0]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1


# ── Parameterization conflict ───────────────────────────────────────


class TestParameterizationConflict:
    def _make_param_registry(self):
        """Registry with a parameterization relationship: ra = ta / T0."""
        return {
            "speech_0010": {
                "id": "speech_0010",
                "canonical_name": "open_quotient",
                "kind": {"quantity": {"unit": "%"}},
                "status": "accepted",
                "definition": "ra = ta / T0",
                "parameterization_relationships": [
                    {
                        "inputs": ["speech_0011", "speech_0012"],
                        "sympy": "speech_0011 / speech_0012",
                        "exactness": "exact",
                    }
                ],
            },
            "speech_0011": {
                "id": "speech_0011",
                "canonical_name": "return_time",
                "kind": {"quantity": {"unit": "s"}},
                "status": "accepted",
                "definition": "ta",
            },
            "speech_0012": {
                "id": "speech_0012",
                "canonical_name": "period",
                "kind": {"quantity": {"unit": "s"}},
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
            make_parameter_claim("claim_0001", "speech_0010", 5.0, unit="%"),
            # Inputs: ta = 0.001, T0 = 0.01 => ra = 0.001/0.01 = 0.1 = 10%... wait
            # Let's use simpler numbers: ta=1, T0=10 => ra = 0.1, but claim says 5.0
            make_parameter_claim("claim_0002", "speech_0011", 1.0, unit="s"),
            make_parameter_claim("claim_0003", "speech_0012", 10.0, unit="s"),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], registry)
        # Should find PARAM_CONFLICT: derived ra = 1/10 = 0.1, but claimed ra = 5.0
        param_conflicts = [r for r in records if r.warning_class == ConflictClass.PARAM_CONFLICT]
        assert len(param_conflicts) >= 1
        assert param_conflicts[0].concept_id == "speech_0010"
        assert param_conflicts[0].derivation_chain is not None

    def test_param_no_conflict_approximate(self):
        """Approximate parameterization -> skip, no PARAM_CONFLICT."""
        pytest.importorskip("sympy")
        registry = {
            "speech_0010": {
                "id": "speech_0010",
                "canonical_name": "open_quotient",
                "kind": {"quantity": {"unit": "%"}},
                "status": "accepted",
                "definition": "ra ~ ta / T0",
                "parameterization_relationships": [
                    {
                        "inputs": ["speech_0011", "speech_0012"],
                        "sympy": "speech_0011 / speech_0012",
                        "exactness": "approximate",
                    }
                ],
            },
            "speech_0011": {
                "id": "speech_0011",
                "canonical_name": "return_time",
                "kind": {"quantity": {"unit": "s"}},
                "status": "accepted",
                "definition": "ta",
            },
            "speech_0012": {
                "id": "speech_0012",
                "canonical_name": "period",
                "kind": {"quantity": {"unit": "s"}},
                "status": "accepted",
                "definition": "T0",
            },
        }
        claims = [
            make_parameter_claim("claim_0001", "speech_0010", 5.0, unit="%"),
            make_parameter_claim("claim_0002", "speech_0011", 1.0, unit="s"),
            make_parameter_claim("claim_0003", "speech_0012", 10.0, unit="s"),
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
            make_parameter_claim("claim_0001", "speech_0001", val_a),
            make_parameter_claim("claim_0002", "speech_0001", val_b),
        ]
        cf_ab = make_claim_file(claims_ab)
        records_ab = detect_conflicts([cf_ab], registry)

        claims_ba = [
            make_parameter_claim("claim_0002", "speech_0001", val_b),
            make_parameter_claim("claim_0001", "speech_0001", val_a),
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
            make_parameter_claim("claim_0001", "speech_0001", val),
            make_parameter_claim("claim_0002", "speech_0001", val),
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
            make_parameter_claim("claim_0001", "speech_0001", 200.0,
                                 conditions=["task == 'speech'"]),
            make_parameter_claim("claim_0002", "speech_0001", 350.0,
                                 conditions=["task == 'speech'"]),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], make_concept_registry())
        assert len(records) == 1
        r = records[0]
        assert r.concept_id == "speech_0001"
        assert r.claim_a_id == "claim_0001"
        assert r.claim_b_id == "claim_0002"
        assert r.warning_class == ConflictClass.CONFLICT
        assert r.conditions_a == ["task == 'speech'"]
        assert r.conditions_b == ["task == 'speech'"]
        assert r.derivation_chain is None

    def test_cross_file_conflicts(self):
        """Conflicts detected across different claim files."""
        cf1 = make_claim_file(
            [make_parameter_claim("claim_0001", "speech_0001", 200.0)],
            filename="paper_a",
        )
        cf2 = make_claim_file(
            [make_parameter_claim("claim_0002", "speech_0001", 350.0)],
            filename="paper_b",
        )
        records = detect_conflicts([cf1, cf2], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONFLICT
