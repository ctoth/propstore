"""Tests for the conflict detector.

Tests the classification of same-concept claim pairs:
- COMPATIBLE: same value (within tolerance) or overlapping ranges
- PHI_NODE: different values with different conditions
- CONFLICT: different values with identical conditions
- OVERLAP: different values with partially overlapping conditions
- PARAM_CONFLICT: conflict detected via parameterization chain
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from hypothesis import given, strategies as st, settings

from propstore.conflict_detector import (
    ConflictClass,
    detect_conflicts as _detect_conflicts,
)
from propstore.conflict_detector.collectors import (
    conflict_claim_from_payload,
    conflict_claims_from_claim_files,
)
from propstore.conflict_detector.models import ConflictClaim
from propstore.claims import loaded_claim_file_from_payload
from propstore.cel_checker import ConceptInfo, KindType
from propstore.families.contexts.stages import LoadedContext
from tests.conftest import make_cel_registry, make_concept_identity, make_concept_registry


# ── Test helpers ─────────────────────────────────────────────────────


def make_parameter_claim(id, concept_id, value, unit="Hz", conditions=None):
    """Build a minimal parameter claim dict for testing."""
    claim = {
        "id": id,
        "type": "parameter",
        "output_concept": concept_id,
        "unit": unit,
        "conditions": conditions or [],
        "context": {"id": "ctx_test"},
        "provenance": {"paper": "test", "page": 1},
    }
    if isinstance(value, list):
        if len(value) == 1:
            claim["value"] = value[0]
        elif len(value) == 2:
            claim["lower_bound"] = value[0]
            claim["upper_bound"] = value[1]
        else:
            raise ValueError(f"unsupported test value list shape: {value!r}")
    else:
        claim["value"] = value
    return claim


def make_claim_file(claims, filename="test_paper"):
    """Build runtime conflict claims from claim payloads."""
    records = []
    for claim in claims:
        record = conflict_claim_from_payload(claim, source_paper=filename)
        assert record is not None
        records.append(record)
    return records


def make_context(filename: str, data: dict) -> LoadedContext:
    return LoadedContext.from_payload(filename=filename, source_path=None, data=data)


def flatten_claims(claims_or_files):
    flattened = []
    for item in claims_or_files:
        if isinstance(item, ConflictClaim):
            flattened.append(item)
        else:
            flattened.extend(item)
    return flattened


def detect_conflicts(claim_files, registry, lifting_system=None):
    return _detect_conflicts(
        flatten_claims(claim_files),
        registry,
        make_cel_registry(registry),
        lifting_system=lifting_system,
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


class TestConflictRegistryProjection:
    def test_conflicting_alias_entries_raise(self):
        registry = make_concept_registry()
        base = next(
            dict(value)
            for value in registry.values()
            if value.get("canonical_name") == "fundamental_frequency"
        )
        conflicting = dict(base)
        conflicting["canonical_name"] = "different_name"
        registry["concept1_alias_conflict"] = conflicting

        with pytest.raises(ValueError, match="conflicting concept registry entries"):
            detect_conflicts([], registry)

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
        concept10 = make_concept_identity(
            "concept10",
            domain="speech",
            canonical_name="open_quotient",
        )
        concept11 = make_concept_identity(
            "concept11",
            domain="speech",
            canonical_name="return_time",
        )
        concept12 = make_concept_identity(
            "concept12",
            domain="speech",
            canonical_name="period",
        )
        return {
            concept10["artifact_id"]: {
                **concept10,
                "canonical_name": "open_quotient",
                "form": "duration_ratio",
                "status": "accepted",
                "definition": "ra = ta / T0",
                "parameterization_relationships": [
                    {
                        "inputs": [concept11["artifact_id"], concept12["artifact_id"]],
                        "sympy": "concept11 / concept12",
                        "exactness": "exact",
                    }
                ],
            },
            concept11["artifact_id"]: {
                **concept11,
                "canonical_name": "return_time",
                "form": "time",
                "status": "accepted",
                "definition": "ta",
            },
            concept12["artifact_id"]: {
                **concept12,
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
        concept10_id = make_concept_identity(
            "concept10",
            domain="speech",
            canonical_name="open_quotient",
        )["artifact_id"]
        concept11_id = make_concept_identity(
            "concept11",
            domain="speech",
            canonical_name="return_time",
        )["artifact_id"]
        concept12_id = make_concept_identity(
            "concept12",
            domain="speech",
            canonical_name="period",
        )["artifact_id"]
        claims = [
            # Direct claim: ra = 5%
            make_parameter_claim("claim1", concept10_id, 5.0, unit="%"),
            # Inputs: ta = 0.001, T0 = 0.01 => ra = 0.001/0.01 = 0.1 = 10%... wait
            # Let's use simpler numbers: ta=1, T0=10 => ra = 0.1, but claim says 5.0
            make_parameter_claim("claim2", concept11_id, 1.0, unit="s"),
            make_parameter_claim("claim3", concept12_id, 10.0, unit="s"),
        ]
        cf = make_claim_file(claims)
        records = detect_conflicts([cf], registry)
        # Should find PARAM_CONFLICT: derived ra = 1/10 = 0.1, but claimed ra = 5.0
        param_conflicts = [r for r in records if r.warning_class == ConflictClass.PARAM_CONFLICT]
        assert len(param_conflicts) >= 1
        assert param_conflicts[0].concept_id == concept10_id
        assert param_conflicts[0].derivation_chain is not None

    def test_param_no_conflict_approximate(self):
        """Approximate parameterization -> skip, no PARAM_CONFLICT."""
        pytest.importorskip("sympy")
        concept10 = make_concept_identity(
            "concept10",
            domain="speech",
            canonical_name="open_quotient",
        )
        concept11 = make_concept_identity(
            "concept11",
            domain="speech",
            canonical_name="return_time",
        )
        concept12 = make_concept_identity(
            "concept12",
            domain="speech",
            canonical_name="period",
        )
        registry = {
            concept10["artifact_id"]: {
                **concept10,
                "canonical_name": "open_quotient",
                "form": "duration_ratio",
                "status": "accepted",
                "definition": "ra ~ ta / T0",
                "parameterization_relationships": [
                    {
                        "inputs": [concept11["artifact_id"], concept12["artifact_id"]],
                        "sympy": "concept11 / concept12",
                        "exactness": "approximate",
                    }
                ],
            },
            concept11["artifact_id"]: {
                **concept11,
                "canonical_name": "return_time",
                "form": "time",
                "status": "accepted",
                "definition": "ta",
            },
            concept12["artifact_id"]: {
                **concept12,
                "canonical_name": "period",
                "form": "time",
                "status": "accepted",
                "definition": "T0",
            },
        }
        claims = [
            make_parameter_claim("claim1", concept10["artifact_id"], 5.0, unit="%"),
            make_parameter_claim("claim2", concept11["artifact_id"], 1.0, unit="s"),
            make_parameter_claim("claim3", concept12["artifact_id"], 10.0, unit="s"),
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
    @settings()
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
    @settings()
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
        assert r.conditions_a == ["source == 'test_paper'", "task == 'speech'"]
        assert r.conditions_b == ["source == 'test_paper'", "task == 'speech'"]
        assert r.derivation_chain is None

    def test_cross_file_conflicts(self):
        """Different source papers are source-conditioned and surface as PHI_NODE."""
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
        assert records[0].warning_class == ConflictClass.PHI_NODE

    def test_typed_claim_files_add_source_conditions_at_boundary(self):
        """Typed claim files convert to runtime conflict claims with source conditions."""
        file_a = loaded_claim_file_from_payload(
            filename="paper_a",
            source_path=None,
            data={
                "source": {"paper": "paper_a"},
                "claims": [make_parameter_claim("claim1", "concept1", 200.0)],
            },
        )
        file_b = loaded_claim_file_from_payload(
            filename="paper_b",
            source_path=None,
            data={
                "source": {"paper": "paper_b"},
                "claims": [make_parameter_claim("claim2", "concept1", 350.0)],
            },
        )

        claims = conflict_claims_from_claim_files([file_a, file_b])
        assert claims[0].conditions == ("source == 'paper_a'",)
        assert claims[1].conditions == ("source == 'paper_b'",)

        records = detect_conflicts([claims], make_concept_registry())
        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.PHI_NODE


# ── Named value field conflict detection ─────────────────────────────


def _make_named_claim(id, concept_id, unit="Hz", conditions=None, **fields):
    """Build a parameter claim with named value fields (value, lower_bound, upper_bound)."""
    c = {
        "id": id,
        "type": "parameter",
        "output_concept": concept_id,
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

    def test_unsupported_equation_surface_logs_diagnostic(self, caplog):
        claims = [
            _make_equation_claim(
                "claim1",
                "Ps = 1.00 + 0.88 * F0",
                [
                    {"symbol": "Ps", "concept": "concept2", "role": "dependent"},
                    {"symbol": "F0", "concept": "concept1", "role": "independent"},
                ],
                conditions=["task == 'speech'"],
            ),
            _make_equation_claim(
                "claim2",
                "Ps = And(F0, F0)",
                [
                    {"symbol": "Ps", "concept": "concept2", "role": "dependent"},
                    {"symbol": "F0", "concept": "concept1", "role": "independent"},
                ],
                conditions=["task == 'speech'"],
            ),
        ]
        cf = make_claim_file(claims)

        with caplog.at_level("WARNING"):
            records = detect_conflicts([cf], make_concept_registry())

        assert records == []
        assert any(
            "unsupported_surface" in record.message and "claim2" in record.message
            for record in caplog.records
        )


# ── Algorithm claim conflict detection ────────────────────────────────


def _make_algorithm_claim(id, body, variables, conditions=None, **fields):
    """Build an algorithm claim dict for testing."""
    concept = fields.pop("concept", None)
    claim = {
        "id": id,
        "type": "algorithm",
        "body": body,
        "variables": variables,
        "conditions": conditions or [],
        "provenance": {"paper": "test", "page": 1},
    }
    if concept is not None:
        fields["output_concept"] = concept
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

    def test_algorithm_sympy_tier_still_conflicts(self, monkeypatch):
        """SymPy-only equivalence is not enough to suppress a conflict."""
        from ast_equiv import Tier
        from propstore.conflict_detector import algorithms

        claims = [
            _make_algorithm_claim(
                "algo1",
                "def compute(x):\n    return x / 2 + x / 2",
                [{"name": "x", "concept": "concept1"}],
                concept="concept1",
            ),
            _make_algorithm_claim(
                "algo2",
                "def calc(val):\n    return val",
                [{"name": "val", "concept": "concept1"}],
                concept="concept1",
            ),
        ]
        cf = make_claim_file(claims)
        monkeypatch.setattr(
            algorithms,
            "ast_compare",
            lambda *_args, **_kwargs: SimpleNamespace(
                equivalent=True,
                tier=Tier.SYMPY,
                similarity=1.0,
            ),
        )

        records = detect_conflicts([cf], make_concept_registry())

        algo_records = [r for r in records if r.value_a.startswith("algorithm:")]
        assert len(algo_records) == 1
        assert algo_records[0].concept_id == "concept1"
        assert f"tier:{Tier.SYMPY}" in algo_records[0].derivation_chain

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
    @settings()
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
    def test_transitive_conflicts_in_unrelated_contexts_are_context_phi_nodes(self):
        """Unrelated contexts require an explicit lifting rule before conflict."""
        from propstore.conflict_detector import detect_transitive_conflicts
        from propstore.context_lifting import ContextReference, LiftingSystem

        concept_out = make_concept_identity(
            "concept_out",
            domain="speech",
            canonical_name="concept_out",
        )
        concept_mid = make_concept_identity(
            "concept_mid",
            domain="speech",
            canonical_name="concept_mid",
        )
        concept_in = make_concept_identity(
            "concept_in",
            domain="speech",
            canonical_name="concept_in",
        )
        registry = {
            concept_out["artifact_id"]: {
                **concept_out,
                "canonical_name": "concept_out",
                "form": "frequency",
                "status": "accepted",
                "definition": "output",
                "parameterization_relationships": [
                    {
                        "inputs": [concept_mid["artifact_id"]],
                        "sympy": "concept_mid * 2",
                        "exactness": "exact",
                    }
                ],
            },
            concept_mid["artifact_id"]: {
                **concept_mid,
                "canonical_name": "concept_mid",
                "form": "frequency",
                "status": "accepted",
                "definition": "middle",
                "parameterization_relationships": [
                    {
                        "inputs": [concept_in["artifact_id"]],
                        "sympy": "concept_in * 3",
                        "exactness": "exact",
                    }
                ],
            },
            concept_in["artifact_id"]: {
                **concept_in,
                "canonical_name": "concept_in",
                "form": "frequency",
                "status": "accepted",
                "definition": "input",
            },
        }
        claims = [
            make_parameter_claim(
                "direct_out",
                concept_out["artifact_id"],
                100.0,
                conditions=["task == 'speech'"],
            ) | {"context": "ctx_root"},
            make_parameter_claim(
                "source_in",
                concept_in["artifact_id"],
                10.0,
                conditions=["task == 'speech'"],
            ) | {"context": "ctx_other"},
        ]
        cf = make_claim_file(claims)
        lifting_system = LiftingSystem(
            contexts=(ContextReference("ctx_root"), ContextReference("ctx_other")),
        )

        records = detect_transitive_conflicts(
            cf,
            registry,
            lifting_system=lifting_system,
        )

        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONTEXT_PHI_NODE
        assert records[0].concept_id == concept_out["artifact_id"]

    def test_unrelated_contexts_classify_direct_conflicts_as_context_phi(self):
        """Claims in unrelated contexts need authored lifting to interact."""
        from propstore.context_lifting import ContextReference, LiftingSystem

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
        lifting_system = LiftingSystem(
            contexts=(ContextReference("ctx_alpha"), ContextReference("ctx_beta")),
        )

        records = detect_conflicts(
            [cf],
            make_concept_registry(),
            lifting_system=lifting_system,
        )

        assert len(records) == 1
        assert records[0].warning_class == ConflictClass.CONTEXT_PHI_NODE

    def test_lifting_rules_project_claims_into_shared_target_context(self):
        """A lift-selected shared target context can convert cross-paper PHI nodes into conflicts."""
        from propstore.context_lifting import (
            ContextReference,
            LiftingRule,
            LiftingSystem,
        )

        cf_a = make_claim_file(
            [
                make_parameter_claim(
                    "claim_a",
                    "concept1",
                    200.0,
                    conditions=["task == 'speech'"],
                ) | {"context": "ctx_alpha"},
            ],
            filename="paper_a",
        )
        cf_b = make_claim_file(
            [
                make_parameter_claim(
                    "claim_b",
                    "concept1",
                    350.0,
                    conditions=["task == 'singing'"],
                ) | {"context": "ctx_beta"},
            ],
            filename="paper_b",
        )
        lifting_system = LiftingSystem(
            contexts=(
                ContextReference("ctx_alpha"),
                ContextReference("ctx_beta"),
                ContextReference("ctx_shared"),
            ),
            lifting_rules=(
                LiftingRule(
                    id="lift_alpha",
                    source=ContextReference("ctx_alpha"),
                    target=ContextReference("ctx_shared"),
                    conditions=("task == 'speech'",),
                ),
                LiftingRule(
                    id="lift_beta",
                    source=ContextReference("ctx_beta"),
                    target=ContextReference("ctx_shared"),
                    conditions=("task == 'singing'",),
                ),
            ),
            context_assumptions={
                "ctx_shared": ("task == 'whisper'",),
            },
        )

        records = detect_conflicts(
            [cf_a, cf_b],
            make_concept_registry(),
            lifting_system=lifting_system,
        )

        assert any(record.warning_class == ConflictClass.PHI_NODE for record in records)
        lifted_conflicts = [
            record
            for record in records
            if record.warning_class == ConflictClass.CONFLICT
        ]
        assert len(lifted_conflicts) == 1
        assert lifted_conflicts[0].claim_a_id == "claim_a"
        assert lifted_conflicts[0].claim_b_id == "claim_b"
        assert lifted_conflicts[0].conditions_a == ["task == 'whisper'"]
        assert lifted_conflicts[0].conditions_b == ["task == 'whisper'"]

    def test_lifting_rules_require_claims_to_satisfy_selector_conditions(self):
        """Lift selectors should not apply when the claim only remains compatible by omission."""
        from propstore.context_lifting import (
            ContextReference,
            LiftingRule,
            LiftingSystem,
        )

        cf_a = make_claim_file(
            [
                make_parameter_claim(
                    "claim_a",
                    "concept1",
                    200.0,
                    conditions=["task == 'speech'"],
                ) | {"context": "ctx_alpha"},
            ],
            filename="paper_a",
        )
        cf_b = make_claim_file(
            [
                make_parameter_claim(
                    "claim_b",
                    "concept1",
                    350.0,
                    conditions=["task == 'singing'"],
                ) | {"context": "ctx_beta"},
            ],
            filename="paper_b",
        )
        lifting_system = LiftingSystem(
            contexts=(
                ContextReference("ctx_alpha"),
                ContextReference("ctx_beta"),
                ContextReference("ctx_shared"),
            ),
            lifting_rules=(
                LiftingRule(
                    id="lift_alpha",
                    source=ContextReference("ctx_alpha"),
                    target=ContextReference("ctx_shared"),
                    conditions=(
                        "task == 'speech'",
                        "fundamental_frequency > 100",
                    ),
                ),
                LiftingRule(
                    id="lift_beta",
                    source=ContextReference("ctx_beta"),
                    target=ContextReference("ctx_shared"),
                    conditions=("task == 'singing'",),
                ),
            ),
            context_assumptions={
                "ctx_shared": ("task == 'whisper'",),
            },
        )

        records = detect_conflicts(
            [cf_a, cf_b],
            make_concept_registry(),
            lifting_system=lifting_system,
        )

        assert all(record.warning_class != ConflictClass.CONFLICT for record in records)
        assert any(record.warning_class == ConflictClass.PHI_NODE for record in records)


# ── Exception-handling tests (Group 2) ──────────────────────────────


class TestAlgorithmExceptionHandling:
    @pytest.mark.parametrize(
        "exc",
        [
            pytest.param("algorithm_parse", id="algorithm-parse"),
            pytest.param("recursion", id="recursion"),
        ],
    )
    def test_ast_equiv_recoverable_errors_skipped(self, exc):
        """Recoverable ast-equiv failures should skip the pair, not crash."""
        from unittest.mock import patch
        from ast_equiv import AlgorithmParseError
        from propstore.conflict_detector.algorithms import detect_algorithm_conflicts

        cf = make_claim_file([
            {
                "id": "alg1",
                "type": "algorithm",
                "output_concept": "concept_algo",
                "body": "x + 1",
                "variables": [{"name": "x", "concept": "input"}],
            },
            {
                "id": "alg2",
                "type": "algorithm",
                "output_concept": "concept_algo",
                "body": "x + 2",
                "variables": [{"name": "x", "concept": "input"}],
            },
        ])
        registry = {"concept_algo": ConceptInfo(
            id="concept_algo", canonical_name="concept_algo", kind=KindType.QUANTITY,
        )}
        side_effect = (
            AlgorithmParseError("bad algorithm")
            if exc == "algorithm_parse"
            else RecursionError("deep ast")
        )

        with patch(
            "propstore.conflict_detector.algorithms.ast_compare",
            side_effect=side_effect,
        ):
            records = detect_algorithm_conflicts(cf, registry)

        assert records == []

    def test_value_error_skipped(self):
        """ValueError from ast_compare should skip the pair, not crash."""
        from unittest.mock import patch
        from propstore.conflict_detector.algorithms import detect_algorithm_conflicts

        cf = make_claim_file([
            {
                "id": "alg1",
                "type": "algorithm",
                "output_concept": "concept_algo",
                "body": "x + 1",
                "variables": [{"name": "x", "concept": "input"}],
            },
            {
                "id": "alg2",
                "type": "algorithm",
                "output_concept": "concept_algo",
                "body": "x + 2",
                "variables": [{"name": "x", "concept": "input"}],
            },
        ])
        registry = {"concept_algo": ConceptInfo(
            id="concept_algo", canonical_name="concept_algo", kind=KindType.QUANTITY,
        )}

        with patch(
            "propstore.conflict_detector.algorithms.ast_compare",
            side_effect=ValueError("bad parse"),
        ):
            records = detect_algorithm_conflicts(cf, registry)

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
                "output_concept": "concept_algo",
                "body": "x + 1",
                "variables": [{"name": "x", "concept": "input"}],
            },
            {
                "id": "alg2",
                "type": "algorithm",
                "output_concept": "concept_algo",
                "body": "x + 2",
                "variables": [{"name": "x", "concept": "input"}],
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
                detect_algorithm_conflicts(cf, registry)


class TestParameterZ3FailureHandling:
    def test_z3_partition_error_raises(self):
        """Z3 partition failure should raise; there is no pairwise fallback."""
        from unittest.mock import patch
        from propstore.z3_conditions import Z3TranslationError, Z3ConditionSolver
        from propstore.conflict_detector.parameter_claims import detect_parameter_conflicts

        cel_registry = {"freq": ConceptInfo(
            id="freq", canonical_name="freq", kind=KindType.QUANTITY,
        )}
        solver = Z3ConditionSolver(cel_registry)

        # 3 claims triggers the Z3 partition path
        cf = make_claim_file([
            {"id": "p1", "type": "parameter", "output_concept": "freq", "body": "100", "conditions": ["freq > 50"]},
            {"id": "p2", "type": "parameter", "output_concept": "freq", "body": "200", "conditions": ["freq > 50"]},
            {"id": "p3", "type": "parameter", "output_concept": "freq", "body": "300", "conditions": ["freq > 50"]},
        ])

        with patch.object(
            solver,
            "partition_equivalence_classes",
            side_effect=Z3TranslationError("partition failed"),
        ):
            with pytest.raises(RuntimeError, match="Z3 partitioning failed during parameter conflict detection"):
                detect_parameter_conflicts(cf, cel_registry, solver=solver)

    def test_z3_partition_unexpected_error_propagates(self):
        """RuntimeError in partition should propagate."""
        from unittest.mock import patch
        from propstore.z3_conditions import Z3ConditionSolver
        from propstore.conflict_detector.parameter_claims import detect_parameter_conflicts

        cel_registry = {"freq": ConceptInfo(
            id="freq", canonical_name="freq", kind=KindType.QUANTITY,
        )}
        solver = Z3ConditionSolver(cel_registry)

        cf = make_claim_file([
            {"id": "p1", "type": "parameter", "output_concept": "freq", "body": "100", "conditions": ["freq > 50"]},
            {"id": "p2", "type": "parameter", "output_concept": "freq", "body": "200", "conditions": ["freq > 50"]},
            {"id": "p3", "type": "parameter", "output_concept": "freq", "body": "300", "conditions": ["freq > 50"]},
        ])

        with patch.object(
            solver,
            "partition_equivalence_classes",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError, match="unexpected"):
                detect_parameter_conflicts(cf, cel_registry, solver=solver)

    def test_z3_disjoint_unexpected_error_propagates(self):
        """RuntimeError in are_disjoint should propagate, not be swallowed."""
        from unittest.mock import patch
        from propstore.z3_conditions import Z3ConditionSolver
        from propstore.conflict_detector.parameter_claims import detect_parameter_conflicts

        cel_registry = {"freq": ConceptInfo(
            id="freq", canonical_name="freq", kind=KindType.QUANTITY,
        )}
        solver = Z3ConditionSolver(cel_registry)

        cf = make_claim_file([
            {"id": "p1", "type": "parameter", "output_concept": "freq", "body": "100", "conditions": ["freq > 50"]},
            {"id": "p2", "type": "parameter", "output_concept": "freq", "body": "200", "conditions": ["freq > 50"]},
            {"id": "p3", "type": "parameter", "output_concept": "freq", "body": "300", "conditions": ["freq < 10"]},
        ])

        with patch.object(
            solver,
            "partition_equivalence_classes",
            return_value=[[0, 1], [2]],
        ), patch.object(
            solver,
            "are_disjoint_result",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(RuntimeError, match="unexpected"):
                detect_parameter_conflicts(cf, cel_registry, solver=solver)
