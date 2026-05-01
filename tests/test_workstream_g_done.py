from __future__ import annotations

from pathlib import Path

import pytest

from argumentation.af_revision import (
    ExtensionRevisionState,
    NoStableExtensionsError,
    diller_2015_revise_by_framework,
)
from argumentation.dung import ArgumentationFramework
from belief_set import Atom, BeliefSet, SpohnEpistemicState, revise


def test_workstream_g_done() -> None:
    """Behavioral closure sentinel for WS-G belief revision."""

    assert not Path("propstore/belief_set").exists()
    assert Path("tests/support_revision/revision_assertion_helpers.py").exists()
    assert not Path("tests/revision_assertion_helpers.py").exists()

    docs = {
        Path("docs/belief-set-revision.md"),
        Path("docs/ic-merge.md"),
        Path("docs/af-revision.md"),
    }
    for doc in docs:
        assert "## Not Implemented" in doc.read_text(encoding="utf-8")

    p = Atom("p")
    state = SpohnEpistemicState.from_belief_set(
        BeliefSet.tautology(frozenset({"p"})),
    )
    assert revise(state, p).belief_set.entails(p)

    no_stable_target = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c"}),
        defeats=frozenset({("a", "b"), ("b", "c"), ("c", "a")}),
    )
    with pytest.raises(NoStableExtensionsError) as exc_info:
        diller_2015_revise_by_framework(
            state=ExtensionRevisionState.from_extensions(frozenset(), (frozenset(),)),
            framework=no_stable_target,
            semantics="stable",
        )
    assert exc_info.value.framework == no_stable_target
