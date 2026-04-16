from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.conflict_detector import detect_conflicts as _detect_conflicts
from propstore.conflict_detector.collectors import conflict_claim_from_payload
from propstore.conflict_detector.models import ConflictClaimVariable
from propstore.conflict_detector.models import ConflictClaim
from propstore.equation_comparison import (
    EquationComparisonStatus,
    EquationFailure,
    EquationFailureCode,
    EquationNormalization,
    canonicalize_equation,
    compare_equation_claims,
    structural_signature,
)
from propstore.equation_parser import (
    BinaryExpr,
    EquationExpr,
    FunctionExpr,
    NumberExpr,
    SymbolExpr,
    UnaryExpr,
    render_equation,
)
from tests.conftest import make_cel_registry, make_concept_registry


_BASE_VARIABLES = (
    ConflictClaimVariable(concept_id="concept2", symbol="x", role="dependent"),
    ConflictClaimVariable(concept_id="concept1", symbol="y", role="independent"),
    ConflictClaimVariable(concept_id="concept3", symbol="z", role="independent"),
)


def _flatten_claims(claims_or_files):
    flattened = []
    for item in claims_or_files:
        if isinstance(item, ConflictClaim):
            flattened.append(item)
        else:
            flattened.extend(item)
    return flattened


def detect_conflicts(claim_files, registry, context_hierarchy=None):
    return _detect_conflicts(
        _flatten_claims(claim_files),
        registry,
        make_cel_registry(registry),
        context_hierarchy=context_hierarchy,
    )


def _make_claim(
    expression: str,
    *,
    claim_id: str = "eq",
    variables: tuple[ConflictClaimVariable, ...] = _BASE_VARIABLES,
) -> dict:
    return {
        "id": claim_id,
        "type": "equation",
        "expression": expression,
        "variables": [
            {
                "symbol": variable.symbol,
                "concept": variable.concept_id,
                "role": variable.role,
            }
            for variable in variables
        ],
        "conditions": ["task == 'speech'"],
        "provenance": {"paper": "test", "page": 1},
    }


def _make_claim_file(*claims: dict) -> list[ConflictClaim]:
    records = []
    for claim_payload in claims:
        claim = conflict_claim_from_payload(claim_payload, source_paper="equations")
        assert claim is not None
        records.append(claim)
    return records


def _claim_from_expr(
    expr: EquationExpr,
    *,
    dependent_symbol: str = "x",
    dependent_concept: str = "length",
    independent_symbol: str = "y",
    independent_concept: str = "time",
) -> ConflictClaim:
    return ConflictClaim(
        claim_id="eq1",
        claim_type="equation",
        expression=f"{dependent_symbol} = {render_equation(expr)}",
        variables=(
            ConflictClaimVariable(
                concept_id=dependent_concept,
                symbol=dependent_symbol,
                role="dependent",
            ),
            ConflictClaimVariable(
                concept_id=independent_concept,
                symbol=independent_symbol,
                role="independent",
            ),
        ),
    )


def _rename_expr(expr: EquationExpr, mapping: dict[str, str], concept_mapping: dict[str, str]) -> EquationExpr:
    if isinstance(expr, NumberExpr):
        return expr
    if isinstance(expr, SymbolExpr):
        return SymbolExpr(
            symbol=mapping.get(expr.symbol, expr.symbol),
            concept_id=concept_mapping.get(expr.symbol, expr.concept_id),
        )
    if isinstance(expr, UnaryExpr):
        return UnaryExpr(operator=expr.operator, operand=_rename_expr(expr.operand, mapping, concept_mapping))
    if isinstance(expr, BinaryExpr):
        return BinaryExpr(
            operator=expr.operator,
            left=_rename_expr(expr.left, mapping, concept_mapping),
            right=_rename_expr(expr.right, mapping, concept_mapping),
        )
    if isinstance(expr, FunctionExpr):
        return FunctionExpr(
            name=expr.name,
            arguments=tuple(
                _rename_expr(argument, mapping, concept_mapping)
                for argument in expr.arguments
            ),
        )
    raise TypeError(f"unsupported expression: {expr!r}")


_number_tokens = st.sampled_from(["0", "1", "2", "3", "0.5", "1.25"])
_symbol_exprs = st.sampled_from([
    SymbolExpr(symbol="y", concept_id="time"),
    SymbolExpr(symbol="z", concept_id="task"),
])
_simple_exprs = st.recursive(
    st.one_of(
        _number_tokens.map(NumberExpr),
        _symbol_exprs,
    ),
    lambda children: st.one_of(
        st.builds(UnaryExpr, st.sampled_from(["+", "-"]), children),
        st.builds(BinaryExpr, st.sampled_from(["+", "-", "*", "^"]), children, children),
        st.builds(FunctionExpr, st.sampled_from(["log", "exp", "sqrt"]), st.tuples(children)),
    ),
    max_leaves=6,
)
_polynomial_exprs = st.recursive(
    st.one_of(_number_tokens.map(NumberExpr), st.just(SymbolExpr(symbol="y", concept_id="time"))),
    lambda children: st.one_of(
        st.builds(UnaryExpr, st.sampled_from(["+", "-"]), children),
        st.builds(BinaryExpr, st.sampled_from(["+", "-", "*"]), children, children),
    ),
    max_leaves=6,
)


