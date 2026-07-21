"""Parameterization-derivation conflict detection (single-hop + transitive).

Ported from the reference ``test_param_conflicts`` suite to the rewrite's
substrate-direct construction: concept registries are plain dicts, claims are
built directly as ``ConflictClaim`` values, CEL registries are
``condition_ir.ConceptInfo`` maps, and lifting uses ``Context`` /
``LiftingSystem`` directly. The behavioral contract is preserved — Eq(...)
parameterizations derive values without warnings, SI normalization flows through
single-hop and transitive derivations, derived conditions accumulate,
unlifted-context pairs are CONTEXT_PHI_NODE, transitive conflicts are
order-independent, and unexpected SymPy faults propagate.

Numeric evaluation is delegated to the ``human-to-sympy`` substrate; this suite
never imports sympy except to patch its parser in the propagation test.
"""

from __future__ import annotations

import warnings
from typing import Any
from unittest.mock import patch

import pytest
from condition_ir import KindType, to_cel_exprs

from human_to_sympy import parse_cached
from propstore.conflict_detector import (
    ConflictClass,
    detect_conflicts,
    detect_transitive_conflicts,
)
from propstore.conflict_detector.models import ConflictClaim
from propstore.core.graph_types import ParameterizationEdge
from propstore.core.id_types import to_concept_id, to_concept_ids
from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
)
from propstore.families.claims import ClaimType, Exactness
from propstore.conflict_detector.parameterization_conflicts import (
    detect_parameterization_conflicts,
)
from propstore.context_lifting import LiftingSystem
from propstore.dimensions import UnitConversion
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.forms import FormDefinition


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


_ConceptEntry = tuple[Concept, tuple[ParameterizationEdge, ...]]


def _concept(
    concept_id: str,
    *,
    form: str = "quantity",
    parameterizations: list[dict[str, Any]] | None = None,
) -> _ConceptEntry:
    """Typed fixture: a canonical Concept plus its parameterization edges."""

    concept = Concept(
        concept_id=concept_id,
        canonical_name=concept_id,
        lexical_entry=LexicalEntry(
            identifier=f"entry:{concept_id}",
            canonical_form=LexicalForm(written_rep=concept_id, language="en"),
            senses=(LexicalSense(reference=OntologyReference(uri=f"u:{concept_id}")),),
            physical_dimension_form=form,
        ),
    )
    edges = tuple(
        ParameterizationEdge(
            output_concept_id=to_concept_id(concept_id),
            input_concept_ids=to_concept_ids(relationship["inputs"]),
            sympy=relationship["sympy"],
            exactness=(
                None
                if relationship.get("exactness") is None
                else Exactness(relationship["exactness"])
            ),
            conditions=to_cel_exprs(relationship.get("conditions") or ()),
        )
        for relationship in (parameterizations or ())
    )
    return concept, edges


def _inputs(
    registry: dict[str, _ConceptEntry],
) -> tuple[dict[str, Concept], dict[str, tuple[ParameterizationEdge, ...]]]:
    concepts = {concept_id: entry[0] for concept_id, entry in registry.items()}
    parameterizations = {
        concept_id: entry[1] for concept_id, entry in registry.items() if entry[1]
    }
    return concepts, parameterizations


def _claim(payload: dict[str, Any]) -> ConflictClaim:
    """Test fixture: a ConflictClaim from the suite's compact dict spelling."""

    claim_type = payload.get("type")
    return ConflictClaim(
        claim_id=payload["id"],
        claim_type=None if claim_type is None else ClaimType(claim_type),
        output_concept_id=payload.get("output_concept"),
        value=payload.get("value"),
        unit=payload.get("unit"),
        context_id=payload.get("context"),
        conditions=to_cel_exprs(payload.get("conditions") or ()),
    )


def _param_claim(
    claim_id: str, concept_id: str, value: float, **extra: Any
) -> ConflictClaim:
    return _claim(
        {
            "id": claim_id,
            "type": "parameter",
            "output_concept": concept_id,
            "value": value,
            **extra,
        }
    )


# ── single-hop derivation ────────────────────────────────────────────


