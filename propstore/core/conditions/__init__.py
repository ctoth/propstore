"""Core condition IR and frontend adapters."""

from __future__ import annotations

from propstore.core.conditions.cel_frontend import check_condition_ir, condition_ir_from_cel
from propstore.core.conditions.checked import (
    CheckedCondition,
    CheckedConditionSet,
    checked_condition_set,
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

__all__ = [
    "CheckedCondition",
    "CheckedConditionSet",
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
    "check_condition_ir",
    "checked_condition_set",
    "condition_ir_to_python_ast",
    "condition_ir_from_cel",
    "evaluate_condition_ir",
]
