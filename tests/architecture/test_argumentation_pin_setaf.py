from __future__ import annotations

import pytest

from argumentation.setaf import (
    SETAF,
    complete_extensions,
    conflict_free,
    defends,
    stable_extensions,
)
from argumentation.setaf_io import parse_aspartix_setaf, write_aspartix_setaf


def test_argumentation_pin_exposes_setaf_collective_attack_semantics() -> None:
    framework = SETAF(
        arguments=frozenset({"a", "b", "c", "x"}),
        attacks=frozenset(
            {
                (frozenset({"a", "b"}), "c"),
                (frozenset({"x"}), "a"),
            }
        ),
    )

    assert conflict_free(framework, frozenset({"a", "c"}))
    assert not conflict_free(framework, frozenset({"a", "b", "c"}))
    assert defends(framework, frozenset({"x"}), "c")
    assert frozenset({"b", "c", "x"}) in stable_extensions(framework)
    assert all(extension in complete_extensions(framework) for extension in stable_extensions(framework))


def test_argumentation_pin_exposes_aspartix_setaf_io() -> None:
    text = """
    arg(a).
    arg(b).
    arg(c).
    att(r1,c).
    mem(r1,a).
    mem(r1,b).
    """
    framework = parse_aspartix_setaf(text)

    assert framework == SETAF(
        arguments=frozenset({"a", "b", "c"}),
        attacks=frozenset({(frozenset({"a", "b"}), "c")}),
    )
    assert parse_aspartix_setaf(write_aspartix_setaf(framework)) == framework


def test_argumentation_pin_rejects_empty_setaf_attack_tails() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        SETAF(arguments=frozenset({"a"}), attacks=frozenset({(frozenset(), "a")}))
