"""Canonical parameterization exactness vocabulary."""

from __future__ import annotations

from enum import StrEnum


class Exactness(StrEnum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    CONDITIONAL = "conditional"


def coerce_exactness(value: object | None) -> Exactness | None:
    if value is None:
        return None
    return Exactness(str(value))
