"""Canonical claim-type vocabulary for authored and runtime claim semantics."""

from __future__ import annotations

from enum import StrEnum


class ClaimType(StrEnum):
    PARAMETER = "parameter"
    EQUATION = "equation"
    OBSERVATION = "observation"
    MECHANISM = "mechanism"
    COMPARISON = "comparison"
    LIMITATION = "limitation"
    MODEL = "model"
    MEASUREMENT = "measurement"
    ALGORITHM = "algorithm"
    UNKNOWN = "unknown"


VALID_CLAIM_TYPES = frozenset(
    claim_type.value
    for claim_type in ClaimType
    if claim_type is not ClaimType.UNKNOWN
)


def coerce_claim_type(value: object | None) -> ClaimType | None:
    if value is None:
        return None
    return ClaimType(str(value))
