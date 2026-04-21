"""Shared stance-type vocabulary and helpers."""

from __future__ import annotations

from enum import StrEnum


class StanceType(StrEnum):
    REBUTS = "rebuts"
    UNDERCUTS = "undercuts"
    UNDERMINES = "undermines"
    SUPPORTS = "supports"
    EXPLAINS = "explains"
    SUPERSEDES = "supersedes"
    ABSTAIN = "abstain"
    NONE = "none"


VALID_STANCE_TYPES = frozenset(stance_type.value for stance_type in StanceType)


class UnknownStanceType(ValueError):
    def __init__(self, value: object) -> None:
        expected = ", ".join(sorted(VALID_STANCE_TYPES))
        super().__init__(f"Unknown stance_type {value!r}; expected one of: {expected}")


def coerce_stance_type(value: object | None) -> StanceType | None:
    if value is None:
        return None
    if isinstance(value, StanceType):
        return value
    try:
        return StanceType(str(value))
    except ValueError as exc:
        raise UnknownStanceType(value) from exc
