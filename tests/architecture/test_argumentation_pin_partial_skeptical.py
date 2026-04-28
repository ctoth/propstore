from __future__ import annotations

import pytest

from argumentation.partial_af import PartialArgumentationFramework
from argumentation.semantics import accepted_arguments


def test_argumentation_pin_partial_af_splits_skeptical_acceptance_modes() -> None:
    framework = PartialArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        attacks=frozenset({("a", "b")}),
        ignorance=frozenset({("b", "a")}),
        non_attacks=frozenset({("a", "a"), ("b", "b")}),
    )

    assert accepted_arguments(
        framework,
        semantics="grounded",
        mode="necessary_skeptical",
    ) == frozenset()
    assert accepted_arguments(
        framework,
        semantics="grounded",
        mode="possible_skeptical",
    ) == frozenset({"a"})
    with pytest.raises(ValueError, match="necessary_skeptical"):
        accepted_arguments(framework, semantics="grounded", mode="skeptical")
