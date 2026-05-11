from __future__ import annotations

from propstore.support_revision.belief_set_adapter import decide_ic_merge_profile


def test_ic_merge_decision_report_records_profile_multiset_and_integrity_constraint() -> None:
    decision = decide_ic_merge_profile(
        profile_atom_ids=(("atom:a",), ("atom:a",), ("atom:b",)),
        integrity_constraint={"kind": "atom", "atom_id": "atom:a"},
        merge_operator="sigma",
        max_alphabet_size=4,
    )

    trace = decision.report.trace
    assert trace["profile_atom_ids"] == [["atom:a"], ["atom:a"], ["atom:b"]]
    assert trace["integrity_constraint"] == {"kind": "atom", "atom_id": "atom:a"}


def test_ic_merge_decision_report_records_selected_worlds_hash() -> None:
    decision = decide_ic_merge_profile(
        profile_atom_ids=(("atom:a",), ("atom:b",)),
        integrity_constraint={"kind": "atom", "atom_id": "atom:a"},
        merge_operator="sigma",
        max_alphabet_size=4,
    )

    trace = decision.report.trace
    assert isinstance(trace["selected_worlds_hash"], str)
    assert len(trace["selected_worlds_hash"]) == 64
    assert isinstance(trace["scored_worlds_hash"], str)
    assert len(trace["scored_worlds_hash"]) == 64


def test_ic_merge_decision_report_records_formal_operator_family() -> None:
    decision = decide_ic_merge_profile(
        profile_atom_ids=(("atom:a",), ("atom:b",)),
        integrity_constraint={"kind": "top"},
        merge_operator="gmax",
        max_alphabet_size=4,
    )

    assert decision.report.operation == "ic_merge"
    assert decision.report.policy == "belief_set.ic_merge.merge_belief_profile.gmax"
    assert decision.report.trace["merge_operator"] == "gmax"


def test_ic_merge_decision_preserves_duplicate_profile_members() -> None:
    duplicate_decision = decide_ic_merge_profile(
        profile_atom_ids=(("atom:a",), ("atom:a",), ("atom:b",)),
        integrity_constraint={"kind": "top"},
        merge_operator="sigma",
        max_alphabet_size=4,
    )
    unique_decision = decide_ic_merge_profile(
        profile_atom_ids=(("atom:a",), ("atom:b",)),
        integrity_constraint={"kind": "top"},
        merge_operator="sigma",
        max_alphabet_size=4,
    )

    assert duplicate_decision.report.trace["profile_atom_ids"] == [["atom:a"], ["atom:a"], ["atom:b"]]
    assert duplicate_decision.report.trace["profile_hash"] != unique_decision.report.trace["profile_hash"]
