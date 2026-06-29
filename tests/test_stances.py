"""The stance vocabulary is one canonical StrEnum with validated narrowing."""

from __future__ import annotations

import pytest

from propstore.stances import (
    ATTACK_TYPES,
    NON_ATTACK_TYPES,
    SUPPORT_TYPES,
    VALID_STANCE_TYPES,
    StanceType,
    UnknownStanceType,
    coerce_stance_type,
)


def test_valid_stance_types_covers_every_member() -> None:
    assert VALID_STANCE_TYPES == frozenset(member.value for member in StanceType)


def test_coerce_passes_through_enum_and_string() -> None:
    assert coerce_stance_type(StanceType.REBUTS) is StanceType.REBUTS
    assert coerce_stance_type("undercuts") is StanceType.UNDERCUTS


def test_coerce_none_is_none() -> None:
    assert coerce_stance_type(None) is None


def test_coerce_unknown_raises() -> None:
    with pytest.raises(UnknownStanceType, match="Unknown stance_type"):
        coerce_stance_type("not-a-stance")


def test_attack_and_non_attack_categories_are_disjoint() -> None:
    assert ATTACK_TYPES.isdisjoint(NON_ATTACK_TYPES)
    assert StanceType.SUPPORTS in NON_ATTACK_TYPES
    assert StanceType.SUPPORTS in SUPPORT_TYPES
    assert StanceType.REBUTS in ATTACK_TYPES
    assert StanceType.NONE in NON_ATTACK_TYPES
