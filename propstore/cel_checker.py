"""Compatibility export for CEL condition checking.

Production CEL parsing and type-checking live in
``propstore.core.conditions.cel_frontend``. Registry types live in
``propstore.core.conditions.registry``.
"""

from __future__ import annotations

from propstore.core.conditions.cel_frontend import (
    ARITHMETIC_FUNCTIONS,
    EQUALITY_FUNCTIONS,
    LOGICAL_FUNCTIONS,
    ORDERING_FUNCTIONS,
    CelError,
    ExprType,
    check_cel_expression,
)
from propstore.core.conditions.registry import (
    ConceptInfo,
    KindType,
    condition_registry_fingerprint,
    scope_condition_registry,
    synthetic_category_concept,
    with_standard_synthetic_bindings,
    with_synthetic_concepts,
)

__all__ = [
    "ARITHMETIC_FUNCTIONS",
    "ConceptInfo",
    "CelError",
    "EQUALITY_FUNCTIONS",
    "ExprType",
    "KindType",
    "LOGICAL_FUNCTIONS",
    "ORDERING_FUNCTIONS",
    "check_cel_expression",
    "condition_registry_fingerprint",
    "scope_condition_registry",
    "synthetic_category_concept",
    "with_standard_synthetic_bindings",
    "with_synthetic_concepts",
]
