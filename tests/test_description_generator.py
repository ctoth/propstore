"""Tests for auto-generated claim descriptions.

Verifies that human-readable descriptions are generated for claims
that lack explicit statement fields.
"""

import pytest

from propstore.description_generator import generate_description, _format_conditions_prose


# ── Concept registry fixture ─────────────────────────────────────────

@pytest.fixture
def concept_registry():
    return {
        "concept2": {
            "id": "concept2",
            "canonical_name": "open_quotient",
            "form": "duration_ratio",
        },
        "concept1": {
            "id": "concept1",
            "canonical_name": "fundamental_frequency",
            "form": "frequency",
        },
        "concept10": {
            "id": "concept10",
            "canonical_name": "harmonic_richness",
            "form": "level",
        },
    }


# ── Test 1: Parameter claim with value ────────────────────────────────

def test_parameter_claim_with_value(concept_registry):
    claim = {
        "type": "parameter",
        "output_concept": "concept2",
        "value": 0.7,
        "unit": "ratio",
        "conditions": ["voice_quality_type == 'modal'"],
    }
    result = generate_description(claim, concept_registry)
    assert result == "open_quotient = 0.7 ratio (modal voice_quality_type)"


# ── Test 2: Parameter claim with range ────────────────────────────────

def test_parameter_claim_with_range(concept_registry):
    claim = {
        "type": "parameter",
        "output_concept": "concept2",
        "lower_bound": 0.5,
        "upper_bound": 0.9,
        "unit": "ratio",
    }
    result = generate_description(claim, concept_registry)
    assert result == "open_quotient \u2208 [0.5, 0.9] ratio"


# ── Test 3: Parameter claim with uncertainty ──────────────────────────

def test_parameter_claim_with_uncertainty(concept_registry):
    claim = {
        "type": "parameter",
        "output_concept": "concept2",
        "value": 0.7,
        "uncertainty": 0.12,
        "uncertainty_type": "sd",
        "unit": "ratio",
    }
    result = generate_description(claim, concept_registry)
    assert result == "open_quotient = 0.7 \u00b1 0.12 (sd) ratio"


# ── Test 4: Equation claim ────────────────────────────────────────────

def test_equation_claim(concept_registry):
    claim = {
        "type": "equation",
        "expression": "OQ = 1 - CQ",
    }
    result = generate_description(claim, concept_registry)
    assert result == "OQ = 1 - CQ"


# ── Test 5: Observation claim with explicit statement ─────────────────

def test_observation_preserves_statement(concept_registry):
    claim = {
        "type": "observation",
        "statement": "Modal voice has the highest harmonic richness",
    }
    result = generate_description(claim, concept_registry)
    assert result == "Modal voice has the highest harmonic richness"


# ── Test 6: Claim with no conditions ──────────────────────────────────

def test_parameter_no_conditions(concept_registry):
    claim = {
        "type": "parameter",
        "output_concept": "concept2",
        "value": 0.7,
        "unit": "ratio",
    }
    result = generate_description(claim, concept_registry)
    assert result == "open_quotient = 0.7 ratio"


# ── Test 7: Claim with multiple conditions ────────────────────────────

def test_parameter_multiple_conditions(concept_registry):
    claim = {
        "type": "parameter",
        "output_concept": "concept2",
        "value": 0.7,
        "unit": "ratio",
        "conditions": [
            "voice_quality_type == 'modal'",
            "speaker_sex == 'male'",
        ],
    }
    result = generate_description(claim, concept_registry)
    assert result == "open_quotient = 0.7 ratio (modal voice_quality_type, male speaker_sex)"


# ── Test: Model claim ─────────────────────────────────────────────────

def test_model_claim(concept_registry):
    claim = {
        "type": "model",
        "name": "LF glottal flow model",
    }
    result = generate_description(claim, concept_registry)
    assert result == "Model: LF glottal flow model"


# ── Test: Measurement claim ───────────────────────────────────────────

def test_measurement_claim(concept_registry):
    claim = {
        "type": "measurement",
        "target_concept": "concept2",
        "measure": "jnd_absolute",
        "value": 0.05,
        "unit": "ratio",
    }
    result = generate_description(claim, concept_registry)
    assert result == "jnd_absolute of open_quotient = 0.05 ratio"


# ── Test: Algorithm claim with stage ─────────────────────────────────

def test_algorithm_claim_with_stage(concept_registry):
    claim = {
        "type": "algorithm",
        "name": "Viterbi decoding",
        "stage": "inference",
    }
    result = generate_description(claim, concept_registry)
    assert result == "Algorithm: Viterbi decoding [inference]"


# ── Test: Algorithm claim without stage ──────────────────────────────

def test_algorithm_claim_without_stage(concept_registry):
    claim = {
        "type": "algorithm",
        "name": "Viterbi decoding",
    }
    result = generate_description(claim, concept_registry)
    assert result == "Algorithm: Viterbi decoding"


# ── Test: Unknown type returns None ───────────────────────────────────

def test_unknown_type_returns_none(concept_registry):
    claim = {"type": "something_else"}
    result = generate_description(claim, concept_registry)
    assert result is None


# ── Test: Concept not in registry falls back to concept ID ────────────

def test_missing_concept_falls_back_to_id(concept_registry):
    claim = {
        "type": "parameter",
        "output_concept": "concept9999",
        "value": 42.0,
        "unit": "Hz",
    }
    result = generate_description(claim, concept_registry)
    assert result == "concept9999 = 42 Hz"


# ── Test: Parameter with value + range prefers value ──────────────────

def test_parameter_value_and_range(concept_registry):
    claim = {
        "type": "parameter",
        "output_concept": "concept2",
        "value": 0.7,
        "lower_bound": 0.5,
        "upper_bound": 0.9,
        "unit": "ratio",
    }
    result = generate_description(claim, concept_registry)
    # When both value and range exist, show value with range context
    assert result == "open_quotient = 0.7 ratio"


# ── Test: Condition summarizer ────────────────────────────────────────

def test_summarize_voice_quality():
    assert _format_conditions_prose(["voice_quality_type == 'modal'"]) == "modal voice_quality_type"


def test_summarize_speaker_sex():
    assert _format_conditions_prose(["speaker_sex == 'male'"]) == "male speaker_sex"


def test_summarize_complex_condition():
    # Complex conditions pass through as-is
    result = _format_conditions_prose(["F0 > 200 && F0 < 400"])
    assert result == "F0 > 200 && F0 < 400"


def test_summarize_multiple():
    result = _format_conditions_prose([
        "voice_quality_type == 'breathy'",
        "speaker_sex == 'female'",
    ])
    assert result == "breathy voice_quality_type, female speaker_sex"


def test_summarize_double_quoted_equality():
    result = _format_conditions_prose(['task == "speech"'])
    assert result == "speech task"
