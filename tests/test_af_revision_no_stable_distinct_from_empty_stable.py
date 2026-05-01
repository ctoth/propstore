from __future__ import annotations

import pytest

from argumentation.af_revision import (
    ExtensionRevisionState,
    NoStableExtensionsError,
    diller_2015_revise_by_framework,
)
from argumentation.dung import ArgumentationFramework, stable_extensions


def test_af_revision_consumer_distinguishes_no_stable_from_empty_stable() -> None:
    """Class A - propstore must not consume no-stable as empty-stable."""

    no_stable = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c"}),
        defeats=frozenset({("a", "b"), ("b", "c"), ("c", "a")}),
    )
    empty_stable = ArgumentationFramework(arguments=frozenset(), defeats=frozenset())
    state = ExtensionRevisionState.from_extensions(
        frozenset(),
        (frozenset(),),
    )

    assert tuple(stable_extensions(no_stable)) == ()
    assert tuple(stable_extensions(empty_stable)) == (frozenset(),)

    with pytest.raises(NoStableExtensionsError):
        diller_2015_revise_by_framework(state, no_stable, semantics="stable")

    result = diller_2015_revise_by_framework(state, empty_stable, semantics="stable")
    assert result.extensions == (frozenset(),)
