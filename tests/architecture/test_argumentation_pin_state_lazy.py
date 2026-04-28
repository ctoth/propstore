from __future__ import annotations

from argumentation.af_revision import ExtensionRevisionState


def test_argumentation_pin_revision_state_does_not_rank_full_powerset_at_construction() -> None:
    calls: list[frozenset[str]] = []

    def ranking(extension: frozenset[str]) -> int:
        calls.append(extension)
        return 0 if extension == frozenset({"a0"}) else 1

    state = ExtensionRevisionState.from_extensions(
        frozenset(f"a{i}" for i in range(20)),
        (frozenset({"a0"}),),
        ranking=ranking,
    )

    assert calls == []
    assert state.minimal_extensions((frozenset({"a0"}), frozenset({"a1"}))) == (
        frozenset({"a0"}),
    )
    assert set(calls) == {frozenset({"a0"}), frozenset({"a1"})}
