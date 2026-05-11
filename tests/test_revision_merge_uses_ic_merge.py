from __future__ import annotations

from belief_set import Atom, TOP, merge_belief_profile

from propstore.support_revision.belief_set_adapter import decide_ic_merge


def test_ic_merge_adapter_delegates_to_belief_set_merge_kernel() -> None:
    alphabet = frozenset({"a", "b"})
    profile = (Atom("a"), Atom("b"))

    decision = decide_ic_merge(
        alphabet,
        profile,
        TOP,
        max_alphabet_size=16,
    )
    direct = merge_belief_profile(alphabet, profile, TOP, max_alphabet_size=16)

    assert decision.operation == "ic_merge"
    assert decision.report.operation == "ic_merge"
    assert decision.report.policy == "belief_set.ic_merge.merge_belief_profile.sigma"
    assert decision.outcome.belief_set.equivalent(direct.belief_set)