def test_detect_param_conflicts_handles_equality_parameterizations_without_warning() -> (
    None
):
    by_concept = {
        "concept1": [_claim({"id": "claim_a", "value": 10.0})],
        "concept2": [_claim({"id": "claim_b", "value": 9.807})],
        "concept3": [_claim({"id": "claim_c", "value": 99.0})],
    }
    concept_registry = {
        "concept1": _concept("concept1"),
        "concept2": _concept("concept2"),
        "concept3": _concept(
            "concept3",
            parameterizations=[
                {
                    "exactness": "exact",
                    "inputs": ["concept1", "concept2"],
                    "sympy": "Eq(concept3, concept1 * concept2)",
                }
            ],
        ),
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        concepts, parameterizations = _inputs(concept_registry)
        records = detect_parameterization_conflicts(
            by_concept, concepts, parameterizations, []
        )

    param_warnings = [
        warning
        for warning in caught
        if "Could not evaluate parameterization for concept3" in str(warning.message)
    ]
    assert param_warnings == []
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert records[0].concept_id == "concept3"
    assert records[0].claim_b_id == "claim_a"


def test_same_value_different_units_no_conflict() -> None:
    forms = {"frequency": _frequency_form()}
    by_concept = {
        "freq_input": [
            _claim({"id": "claim_hz", "value": 200.0, "unit": "Hz"}),
            _claim({"id": "claim_khz", "value": 0.2, "unit": "kHz"}),
        ],
        "freq_output": [_claim({"id": "claim_out", "value": 100.0})],
    }
    concept_registry = {
        "freq_input": _concept("freq_input", form="frequency"),
        "freq_output": _concept(
            "freq_output",
            parameterizations=[
                {
                    "exactness": "exact",
                    "inputs": ["freq_input"],
                    "sympy": "Eq(freq_output, freq_input / 2)",
                }
            ],
        ),
    }
    concepts, parameterizations = _inputs(concept_registry)
    records = detect_parameterization_conflicts(
        by_concept, concepts, parameterizations, [], forms=forms
    )
    assert records == []


def test_different_value_different_units_conflict() -> None:
    forms = {"frequency": _frequency_form()}
    by_concept = {
        "freq_input": [_claim({"id": "claim_khz", "value": 0.5, "unit": "kHz"})],
        "freq_output": [_claim({"id": "claim_out", "value": 100.0})],
    }
    concept_registry = {
        "freq_input": _concept("freq_input", form="frequency"),
        "freq_output": _concept(
            "freq_output",
            parameterizations=[
                {
                    "exactness": "exact",
                    "inputs": ["freq_input"],
                    "sympy": "Eq(freq_output, freq_input / 2)",
                }
            ],
        ),
    }
    concepts, parameterizations = _inputs(concept_registry)
    records = detect_parameterization_conflicts(
        by_concept, concepts, parameterizations, [], forms=forms
    )
    # 0.5 kHz -> 500 Hz (SI) -> derived 250, direct 100: conflict; value_b proves SI.
    # freq_output's form ("quantity") is not in `forms`, so the derived state's
    # unit is honestly unknown and the record renders the bare SI number.
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert records[0].value_b == "250.0"


def test_conflict_record_renders_both_sides_with_their_units() -> None:
    """A record's two sides are in different unit systems; both must say which.

    ``value_a`` is the authored claim (kHz here); ``value_b`` is the derived
    value, which is always SI. Rendering both unlabelled made a genuine conflict
    read as the uninterpretable "0.1 vs 250.0".
    """

    forms = {"frequency": _frequency_form()}
    by_concept = {
        "freq_input": [_claim({"id": "claim_khz", "value": 0.5, "unit": "kHz"})],
        "freq_output": [_claim({"id": "claim_out", "value": 0.1, "unit": "kHz"})],
    }
    concept_registry = {
        "freq_input": _concept("freq_input", form="frequency"),
        "freq_output": _concept(
            "freq_output",
            form="frequency",
            parameterizations=[
                {
                    "exactness": "exact",
                    "inputs": ["freq_input"],
                    "sympy": "Eq(freq_output, freq_input / 2)",
                }
            ],
        ),
    }
    concepts, parameterizations = _inputs(concept_registry)
    records = detect_parameterization_conflicts(
        by_concept, concepts, parameterizations, [], forms=forms
    )
    # 0.5 kHz -> 500 Hz -> derived 250 Hz; direct 0.1 kHz -> 100 Hz: conflict.
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert records[0].value_a == "0.1 kHz"
    assert records[0].value_b == "250.0 Hz"


def test_single_hop_conflict_carries_derived_conditions() -> None:
    by_concept = {
        "concept_in": [
            _claim(
                {
                    "id": "claim_in",
                    "value": 10.0,
                    "conditions": ["task == 'speech'"],
                    "context": "ctx_input",
                }
            )
        ],
        "concept_out": [
            _claim(
                {
                    "id": "claim_out",
                    "value": 100.0,
                    "conditions": ["task == 'speech'", "mode == 'normal'"],
                    "context": "ctx_input",
                }
            )
        ],
    }
    concept_registry = {
        "concept_in": _concept("concept_in", form="frequency"),
        "concept_out": _concept(
            "concept_out",
            form="frequency",
            parameterizations=[
                {
                    "exactness": "exact",
                    "inputs": ["concept_in"],
                    "sympy": "Eq(concept_out, concept_in * 2)",
                    "conditions": ["mode == 'normal'"],
                }
            ],
        ),
    }
    concepts, parameterizations = _inputs(concept_registry)
    records = detect_parameterization_conflicts(
        by_concept, concepts, parameterizations, []
    )
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert [str(condition) for condition in records[0].conditions_b] == [
        "mode == 'normal'",
        "task == 'speech'",
    ]


def test_single_hop_conflict_requires_lifted_contexts() -> None:
    concept_registry = {
        "concept_in": _concept("concept_in", form="frequency"),
        "concept_out": _concept(
            "concept_out",
            form="frequency",
            parameterizations=[
                {
                    "exactness": "exact",
                    "inputs": ["concept_in"],
                    "sympy": "Eq(concept_out, concept_in * 2)",
                }
            ],
        ),
    }
    claims = [
        _param_claim("claim_in", "concept_in", 10.0, context="ctx_input"),
        _param_claim("claim_out", "concept_out", 100.0, context="ctx_direct"),
    ]
    lifting_system = LiftingSystem(
        contexts=(
            Context(context_id="ctx_input", name="input"),
            Context(context_id="ctx_direct", name="direct"),
        ),
    )
    concepts, parameterizations = _inputs(concept_registry)
    records = detect_conflicts(
        claims,
        concepts,
        {},
        lifting_system=lifting_system,
        parameterizations=parameterizations,
    )
    assert len(records) == 1
    assert records[0].warning_class == ConflictClass.CONTEXT_PHI_NODE


# ── transitive derivation ────────────────────────────────────────────


def test_transitive_propagation_normalizes_units() -> None:
    forms = {"frequency": _frequency_form()}
    concept_registry = {
        "concept_a": _concept("concept_a", form="frequency"),
        "concept_b": _concept(
            "concept_b",
            parameterizations=[
                {
                    "exactness": "exact",
                    "inputs": ["concept_a"],
                    "sympy": "Eq(concept_b, concept_a * 2)",
                }
            ],
        ),
        "concept_c": _concept(
            "concept_c",
            parameterizations=[
                {
                    "exactness": "exact",
                    "inputs": ["concept_b"],
                    "sympy": "Eq(concept_c, concept_b + 100)",
                }
            ],
        ),
    }
    claims = [
        _param_claim("claim_a", "concept_a", 0.1, unit="kHz"),
        _param_claim("claim_b_direct", "concept_b", 200.0),
        _param_claim("claim_c_direct", "concept_c", 300.0),
    ]
    concepts, parameterizations = _inputs(concept_registry)
    conflicts = detect_transitive_conflicts(
        claims, concepts, parameterizations, forms=forms
    )
    # 0.1 kHz -> 100 Hz; chain 100*2=200, 200+100=300 == direct 300: no conflict.
    param_conflicts = [
        record
        for record in conflicts
        if record.warning_class == ConflictClass.PARAM_CONFLICT
    ]
    assert param_conflicts == []


def test_transitive_conflict_detection_is_order_independent() -> None:
    concept_registry = {
        "concept_in": _concept("concept_in", form="frequency"),
        "concept_mid": _concept(
            "concept_mid",
            form="frequency",
            parameterizations=[
                {
                    "exactness": "exact",
                    "inputs": ["concept_in"],
                    "sympy": "Eq(concept_mid, concept_in * 2)",
                }
            ],
        ),
        "concept_out": _concept(
            "concept_out",
            form="frequency",
            parameterizations=[
                {
                    "exactness": "exact",
                    "inputs": ["concept_mid"],
                    "sympy": "Eq(concept_out, concept_mid + 5)",
                }
            ],
        ),
    }
    forward = [
        _param_claim("in_a", "concept_in", 10.0),
        _param_claim("in_b", "concept_in", 20.0),
        _param_claim("out_direct", "concept_out", 25.0),
    ]
    reverse = [
        _param_claim("in_b", "concept_in", 20.0),
        _param_claim("in_a", "concept_in", 10.0),
        _param_claim("out_direct", "concept_out", 25.0),
    ]
    concepts, parameterizations = _inputs(concept_registry)
    first_records = detect_transitive_conflicts(forward, concepts, parameterizations)
    second_records = detect_transitive_conflicts(reverse, concepts, parameterizations)
    assert len(first_records) == 1
    assert len(second_records) == 1
    assert first_records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert second_records[0].warning_class == ConflictClass.PARAM_CONFLICT
    assert first_records[0].value_b == second_records[0].value_b == "45.0"


# ── error propagation ────────────────────────────────────────────────


def test_runtime_error_from_sympy_parameterization_propagates() -> None:
    by_concept = {
        "a": [_claim({"id": "claim_a", "value": 2.0})],
        "b": [_claim({"id": "claim_b", "value": 3.0})],
        "derived": [_claim({"id": "claim_derived", "value": 10.0})],
    }
    concept_registry = {
        "a": _concept("a"),
        "b": _concept("b"),
        "derived": _concept(
            "derived",
            parameterizations=[
                {
                    "exactness": "exact",
                    "inputs": ["a", "b"],
                    "sympy": "Eq(derived, a * b)",
                }
            ],
        ),
    }
    parse_cached.cache_clear()
    try:
        with patch(
            "sympy.parsing.sympy_parser.parse_expr",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                detect_parameterization_conflicts(
                    by_concept, *_inputs(concept_registry), []
                )
    finally:
        parse_cached.cache_clear()
