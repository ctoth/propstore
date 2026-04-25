"""Regression tests for parameterization conflict detection."""

import warnings
from unittest.mock import patch

import pytest

from propstore.conflict_detector.collectors import conflict_claim_from_payload
from propstore.conflict_detector.models import ConflictClass, ConflictClaim
from propstore.families.contexts.stages import LoadedContext
from propstore.dimensions import UnitConversion
from propstore.form_utils import FormDefinition
from propstore.conflict_detector import (
    detect_conflicts as _detect_conflicts,
    detect_transitive_conflicts,
)
from propstore.conflict_detector.parameterization_conflicts import (
    _detect_parameterization_conflicts,
)
from tests.conftest import make_cel_registry, make_concept_identity

from propstore.cel_checker import KindType


def _frequency_form() -> FormDefinition:
    """Build a frequency FormDefinition with kHz conversion (multiplier=1000)."""
    return FormDefinition(
        name="frequency",
        kind=KindType.QUANTITY,
        unit_symbol="Hz",
        allowed_units={"Hz", "kHz"},
        conversions={
            "kHz": UnitConversion(
                unit="kHz",
                type="multiplicative",
                multiplier=1000.0,
            ),
        },
    )


def _stub_claim_file() -> list[ConflictClaim]:
    return []


def _concept(local_id: str, *, form: str) -> tuple[str, dict]:
    data = {
        **make_concept_identity(local_id, domain="test", canonical_name=local_id),
        "canonical_name": local_id,
        "status": "active",
        "definition": local_id,
        "form": form,
    }
    return data["artifact_id"], data


def _claim(payload: dict) -> ConflictClaim:
    claim = ConflictClaim.from_payload(payload)
    assert claim is not None
    return claim


def _claim_file(payloads: list[dict], filename: str = "test") -> list[ConflictClaim]:
    claims = []
    for payload in payloads:
        normalized = dict(payload)
        if "type" not in normalized and "concept" in normalized:
            normalized["type"] = "parameter"
        if "output_concept" not in normalized and "concept" in normalized:
            normalized["output_concept"] = normalized.pop("concept")
        claim = conflict_claim_from_payload(normalized, source_paper=filename)
        assert claim is not None
        claims.append(claim)
    return claims


def _context(filename: str, data: dict) -> LoadedContext:
    return LoadedContext.from_payload(filename=filename, source_path=None, data=data)


def _flatten_claims(claims_or_files):
    flattened = []
    for item in claims_or_files:
        if isinstance(item, ConflictClaim):
            flattened.append(item)
        else:
            flattened.extend(item)
    return flattened


def detect_conflicts(claim_files, registry, lifting_system=None):
    return _detect_conflicts(
        _flatten_claims(claim_files),
        registry,
        make_cel_registry(registry),
        lifting_system=lifting_system,
    )


def test_detect_param_conflicts_handles_equality_parameterizations_without_warning():
    """Eq(...) parameterizations should produce conflicts, not warnings."""
    records = []
    concept1_id, concept1 = _concept("concept1", form="quantity")
    concept2_id, concept2 = _concept("concept2", form="quantity")
    concept3_id, concept3 = _concept("concept3", form="quantity")
    by_concept = {
        concept1_id: [_claim({"id": "claim_a", "value": 10.0, "conditions": []})],
        concept2_id: [_claim({"id": "claim_b", "value": 9.807, "conditions": []})],
        concept3_id: [_claim({"id": "claim_c", "value": 99.0, "conditions": []})],
    }
    concept_registry = {
        concept1_id: concept1,
        concept2_id: concept2,
        concept3_id: {
            **concept3,
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": [concept1_id, concept2_id],
                    "sympy": "Eq(concept3, concept1 * concept2)",
                }
            ],
        },
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _detect_parameterization_conflicts(records, by_concept, concept_registry, [])

    param_warnings = [
        warning for warning in caught
        if f"Could not evaluate parameterization for {concept3_id}" in str(warning.message)
    ]
    assert param_warnings == []
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert records[0].concept_id == concept3_id
    assert records[0].claim_b_id == "claim_a"


