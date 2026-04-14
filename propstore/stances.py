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
    NONE = "none"


VALID_STANCE_TYPES = frozenset(stance_type.value for stance_type in StanceType)


def coerce_stance_type(value: object | None) -> StanceType | None:
    if value is None:
        return None
    if isinstance(value, StanceType):
        return value
    return StanceType(str(value))
