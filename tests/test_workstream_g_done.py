from __future__ import annotations

from pathlib import Path

from argumentation.af_revision import ExtensionRevisionState
from argumentation.dung import ArgumentationFramework

from propstore.belief_set.af_revision_adapter import (
    NoStableExtensionRevisionTarget,
    revise_by_stable_framework,
)
from tests.test_agm_postulate_audit import _cases


def test_workstream_g_done() -> None:
    """Behavioral closure sentinel for WS-G belief revision."""

    assert len(_cases()) >= 60
    postulate_ids = {case.postulate_id for case in _cases()}
    required_ids = {
        "K*2[Bottom()]",
        "K-8[Atom(name='p')]",
        "IC4",
        "Maj",
        "Arb",
        "EE5",
        "agm_af_no_stable_distinct_from_empty_stable",
    }
    assert required_ids <= postulate_ids

    assert not Path("propstore/belief_set/af_revision.py").exists()
    assert Path("tests/support_revision/revision_assertion_helpers.py").exists()
    assert not Path("tests/revision_assertion_helpers.py").exists()

    docs = {
        Path("docs/belief-set-revision.md"),
        Path("docs/ic-merge.md"),
        Path("docs/af-revision.md"),
    }
    for doc in docs:
        assert "## Not Implemented" in doc.read_text(encoding="utf-8")

    no_stable_target = ArgumentationFramework(
        arguments=frozenset({"a", "b", "c"}),
        defeats=frozenset({("a", "b"), ("b", "c"), ("c", "a")}),
    )
    try:
        revise_by_stable_framework(
            state=ExtensionRevisionState.from_extensions(frozenset(), (frozenset(),)),
            framework=no_stable_target,
        )
    except NoStableExtensionRevisionTarget as exc:
        assert exc.framework == no_stable_target
    else:
        raise AssertionError("no-stable AF revision target was not rejected")