def test_same_value_different_units_no_conflict():
    """Two claims for the same concept: 200 Hz and 0.2 kHz are identical. No conflict."""
    records = []
    freq_form = _frequency_form()
    forms = {"frequency": freq_form}
    freq_input_id, freq_input = _concept("freq_input", form="frequency")
    freq_output_id, freq_output = _concept("freq_output", form="quantity")

    by_concept = {
        freq_input_id: [
            _claim({"id": "claim_hz", "value": 200.0, "unit": "Hz", "conditions": []}),
            _claim({"id": "claim_khz", "value": 0.2, "unit": "kHz", "conditions": []}),
        ],
        freq_output_id: [_claim({"id": "claim_out", "value": 100.0, "conditions": []})],
    }
    concept_registry = {
        freq_input_id: freq_input,
        freq_output_id: {
            **freq_output,
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": [freq_input_id],
                    "sympy": "Eq(freq_output, freq_input / 2)",
                }
            ],
        },
    }

    _detect_parameterization_conflicts(
        records, by_concept, concept_registry, _stub_claim_file(), forms=forms
    )

    # Both claims for freq_input are 200 Hz after normalization.
    # Derived = 100 which matches claim_out.  No conflict expected.
    assert len(records) == 0


def test_different_value_different_units_conflict():
    """0.5 kHz input (=500 Hz) derives 250, but direct claim says 100. Conflict expected."""
    records = []
    freq_form = _frequency_form()
    forms = {"frequency": freq_form}
    freq_input_id, freq_input = _concept("freq_input", form="frequency")
    freq_output_id, freq_output = _concept("freq_output", form="quantity")

    by_concept = {
        freq_input_id: [
            _claim({"id": "claim_khz", "value": 0.5, "unit": "kHz", "conditions": []}),
        ],
        freq_output_id: [_claim({"id": "claim_out", "value": 100.0, "conditions": []})],
    }
    concept_registry = {
        freq_input_id: freq_input,
        freq_output_id: {
            **freq_output,
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": [freq_input_id],
                    "sympy": "Eq(freq_output, freq_input / 2)",
                }
            ],
        },
    }

    _detect_parameterization_conflicts(
        records, by_concept, concept_registry, _stub_claim_file(), forms=forms
    )

    # 0.5 kHz → 500 Hz (normalized) → derived = 500/2 = 250, but claim_out = 100
    # Without normalization: 0.5/2 = 0.25, also ≠ 100 (conflict either way, but
    # the derived value_b in the record should be 250.0, proving SI normalization)
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert records[0].value_b == "250.0"


def test_transitive_propagation_normalizes_units():
    """A parameterization chain where an input uses non-SI unit. Derived value should use SI."""
    freq_form = _frequency_form()
    forms = {"frequency": freq_form}
    concept_a_id, concept_a = _concept("concept_a", form="frequency")
    concept_b_id, concept_b = _concept("concept_b", form="quantity")
    concept_c_id, concept_c = _concept("concept_c", form="quantity")

    # Chain: concept_a (input) -> concept_b (derived) -> concept_c (derived)
    # concept_a has a claim in kHz, concept_c has a direct claim to compare against
    concept_registry = {
        concept_a_id: concept_a,
        concept_b_id: {
            **concept_b,
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": [concept_a_id],
                    "sympy": "Eq(concept_b, concept_a * 2)",
                }
            ],
        },
        concept_c_id: {
            **concept_c,
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": [concept_b_id],
                    "sympy": "Eq(concept_c, concept_b + 100)",
                }
            ],
        },
    }

    # concept_a = 0.1 kHz = 100 Hz
    # concept_b derived = 100 * 2 = 200
    # concept_c derived = 200 + 100 = 300
    # Direct claim for concept_c = 300 → should match (no conflict)
    claim_file = _claim_file(
        [
            {"id": "claim_a", "concept": concept_a_id, "value": 0.1, "unit": "kHz"},
            {"id": "claim_b_direct", "concept": concept_b_id, "value": 200.0},
            {"id": "claim_c_direct", "concept": concept_c_id, "value": 300.0},
        ]
    )

    conflicts = detect_transitive_conflicts(
        claim_file, concept_registry, forms=forms
    )

    # With correct SI normalization (0.1 kHz → 100 Hz), chain gives 300,
    # matching the direct claim. No conflict.
    # Without normalization, 0.1 * 2 = 0.2, 0.2 + 100 = 100.2 ≠ 300 → spurious conflict.
    param_conflicts = [c for c in conflicts if c.warning_class == ConflictClass.PARAM_CONFLICT]
    assert len(param_conflicts) == 0


def test_single_hop_conflict_carries_derived_conditions():
    records = []
    concept_in_id, concept_in = _concept("concept_in", form="frequency")
    concept_out_id, concept_out = _concept("concept_out", form="frequency")
    by_concept = {
        concept_in_id: [
            _claim({
                "id": "claim_in",
                "value": 10.0,
                "conditions": ["task == 'speech'"],
                "context": "ctx_input",
            }),
        ],
        concept_out_id: [
            _claim({
                "id": "claim_out",
                "value": 100.0,
                "conditions": ["task == 'speech'", "mode == 'normal'"],
                "context": "ctx_input",
            }),
        ],
    }
    concept_registry = {
        concept_in_id: concept_in,
        concept_out_id: {
            **concept_out,
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": [concept_in_id],
                    "sympy": "Eq(concept_out, concept_in * 2)",
                    "conditions": ["mode == 'normal'"],
                }
            ],
        },
    }

    _detect_parameterization_conflicts(
        records,
        by_concept,
        concept_registry,
        _stub_claim_file(),
    )

    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert records[0].conditions_b == ["mode == 'normal'", "task == 'speech'"]


