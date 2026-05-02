"""Property-based tests for the propstore compiler (T4).

Uses hypothesis to test CEL tokenizer and numeric interval comparison
with randomized inputs.
"""
from __future__ import annotations

import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

from cel_parser import (
    Call,
    DoubleLit,
    Ident,
    IntLit,
    RESERVED_WORDS,
    StringLit,
    parse,
)
from propstore.core.conditions.cel_frontend import check_cel_expression
from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.conflict_detector import (
    ConflictClass,
    detect_conflicts as _detect_conflicts,
)
from propstore.conflict_detector.collectors import conflict_claim_from_payload
from propstore.conflict_detector.models import ConflictClaim
from tests.conftest import make_cel_registry, make_concept_registry


# ── CEL tokenizer property tests ─────────────────────────────────────


_VALID_IDENT = st.from_regex(r"[a-z][a-z0-9_]{0,15}", fullmatch=True)
_VALID_OP = st.sampled_from(["==", "!=", ">", "<", ">=", "<="])
_VALID_INT = st.integers(min_value=0, max_value=9999)
_VALID_FLOAT = st.floats(min_value=0.1, max_value=9999.0, allow_nan=False, allow_infinity=False)
_VALID_STRING_LIT = st.from_regex(r"[a-z][a-z_]{0,10}", fullmatch=True)


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


@pytest.mark.property
@given(name=_VALID_IDENT, op=_VALID_OP, val=_VALID_INT)
@settings()
def test_parser_simple_int_comparison(name, op, val):
    """Parser should handle any simple 'ident op integer' expression."""
    assume(name not in RESERVED_WORDS)
    expr = f"{name} {op} {val}"
    ast = parse(expr)
    assert isinstance(ast, Call)
    assert len(ast.args) == 2
    left, right = ast.args
    assert isinstance(left, Ident) and left.name == name
    assert isinstance(right, IntLit) and right.value == val


@pytest.mark.property
@given(name=_VALID_IDENT, op=_VALID_OP, val=_VALID_FLOAT)
@settings()
def test_parser_simple_float_comparison(name, op, val):
    """Parser should handle any simple 'ident op float' expression."""
    assume(name not in RESERVED_WORDS)
    expr = f"{name} {op} {val}"
    ast = parse(expr)
    assert isinstance(ast, Call)
    left, right = ast.args
    assert isinstance(left, Ident) and left.name == name
    assert isinstance(right, DoubleLit)


@pytest.mark.property
@given(name=_VALID_IDENT, val=_VALID_STRING_LIT)
@settings()
def test_parser_string_equality(name, val):
    """Parser should handle 'ident == string_literal' expressions."""
    assume(name not in RESERVED_WORDS)
    expr = f"{name} == '{val}'"
    ast = parse(expr)
    assert isinstance(ast, Call)
    left, right = ast.args
    assert isinstance(left, Ident) and left.name == name
    assert isinstance(right, StringLit) and right.value == val


@pytest.mark.property
@given(
    name_a=_VALID_IDENT,
    name_b=_VALID_IDENT,
    op_a=_VALID_OP,
    op_b=_VALID_OP,
    val_a=_VALID_INT,
    val_b=_VALID_INT,
)
@settings()
def test_parser_compound_expression(name_a, name_b, op_a, op_b, val_a, val_b):
    """Parser should handle compound expressions with &&."""
    assume(name_a not in RESERVED_WORDS)
    assume(name_b not in RESERVED_WORDS)
    expr = f"{name_a} {op_a} {val_a} && {name_b} {op_b} {val_b}"
    ast = parse(expr)
    assert isinstance(ast, Call)
    assert ast.function == "_&&_"


# ── Numeric interval comparison property tests ───────────────────────


def _make_parameter_claim(claim_id, concept_id, value, unit="Hz", conditions=None):
    """Build a minimal parameter claim dict for testing."""
    claim = {
        "id": claim_id,
        "type": "parameter",
        "output_concept": concept_id,
        "unit": unit,
        "conditions": conditions or [],
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


def _make_claim_file(claims, filename="test_paper"):
    records = []
    for claim_payload in claims:
        claim = conflict_claim_from_payload(claim_payload, source_paper=filename)
        assert claim is not None
        records.append(claim)
    return records


def _make_registry():
    return {
        "concept1": {
            "id": "concept1",
            "canonical_name": "fundamental_frequency",
            "form": "frequency",
            "status": "accepted",
            "definition": "F0",
        },
    }


@pytest.mark.property
@given(
    lo=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    width_a=st.floats(min_value=10.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    width_b=st.floats(min_value=10.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    offset=st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False),
)
@settings(deadline=None)
def test_overlapping_intervals_compatible(lo, width_a, width_b, offset):
    """Two ranges that overlap should be COMPATIBLE (no conflict records)."""
    # Build overlapping intervals by construction
    lo_a = lo
    hi_a = lo + width_a
    lo_b = lo + offset  # starts within first range since offset < width_a is likely
    hi_b = lo_b + width_b
    assume(lo_a < hi_a and lo_b < hi_b)
    assume(max(lo_a, lo_b) < min(hi_a, hi_b))

    claims = [
        _make_parameter_claim("claim1", "concept1", [lo_a, hi_a]),
        _make_parameter_claim("claim2", "concept1", [lo_b, hi_b]),
    ]
    cf = _make_claim_file(claims)
    records = detect_conflicts([cf], _make_registry())
    assert len(records) == 0, f"Overlapping [{lo_a},{hi_a}] and [{lo_b},{hi_b}] should be compatible"


@pytest.mark.property
@given(
    lo_a=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    width_a=st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    gap=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    width_b=st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False),
)
@settings(deadline=None)
def test_disjoint_intervals_conflict(lo_a, width_a, gap, width_b):
    """Two non-overlapping ranges (with a gap) should produce a CONFLICT."""
    # Build disjoint intervals by construction
    hi_a = lo_a + width_a
    lo_b = hi_a + gap
    hi_b = lo_b + width_b

    claims = [
        _make_parameter_claim("claim1", "concept1", [lo_a, hi_a]),
        _make_parameter_claim("claim2", "concept1", [lo_b, hi_b]),
    ]
    cf = _make_claim_file(claims)
    records = detect_conflicts([cf], _make_registry())
    assert len(records) == 1, f"Disjoint [{lo_a},{hi_a}] and [{lo_b},{hi_b}] should conflict"
    assert records[0].warning_class == ConflictClass.CONFLICT


@pytest.mark.property
@given(
    val=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
)
@settings()
def test_identical_scalar_always_compatible(val):
    """Identical scalar values should always be COMPATIBLE."""
    claims = [
        _make_parameter_claim("claim1", "concept1", val),
        _make_parameter_claim("claim2", "concept1", val),
    ]
    cf = _make_claim_file(claims)
    records = detect_conflicts([cf], _make_registry())
    assert len(records) == 0
