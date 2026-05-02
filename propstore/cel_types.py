"""Typed carriers for authored CEL source."""

from __future__ import annotations

from collections.abc import Iterable
from typing import NewType


CelExpr = NewType("CelExpr", str)
CelRegistryFingerprint = NewType("CelRegistryFingerprint", str)


def to_cel_expr(value: object) -> CelExpr:
    """Brand raw authored text as CEL source."""
    if not isinstance(value, str):
        raise TypeError("CEL expression source must be a string")
    return CelExpr(value)


def to_cel_exprs(values: Iterable[object]) -> tuple[CelExpr, ...]:
    return tuple(to_cel_expr(value) for value in values)