def test_single_hop_conflict_requires_lifted_contexts():
    from propstore.context_lifting import ContextReference, LiftingSystem

    concept_in_id, concept_in = _concept("concept_in", form="frequency")
    concept_out_id, concept_out = _concept("concept_out", form="frequency")
    claim_file = _claim_file(
        [
            {
                "id": "claim_in",
                "type": "parameter",
                "concept": concept_in_id,
                "value": 10.0,
                "conditions": ["task == 'speech'"],
                "context": "ctx_input",
            },
            {
                "id": "claim_out",
                "type": "parameter",
                "concept": concept_out_id,
                "value": 100.0,
                "conditions": ["task == 'speech'"],
                "context": "ctx_direct",
            },
        ],
    )
    concept_registry = {
        concept_in_id: concept_in,
        concept_out_id: {
            **concept_out,
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": [concept_in_id],
                    "sympy": "Eq(concept_out, concept_in * 2)",
                }
            ],
        },
    }
    lifting_system = LiftingSystem(
        contexts=(ContextReference("ctx_input"), ContextReference("ctx_direct")),
    )

    records = detect_conflicts(
        [claim_file],
        concept_registry,
        lifting_system=lifting_system,
    )

    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.CONTEXT_PHI_NODE


def test_transitive_conflict_detection_is_order_independent():
    concept_in_id, concept_in = _concept("concept_in", form="frequency")
    concept_mid_id, concept_mid = _concept("concept_mid", form="frequency")
    concept_out_id, concept_out = _concept("concept_out", form="frequency")
    concept_registry = {
        concept_in_id: concept_in,
        concept_mid_id: {
            **concept_mid,
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": [concept_in_id],
                    "sympy": "Eq(concept_mid, concept_in * 2)",
                }
            ],
        },
        concept_out_id: {
            **concept_out,
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": [concept_mid_id],
                    "sympy": "Eq(concept_out, concept_mid + 5)",
                }
            ],
        },
    }
    first_order = _claim_file(
        [
            {"id": "in_a", "type": "parameter", "concept": concept_in_id, "value": 10.0},
            {"id": "in_b", "type": "parameter", "concept": concept_in_id, "value": 20.0},
            {"id": "out_direct", "type": "parameter", "concept": concept_out_id, "value": 25.0},
        ],
        filename="first",
    )
    second_order = _claim_file(
        [
            {"id": "in_b", "type": "parameter", "concept": concept_in_id, "value": 20.0},
            {"id": "in_a", "type": "parameter", "concept": concept_in_id, "value": 10.0},
            {"id": "out_direct", "type": "parameter", "concept": concept_out_id, "value": 25.0},
        ],
        filename="second",
    )

    first_records = detect_transitive_conflicts(first_order, concept_registry)
    second_records = detect_transitive_conflicts(second_order, concept_registry)

    assert len(first_records) == 1
    assert len(second_records) == 1
    assert first_records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert second_records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert first_records[0].value_b == second_records[0].value_b == "45.0"


def test_runtime_error_from_sympy_parameterization_propagates():
    records = []
    concept_a_id, concept_a = _concept("a", form="quantity")
    concept_b_id, concept_b = _concept("b", form="quantity")
    derived_id, derived = _concept("derived", form="quantity")
    by_concept = {
        concept_a_id: [_claim({"id": "claim_a", "value": 2.0, "conditions": []})],
        concept_b_id: [_claim({"id": "claim_b", "value": 3.0, "conditions": []})],
        derived_id: [_claim({"id": "claim_derived", "value": 10.0, "conditions": []})],
    }
    concept_registry = {
        concept_a_id: concept_a,
        concept_b_id: concept_b,
        derived_id: {
            **derived,
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": [concept_a_id, concept_b_id],
                    "sympy": "Eq(derived, a * b)",
                }
            ],
        },
    }

    from propstore.propagation import parse_cached

    parse_cached.cache_clear()
    try:
        with patch(
            "sympy.parsing.sympy_parser.parse_expr",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                _detect_parameterization_conflicts(
                    records,
                    by_concept,
                    concept_registry,
                    [],
                )
    finally:
        parse_cached.cache_clear()
