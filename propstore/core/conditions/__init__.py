"""Core condition IR and frontend adapters."""

from __future__ import annotations

from propstore.core.conditions.checked import (
    CheckedCondition,
    CheckedConditionSet,
    checked_condition_set,
)
from propstore.core.conditions.codec import condition_ir_from_json, condition_ir_to_json
from propstore.core.conditions.estree_backend import (
    EstreeArrayExpression,
    EstreeBinaryExpression,
    EstreeCallExpression,
    EstreeConditionalExpression,
    EstreeExpression,
    EstreeIdentifier,
    EstreeLiteral,
    EstreeLogicalExpression,
    EstreeMemberExpression,
    EstreeUnaryExpression,
    condition_ir_to_estree,
    evaluate_estree_expression,
)
from propstore.core.conditions.ir import (
    ConditionBinary,
    ConditionBinaryOp,
    ConditionChoice,
    ConditionIR,
    ConditionLiteral,
    ConditionMembership,
    ConditionReference,
    ConditionSourceSpan,
    ConditionUnary,
    ConditionUnaryOp,
    ConditionValueKind,
)
from propstore.core.conditions.python_backend import (
    condition_ir_to_python_ast,
    evaluate_condition_ir,
)
from propstore.core.conditions.sql_backend import (
    SqlConditionFragment,
    condition_ir_to_sql,
)
from propstore.core.conditions.solver import (
    DEFAULT_Z3_TIMEOUT_MS,
    ConditionSolver,
    SolverResult,
    SolverSat,
    SolverUnknown,
    SolverUnknownReason,
    SolverUnsat,
    Z3TranslationError,
    Z3UnknownError,
    solver_result_from_z3,
)
from propstore.core.conditions.z3_backend import (
    condition_ir_to_z3,
    z3_bindings_for_values,
)


def __getattr__(name: str):
    if name in {"check_condition_ir", "condition_ir_from_cel"}:
        from propstore.core.conditions.cel_frontend import (
            check_condition_ir,
            condition_ir_from_cel,
        )

        return {
            "check_condition_ir": check_condition_ir,
            "condition_ir_from_cel": condition_ir_from_cel,
        }[name]
    raise AttributeError(name)

__all__ = [
    "CheckedCondition",
    "CheckedConditionSet",
    "ConditionSolver",
    "ConditionBinary",
    "ConditionBinaryOp",
    "ConditionChoice",
    "ConditionIR",
    "ConditionLiteral",
    "ConditionMembership",
    "ConditionReference",
    "ConditionSourceSpan",
    "ConditionUnary",
    "ConditionUnaryOp",
    "ConditionValueKind",
    "DEFAULT_Z3_TIMEOUT_MS",
    "EstreeArrayExpression",
    "EstreeBinaryExpression",
    "EstreeCallExpression",
    "EstreeConditionalExpression",
    "EstreeExpression",
    "EstreeIdentifier",
    "EstreeLiteral",
    "EstreeLogicalExpression",
    "EstreeMemberExpression",
    "EstreeUnaryExpression",
    "SqlConditionFragment",
    "SolverResult",
    "SolverSat",
    "SolverUnknown",
    "SolverUnknownReason",
    "SolverUnsat",
    "Z3TranslationError",
    "Z3UnknownError",
    "checked_condition_set",
    "condition_ir_from_json",
    "condition_ir_to_estree",
    "condition_ir_to_json",
    "condition_ir_to_python_ast",
    "condition_ir_to_sql",
    "condition_ir_to_z3",
    "evaluate_estree_expression",
    "evaluate_condition_ir",
    "solver_result_from_z3",
    "z3_bindings_for_values",
]
