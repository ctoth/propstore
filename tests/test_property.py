"""Property-based tests for the propstore compiler (T4).

Uses hypothesis to test CEL tokenizer and numeric interval comparison
with randomized inputs.
"""
from __future__ import annotations

from hypothesis import given, assume, settings
from hypothesis import strategies as st

from propstore.cel_checker import (
    ConceptInfo,
    KindType,
    check_cel_expression,
    tokenize,
)
from propstore.conflict_detector import (
    ConflictClass,
    detect_conflicts,
)
from propstore.validate_claims import LoadedClaimFile
from pathlib import Path


# ── CEL tokenizer property tests ─────────────────────────────────────


_VALID_IDENT = st.from_regex(r"[a-z][a-z0-9_]{0,15}", fullmatch=True)
_VALID_OP = st.sampled_from(["==", "!=", ">", "<", ">=", "<="])
_VALID_INT = st.integers(min_value=0, max_value=9999)
_VALID_FLOAT = st.floats(min_value=0.1, max_value=9999.0, allow_nan=False, allow_infinity=False)
_VALID_STRING_LIT = st.from_regex(r"[a-z][a-z_]{0,10}", fullmatch=True)


@given(name=_VALID_IDENT, op=_VALID_OP, val=_VALID_INT)
@settings(max_examples=50)
def test_tokenizer_simple_int_comparison(name, op, val):
    """Tokenizer should handle any simple 'ident op integer' expression."""
    assume(name not in ("true", "false", "in"))
    expr = f"{name} {op} {val}"
    tokens = tokenize(expr)
    # Should produce at least 3 tokens: ident, op, number
    assert len(tokens) >= 3
    assert tokens[0].value == name
    assert tokens[1].value == op


@given(name=_VALID_IDENT, op=_VALID_OP, val=_VALID_FLOAT)
@settings(max_examples=50)
def test_tokenizer_simple_float_comparison(name, op, val):
    """Tokenizer should handle any simple 'ident op float' expression."""
    assume(name not in ("true", "false", "in"))
    expr = f"{name} {op} {val}"
    tokens = tokenize(expr)
    assert len(tokens) >= 3
    assert tokens[0].value == name


@given(name=_VALID_IDENT, val=_VALID_STRING_LIT)
@settings(max_examples=50)
def test_tokenizer_string_equality(name, val):
    """Tokenizer should handle 'ident == string_literal' expressions."""
    assume(name not in ("true", "false", "in"))
    expr = f"{name} == '{val}'"
    tokens = tokenize(expr)
    assert len(tokens) >= 3
    assert tokens[0].value == name
    assert tokens[2].value == val


@given(
    name_a=_VALID_IDENT,
    name_b=_VALID_IDENT,
    op_a=_VALID_OP,
    op_b=_VALID_OP,
    val_a=_VALID_INT,
    val_b=_VALID_INT,
)
@settings(max_examples=30)
def test_tokenizer_compound_expression(name_a, name_b, op_a, op_b, val_a, val_b):
    """Tokenizer should handle compound expressions with &&."""
    assume(name_a not in ("true", "false", "in"))
    assume(name_b not in ("true", "false", "in"))
    expr = f"{name_a} {op_a} {val_a} && {name_b} {op_b} {val_b}"
    tokens = tokenize(expr)
    # Should have tokens for both sides plus the && operator
    assert len(tokens) >= 7
    ops = [t.value for t in tokens if t.type.name == "OP"]
    assert "&&" in ops


# ── Numeric interval comparison property tests ───────────────────────


def _make_parameter_claim(claim_id, concept_id, value, unit="Hz", conditions=None):
    """Build a minimal parameter claim dict for testing."""
    return {
        "id": claim_id,
        "type": "parameter",
        "concept": concept_id,
        "value": value if isinstance(value, list) else [value],
        "unit": unit,
        "conditions": conditions or [],
        "provenance": {"paper": "test", "page": 1},
    }


def _make_claim_file(claims, filename="test_paper"):
    return LoadedClaimFile(
        filename=filename,
        filepath=Path(f"/fake/{filename}.yaml"),
        data={"source": {"paper": filename}, "claims": claims},
    )


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


@given(
    lo=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    width_a=st.floats(min_value=10.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    width_b=st.floats(min_value=10.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    offset=st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, deadline=None)
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


@given(
    lo_a=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    width_a=st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    gap=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    width_b=st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, deadline=None)
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


@given(
    val=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50)
def test_identical_scalar_always_compatible(val):
    """Identical scalar values should always be COMPATIBLE."""
    claims = [
        _make_parameter_claim("claim1", "concept1", val),
        _make_parameter_claim("claim2", "concept1", val),
    ]
    cf = _make_claim_file(claims)
    records = detect_conflicts([cf], _make_registry())
    assert len(records) == 0
