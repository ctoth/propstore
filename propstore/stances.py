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
_STANCE_TYPE_ALIASES = {
    "contradicts": StanceType.REBUTS,
}


def coerce_stance_type(value: object | None) -> StanceType | None:
    if value is None:
        return None
    if isinstance(value, StanceType):
        return value
    raw_value = str(value)
    alias = _STANCE_TYPE_ALIASES.get(raw_value)
    if alias is not None:
        return alias
    return StanceType(raw_value)
