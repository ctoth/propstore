"""Regression tests for parameterization conflict detection."""

from pathlib import Path

import warnings

from propstore.conflict_detector.models import ConflictClass
from propstore.param_conflicts import _detect_param_conflicts
from propstore.validate_claims import LoadedClaimFile


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
    claim_file = LoadedClaimFile(
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
