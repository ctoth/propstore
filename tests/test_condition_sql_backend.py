from __future__ import annotations

import sqlite3

from propstore.core.conditions import (
    ConditionBinary,
    ConditionBinaryOp,
    ConditionChoice,
    ConditionLiteral,
    ConditionMembership,
    ConditionReference,
    ConditionSourceSpan,
    ConditionUnary,
    ConditionUnaryOp,
    ConditionValueKind,
)
from propstore.core.conditions.sql_backend import (
    SqlConditionFragment,
    condition_ir_to_sql,
)
from propstore.core.id_types import ConceptId


SPAN = ConditionSourceSpan(0, 1)


def test_condition_ir_emits_parameterized_sql_fragment() -> None:
    condition = ConditionBinary(
        op=ConditionBinaryOp.AND,
        left=ConditionBinary(
            op=ConditionBinaryOp.GREATER_THAN,
            left=_numeric_ref("temperature"),
            right=ConditionLiteral(21, ConditionValueKind.NUMERIC, SPAN),
            span=SPAN,
        ),
        right=ConditionMembership(
            element=_string_ref("phase"),
            options=(
                ConditionLiteral("draft", ConditionValueKind.STRING, SPAN),
                ConditionLiteral("review", ConditionValueKind.STRING, SPAN),
            ),
            span=SPAN,
        ),
        span=SPAN,
    )

    fragment = condition_ir_to_sql(condition)

    assert fragment == SqlConditionFragment(
        sql='(("temperature" > ?) AND ("phase" IN (?, ?)))',
        parameters=(21, "draft", "review"),
    )


def test_condition_sql_fragment_evaluates_against_sqlite_rows() -> None:
    condition = ConditionBinary(
        op=ConditionBinaryOp.AND,
        left=ConditionBinary(
            op=ConditionBinaryOp.GREATER_THAN_OR_EQUAL,
            left=ConditionBinary(
                op=ConditionBinaryOp.ADD,
                left=_numeric_ref("x"),
                right=ConditionLiteral(2, ConditionValueKind.NUMERIC, SPAN),
                span=SPAN,
            ),
            right=ConditionLiteral(5, ConditionValueKind.NUMERIC, SPAN),
            span=SPAN,
        ),
        right=ConditionUnary(
            op=ConditionUnaryOp.NOT,
            operand=_boolean_ref("archived"),
            span=SPAN,
        ),
        span=SPAN,
    )
    fragment = condition_ir_to_sql(condition)

    connection = sqlite3.connect(":memory:")
    connection.execute('CREATE TABLE observations ("x" INTEGER, "archived" INTEGER)')
    connection.executemany(
        'INSERT INTO observations ("x", "archived") VALUES (?, ?)',
        [(3, 0), (2, 0), (5, 1)],
    )

    count = connection.execute(
        f"SELECT COUNT(*) FROM observations WHERE {fragment.sql}",
        fragment.parameters,
    ).fetchone()[0]

    assert count == 1


def test_condition_sql_quotes_identifiers_and_never_interpolates_literals() -> None:
    condition = ConditionBinary(
        op=ConditionBinaryOp.EQUAL,
        left=_string_ref('phase"name'),
        right=ConditionLiteral(
            "draft'); DROP TABLE observations; --",
            ConditionValueKind.STRING,
            SPAN,
        ),
        span=SPAN,
    )

    fragment = condition_ir_to_sql(condition)

    assert fragment.sql == '("phase""name" = ?)'
    assert "DROP TABLE" not in fragment.sql
    assert fragment.parameters == ("draft'); DROP TABLE observations; --",)


def test_condition_sql_refuses_conditionals() -> None:
    condition = ConditionChoice(
        condition=_boolean_ref("enabled"),
        when_true=ConditionLiteral(True, ConditionValueKind.BOOLEAN, SPAN),
        when_false=ConditionLiteral(False, ConditionValueKind.BOOLEAN, SPAN),
        span=SPAN,
    )

    try:
        condition_ir_to_sql(condition)
    except ValueError as exc:
        assert "ConditionChoice cannot be projected to SQL" in str(exc)
    else:
        raise AssertionError("ConditionChoice SQL projection should be refused")


def _numeric_ref(name: str) -> ConditionReference:
    return ConditionReference(
        concept_id=ConceptId(f"ps:concept:{name}"),
        source_name=name,
        value_kind=ConditionValueKind.NUMERIC,
        span=SPAN,
    )


def _boolean_ref(name: str) -> ConditionReference:
    return ConditionReference(
        concept_id=ConceptId(f"ps:concept:{name}"),
        source_name=name,
        value_kind=ConditionValueKind.BOOLEAN,
        span=SPAN,
    )


def _string_ref(name: str) -> ConditionReference:
    return ConditionReference(
        concept_id=ConceptId(f"ps:concept:{name}"),
        source_name=name,
        value_kind=ConditionValueKind.STRING,
        span=SPAN,
    )
