"""Regression tests for parameterization conflict detection."""

from pathlib import Path

import warnings

from propstore.conflict_detector.models import ConflictClass
from propstore.form_utils import FormDefinition, UnitConversion
from propstore.param_conflicts import _detect_param_conflicts, detect_transitive_conflicts
from propstore.loaded import LoadedEntry

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


def _stub_claim_file() -> LoadedEntry:
    return LoadedEntry(
        filename="test",
        filepath=Path("test.yaml"),
        data={"source": {"paper": "test"}, "claims": []},
    )


def test_detect_param_conflicts_handles_equality_parameterizations_without_warning():
    """Eq(...) parameterizations should produce conflicts, not warnings."""
    records = []
    by_concept = {
        "concept1": [{"id": "claim_a", "value": [10.0], "conditions": []}],
        "concept2": [{"id": "claim_b", "value": [9.807], "conditions": []}],
        "concept3": [{"id": "claim_c", "value": [99.0], "conditions": []}],
    }
    concept_registry = {
        "concept1": {"id": "concept1", "form": "quantity"},
        "concept2": {"id": "concept2", "form": "quantity"},
        "concept3": {
            "id": "concept3",
            "form": "quantity",
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": ["concept1", "concept2"],
                    "sympy": "Eq(concept3, concept1 * concept2)",
                }
            ],
        },
    }
    claim_file = LoadedEntry(
        filename="test",
        filepath=Path("test.yaml"),
        data={"source": {"paper": "test"}, "claims": []},
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _detect_param_conflicts(records, by_concept, concept_registry, [claim_file])

    param_warnings = [
        warning for warning in caught
        if "Could not evaluate parameterization for concept3" in str(warning.message)
    ]
    assert param_warnings == []
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert records[0].concept_id == "concept3"
    assert records[0].claim_b_id == "claim_a"


def test_same_value_different_units_no_conflict():
    """Two claims for the same concept: 200 Hz and 0.2 kHz are identical. No conflict."""
    records = []
    freq_form = _frequency_form()
    forms = {"frequency": freq_form}

    by_concept = {
        "freq_input": [
            {"id": "claim_hz", "value": 200.0, "unit": "Hz", "conditions": []},
            {"id": "claim_khz", "value": 0.2, "unit": "kHz", "conditions": []},
        ],
        "freq_output": [{"id": "claim_out", "value": [100.0], "conditions": []}],
    }
    concept_registry = {
        "freq_input": {"id": "freq_input", "form": "frequency"},
        "freq_output": {
            "id": "freq_output",
            "form": "quantity",
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": ["freq_input"],
                    "sympy": "Eq(freq_output, freq_input / 2)",
                }
            ],
        },
    }

    _detect_param_conflicts(
        records, by_concept, concept_registry, [_stub_claim_file()], forms=forms
    )

    # Both claims for freq_input are 200 Hz after normalization.
    # Derived = 100 which matches claim_out.  No conflict expected.
    assert len(records) == 0


def test_different_value_different_units_conflict():
    """0.5 kHz input (=500 Hz) derives 250, but direct claim says 100. Conflict expected."""
    records = []
    freq_form = _frequency_form()
    forms = {"frequency": freq_form}

    by_concept = {
        "freq_input": [
            {"id": "claim_khz", "value": 0.5, "unit": "kHz", "conditions": []},
        ],
        "freq_output": [{"id": "claim_out", "value": [100.0], "conditions": []}],
    }
    concept_registry = {
        "freq_input": {"id": "freq_input", "form": "frequency"},
        "freq_output": {
            "id": "freq_output",
            "form": "quantity",
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": ["freq_input"],
                    "sympy": "Eq(freq_output, freq_input / 2)",
                }
            ],
        },
    }

    _detect_param_conflicts(
        records, by_concept, concept_registry, [_stub_claim_file()], forms=forms
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

    # Chain: concept_a (input) -> concept_b (derived) -> concept_c (derived)
    # concept_a has a claim in kHz, concept_c has a direct claim to compare against
    concept_registry = {
        "concept_a": {"id": "concept_a", "form": "frequency"},
        "concept_b": {
            "id": "concept_b",
            "form": "quantity",
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": ["concept_a"],
                    "sympy": "Eq(concept_b, concept_a * 2)",
                }
            ],
        },
        "concept_c": {
            "id": "concept_c",
            "form": "quantity",
            "parameterization_relationships": [
                {
                    "exactness": "exact",
                    "inputs": ["concept_b"],
                    "sympy": "Eq(concept_c, concept_b + 100)",
                }
            ],
        },
    }

    # concept_a = 0.1 kHz = 100 Hz
    # concept_b derived = 100 * 2 = 200
    # concept_c derived = 200 + 100 = 300
    # Direct claim for concept_c = 300 → should match (no conflict)
    claim_data = {
        "source": {"paper": "test"},
        "claims": [
            {"id": "claim_a", "concept": "concept_a", "value": 0.1, "unit": "kHz"},
            {"id": "claim_b_direct", "concept": "concept_b", "value": 200.0},
            {"id": "claim_c_direct", "concept": "concept_c", "value": 300.0},
        ],
    }
    claim_file = LoadedEntry(
        filename="test",
        filepath=Path("test.yaml"),
        data=claim_data,
    )

    conflicts = detect_transitive_conflicts(
        [claim_file], concept_registry, forms=forms
    )

    # With correct SI normalization (0.1 kHz → 100 Hz), chain gives 300,
    # matching the direct claim. No conflict.
    # Without normalization, 0.1 * 2 = 0.2, 0.2 + 100 = 100.2 ≠ 300 → spurious conflict.
    param_conflicts = [c for c in conflicts if c.warning_class == ConflictClass.PARAM_CONFLICT]
    assert len(param_conflicts) == 0
