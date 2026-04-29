from __future__ import annotations

import pytest

from argumentation.af_revision import ExtensionRevisionState
from argumentation.dung import ArgumentationFramework, stable_extensions

from propstore.belief_set.af_revision_adapter import (
    NoStableExtensionRevisionTarget,
    revise_by_stable_framework,
)


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

    with pytest.raises(NoStableExtensionRevisionTarget):
        revise_by_stable_framework(state, no_stable)

    result = revise_by_stable_framework(state, empty_stable)
    assert result.extensions == (frozenset(),)
