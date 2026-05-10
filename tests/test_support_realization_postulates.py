from __future__ import annotations

from itertools import combinations

from tests.support_revision.formal_realization_helpers import contract_via_formal_decision
from tests.test_revision_operators import _base_with_shared_support


def test_support_incision_success_minimality_cascade_and_preservation() -> None:
    base, entrenchment, ids = _base_with_shared_support()

    result = contract_via_formal_decision(
        base,
        (ids["legacy"],),
        entrenchment=entrenchment,
        max_candidates=8,
    )

    assert result.incision_set == ("assumption:shared_weak",)
    assert ids["legacy"] in result.rejected_atom_ids
    assert ids["dependent"] in result.rejected_atom_ids
    assert ids["independent"] in result.accepted_atom_ids
    assert not _has_surviving_support(base.support_sets[ids["legacy"]], result.incision_set)
    assert _is_minimal_hitting_set(base.support_sets[ids["legacy"]], result.incision_set)


def test_support_realization_explains_why_each_cut_was_selected() -> None:
    base, entrenchment, ids = _base_with_shared_support()

    result = contract_via_formal_decision(
        base,
        (ids["legacy"],),
        entrenchment=entrenchment,
        max_candidates=8,
    )

    detail = result.explanation["assumption:shared_weak"]
    assert detail.reason == "incised"
    assert detail.selection_rule == "minimal_support_incision"


def test_support_realization_does_not_promise_af_dung_recovery() -> None:
    base, entrenchment, ids = _base_with_shared_support()

    contracted = contract_via_formal_decision(
        base,
        (ids["legacy"],),
        entrenchment=entrenchment,
        max_candidates=8,
    )

    assert tuple(atom.atom_id for atom in contracted.revised_base.atoms) != tuple(atom.atom_id for atom in base.atoms)
    assert ids["dependent"] not in contracted.accepted_atom_ids


def _has_surviving_support(
    support_sets: tuple[tuple[str, ...], ...],
    incision_set: tuple[str, ...],
) -> bool:
    incised = set(incision_set)
    return any(all(assumption_id not in incised for assumption_id in support_set) for support_set in support_sets)


def _is_minimal_hitting_set(
    support_sets: tuple[tuple[str, ...], ...],
    incision_set: tuple[str, ...],
) -> bool:
    incised = tuple(incision_set)
    for size in range(len(incised)):
        for subset in combinations(incised, size):
            if not _has_surviving_support(support_sets, tuple(subset)):
                return False
    return True
