"""Shared stance-type vocabulary and relation categories.

A *stance* is the typed relation one claim takes toward another (it rebuts,
undercuts, supports, …). :class:`StanceType` is the ONE canonical spelling of
that vocabulary; the relation-category frozensets below classify those members
for argumentation-facing consumers. There is no parallel ``GraphRelationType``
enum — one spelling per thing (CLAUDE.md substrate-boundary rule).

Non-commitment (CLAUDE.md): these categories *classify* stances; they never gate
which stances reach storage. Every authored stance is stored and projected;
whether an ``EXPLAINS`` or ``SUPPORTS`` edge becomes an attack is a render-time
decision, read off :data:`NON_ATTACK_TYPES`, not a build-time filter.
"""

from __future__ import annotations

from enum import StrEnum


class StanceType(StrEnum):
    """The typed relation a claim takes toward another claim."""

    REBUTS = "rebuts"
    UNDERCUTS = "undercuts"
    UNDERMINES = "undermines"
    SUPPORTS = "supports"
    PROPER_DEFEATER = "proper_defeater"
    BLOCKING_DEFEATER = "blocking_defeater"
    EXPLAINS = "explains"
    SUPERSEDES = "supersedes"
    ABSTAIN = "abstain"
    NONE = "none"


VALID_STANCE_TYPES = frozenset(stance_type.value for stance_type in StanceType)


# --- Relation categories (classification only; never a render-time gate) ---

ATTACK_TYPES = frozenset(
    {
        StanceType.REBUTS,
        StanceType.UNDERCUTS,
        StanceType.UNDERMINES,
        StanceType.SUPERSEDES,
    }
)
UNCONDITIONAL_ATTACK_TYPES = frozenset(
    {
        StanceType.UNDERCUTS,
        StanceType.SUPERSEDES,
    }
)
PREFERENCE_SENSITIVE_ATTACK_TYPES = frozenset(
    {
        StanceType.REBUTS,
        StanceType.UNDERMINES,
    }
)
SUPPORT_TYPES = frozenset(
    {
        StanceType.SUPPORTS,
        StanceType.EXPLAINS,
    }
)
NON_ATTACK_TYPES = frozenset(
    {
        StanceType.SUPPORTS,
        StanceType.EXPLAINS,
        StanceType.NONE,
    }
)


class UnknownStanceType(ValueError):
    """Raised when a stored stance string is not a known :class:`StanceType`."""

    def __init__(self, value: object) -> None:
        expected = ", ".join(sorted(VALID_STANCE_TYPES))
        super().__init__(f"Unknown stance_type {value!r}; expected one of: {expected}")


def coerce_stance_type(value: object | None) -> StanceType | None:
    """Narrow a stored value to a :class:`StanceType`, validating membership.

    This is the validating narrowing of a sidecar/string value to the canonical
    enum (like the claim-type narrowing in the claim charter) — not a DTO
    coercer. ``None`` stays ``None``; an unknown string raises
    :class:`UnknownStanceType`.
    """

    if value is None:
        return None
    if isinstance(value, StanceType):
        return value
    try:
        return StanceType(str(value))
    except ValueError as exc:
        raise UnknownStanceType(value) from exc
