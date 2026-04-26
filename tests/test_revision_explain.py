from __future__ import annotations

from propstore.support_revision.operators import contract
from tests.test_revision_operators import _base_with_shared_support


def test_build_revision_explanation_exposes_default_contract() -> None:
    from propstore.support_revision.explain import build_revision_explanation

    base, entrenchment, ids = _base_with_shared_support()
    result = contract(base, (ids["legacy"],), entrenchment=entrenchment)

    explanation = build_revision_explanation(result, entrenchment=entrenchment)

    assert explanation.accepted_atom_ids == result.accepted_atom_ids
    assert explanation.rejected_atom_ids == result.rejected_atom_ids
    assert explanation.incision_set == result.incision_set
    assert explanation.atoms["assumption:shared_weak"].reason == "incised"
    assert explanation.atoms[ids["legacy"]].reason == "support_lost"


def test_build_revision_explanation_includes_ranking_rationale_when_available() -> None:
    from propstore.support_revision.explain import build_revision_explanation

    base, entrenchment, ids = _base_with_shared_support()
    result = contract(base, (ids["legacy"],), entrenchment=entrenchment)

    explanation = build_revision_explanation(result, entrenchment=entrenchment)

    ranking = explanation.atoms["assumption:shared_weak"].ranking
    assert ranking is not None
    assert ranking.support_count == 1


def test_build_revision_explanation_marks_accepted_atoms_as_unchanged_when_not_rejected() -> None:
    from propstore.support_revision.explain import build_revision_explanation

    base, entrenchment, ids = _base_with_shared_support()
    result = contract(base, (ids["legacy"],), entrenchment=entrenchment)

    explanation = build_revision_explanation(result, entrenchment=entrenchment)

    assert explanation.atoms[ids["independent"]].status == "accepted"
    assert explanation.atoms[ids["independent"]].reason == "unchanged"
