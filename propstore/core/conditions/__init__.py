"""Core condition IR and frontend adapters."""

from __future__ import annotations

from propstore.core.conditions.cel_frontend import condition_ir_from_cel
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

__all__ = [
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
    "condition_ir_to_python_ast",
    "condition_ir_from_cel",
    "evaluate_condition_ir",
]