@pytest.mark.property
@given(expr=_simple_exprs)
@settings(deadline=None, max_examples=40)
def test_render_parse_round_trip(expr: EquationExpr):
    from propstore.equation_parser import parse_equation
    from propstore.equation_parser import EquationSymbolBinding

    text = render_equation(expr)
    parsed = parse_equation(
        f"x = {text}",
        (
            EquationSymbolBinding(symbol="x", concept_id="length", role="dependent"),
            EquationSymbolBinding(symbol="y", concept_id="time", role="independent"),
            EquationSymbolBinding(symbol="z", concept_id="task", role="independent"),
        ),
    )

    assert not isinstance(parsed, EquationFailure)
    assert render_equation(parsed.rhs) == text


def test_render_preserves_left_nested_exponentiation() -> None:
    expr = BinaryExpr(
        operator="^",
        left=BinaryExpr(
            operator="^",
            left=NumberExpr("2"),
            right=NumberExpr("3"),
        ),
        right=NumberExpr("4"),
    )

    assert render_equation(expr) == "(2 ^ 3) ^ 4"


def test_render_preserves_division_on_multiplication_rhs() -> None:
    expr = BinaryExpr(
        operator="*",
        left=SymbolExpr(symbol="y", concept_id="time"),
        right=BinaryExpr(
            operator="/",
            left=NumberExpr("2"),
            right=NumberExpr("3"),
        ),
    )

    assert render_equation(expr) == "y * (2 / 3)"


@pytest.mark.property
@given(expr=_polynomial_exprs)
@settings(deadline=None, max_examples=40)
def test_canonicalization_is_idempotent(expr: EquationExpr):
    claim = _claim_from_expr(expr)
    first = canonicalize_equation(claim)
    second = canonicalize_equation(claim)

    assert isinstance(first, EquationNormalization)
    assert second == first


@pytest.mark.property
@given(expr=_polynomial_exprs)
@settings(deadline=None, max_examples=40)
def test_structural_signature_is_invariant_under_alpha_renaming(expr: EquationExpr):
    renamed_expr = _rename_expr(
        expr,
        mapping={"y": "b", "z": "c"},
        concept_mapping={"y": "time", "z": "task"},
    )
    base = _claim_from_expr(expr)
    renamed = _claim_from_expr(
        renamed_expr,
        dependent_symbol="a",
        dependent_concept="length",
        independent_symbol="b",
        independent_concept="time",
    )

    assert structural_signature(base) == structural_signature(renamed)


@pytest.mark.property
@given(
    coeff_a=st.integers(min_value=1, max_value=5),
    coeff_b=st.integers(min_value=1, max_value=5),
)
@settings(deadline=None, max_examples=25)
def test_equivalent_rewrites_normalize_identically(coeff_a: int, coeff_b: int):
    left = _claim_from_expr(
        BinaryExpr(
            operator="+",
            left=BinaryExpr(
                operator="*",
                left=NumberExpr(str(coeff_a)),
                right=SymbolExpr(symbol="y", concept_id="time"),
            ),
            right=BinaryExpr(
                operator="*",
                left=NumberExpr(str(coeff_b)),
                right=SymbolExpr(symbol="y", concept_id="time"),
            ),
        ),
    )
    right = _claim_from_expr(
        BinaryExpr(
            operator="*",
            left=NumberExpr(str(coeff_a + coeff_b)),
            right=SymbolExpr(symbol="y", concept_id="time"),
        ),
    )

    comparison = compare_equation_claims(left, right)
    assert comparison.status == EquationComparisonStatus.EQUIVALENT


@pytest.mark.property
@given(
    relation=st.sampled_from(["==", "<=", ">=", "=", "="]),
    unsupported_function=st.sampled_from(["And", "Piecewise", "Eq"]),
)
@settings(deadline=None, max_examples=20)
def test_invalid_or_unsupported_surfaces_fail_honestly(relation: str, unsupported_function: str):
    if relation == "=":
        text = f"x = {unsupported_function}(y)"
        expected_code = EquationFailureCode.UNSUPPORTED_SURFACE
    else:
        text = f"x {relation} y"
        expected_code = EquationFailureCode.INVALID_RELATION

    template = _claim_from_expr(SymbolExpr(symbol="y", concept_id="time"))
    result = canonicalize_equation(type(template)(
        claim_id="eq4",
        claim_type="equation",
        expression=text,
        variables=template.variables,
    ))

    assert isinstance(result, EquationFailure)
    assert result.code == expected_code


@pytest.mark.property
@given(
    left_offset=st.integers(min_value=1, max_value=5),
    right_offset=st.integers(min_value=1, max_value=5),
)
@settings(deadline=None, max_examples=25)
def test_equation_conflict_detection_is_symmetric(left_offset: int, right_offset: int):
    claim_a = _make_claim(f"x = y + {left_offset}", claim_id="claim_a")
    claim_b = _make_claim(f"x = y + {right_offset}", claim_id="claim_b")

    records_ab = detect_conflicts([_make_claim_file(claim_a, claim_b)], make_concept_registry())
    records_ba = detect_conflicts([_make_claim_file(claim_b, claim_a)], make_concept_registry())

    assert len(records_ab) == len(records_ba)
    if records_ab:
        assert records_ab[0].warning_class == records_ba[0].warning_class
