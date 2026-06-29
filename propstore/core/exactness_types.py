"""Canonical parameterization exactness vocabulary.

A parameterization edge relates an output concept to its input concepts. Its
*exactness* records how faithful the relationship is: an ``EXACT`` algebraic
identity, an ``APPROXIMATE`` fit, or a ``CONDITIONAL`` relationship that only
holds under stated conditions. :func:`coerce_exactness` is a validating
deserialization narrower (the same shape as the family ``_coerce_kind`` helpers),
not a cross-package coercer.
"""

from __future__ import annotations

from enum import StrEnum


class Exactness(StrEnum):
    """How faithful a parameterization relationship is to its output."""

    EXACT = "exact"
    APPROXIMATE = "approximate"
    CONDITIONAL = "conditional"


def coerce_exactness(value: object | None) -> Exactness | None:
    """Narrow a stored value to :class:`Exactness`, or ``None`` when absent."""

    if value is None:
        return None
    return Exactness(str(value))
