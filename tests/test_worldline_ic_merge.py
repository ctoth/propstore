from __future__ import annotations

import pytest

from propstore.support_revision.dispatch import dispatch
from propstore.support_revision.history import JournalOperator
from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from propstore.support_revision.snapshot_types import belief_atom_to_canonical_dict
from propstore.support_revision.state import RevisionMergeRequiredFailure, RevisionScope
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


_POLICY = {
    "revision_policy_version": "revision.v1",
    "ranking_policy_version": "ranking.v1",
    "entrenchment_policy_version": "entrenchment.v1",
}


def test_iterated_revise_at_merge_point_raises_typed_merge_required_failure() -> None:
    base, entrenchment, _, _ = _history_sensitive_base()
    merge_state = make_epistemic_state(
        base=base.__class__(
            scope=RevisionScope(bindings={}, branch="topic", merge_parent_commits=("left", "right")),
            atoms=base.atoms,
            assumptions=base.assumptions,
            support_sets=base.support_sets,
            essential_support=base.essential_support,
        ),
        entrenchment=entrenchment,
    )

    with pytest.raises(RevisionMergeRequiredFailure) as exc_info:
        iterated_revise(
            merge_state,
            make_assertion_atom("merge_point_new"),
            max_candidates=8,
            conflicts={},
            operator="restrained",
        )

    assert exc_info.value.parent_commits == ("left", "right")
    assert exc_info.value.reason == "merge_required"


def test_dispatch_iterated_revise_at_merge_point_raises_typed_merge_required_failure() -> None:
    base, entrenchment, _, _ = _history_sensitive_base()
    merge_base = base.__class__(
        scope=RevisionScope(bindings={}, branch="topic", merge_parent_commits=("left", "right")),
        atoms=base.atoms,
        assumptions=base.assumptions,
        support_sets=base.support_sets,
        essential_support=base.essential_support,
    )
    state = make_epistemic_state(merge_base, entrenchment)
    atom = make_assertion_atom("dispatch_merge_point_new")

    with pytest.raises(RevisionMergeRequiredFailure) as exc_info:
        dispatch(
            JournalOperator.ITERATED_REVISE,
            state_in=state.to_canonical_dict(),
            operator_input={
                "formula": belief_atom_to_canonical_dict(atom),
                "targets": (),
                "revision_operator": "restrained",
                "max_candidates": 8,
            },
            policy=_POLICY,
        )

    assert exc_info.value.parent_commits == ("left", "right")


def test_ic_merge_requires_explicit_integrity_constraint() -> None:
    base, entrenchment, _, _ = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)

    with pytest.raises(RevisionMergeRequiredFailure) as exc_info:
        dispatch(
            JournalOperator.IC_MERGE,
            state_in=state.to_canonical_dict(),
            operator_input={
                "profile_atom_ids": [["atom:left"], ["atom:right"]],
                "max_candidates": 8,
            },
            policy=_POLICY,
        )

    assert exc_info.value.reason == "missing_integrity_constraint"


def test_ic_merge_dispatch_calls_formal_adapter_with_profile_and_constraint(monkeypatch) -> None:
    base, entrenchment, _, _ = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)
    calls = []

    def _fake_decide_ic_merge(*, profile_atom_ids, integrity_constraint, merge_operator, max_alphabet_size):
        calls.append((profile_atom_ids, integrity_constraint, merge_operator, max_alphabet_size))
        raise RevisionMergeRequiredFailure(
            reason="realization_not_implemented",
            parent_commits=(),
        )

    monkeypatch.setattr("propstore.support_revision.dispatch.decide_ic_merge_profile", _fake_decide_ic_merge)

    with pytest.raises(RevisionMergeRequiredFailure):
        dispatch(
            JournalOperator.IC_MERGE,
            state_in=state.to_canonical_dict(),
            operator_input={
                "profile_atom_ids": [["atom:left"], ["atom:right"]],
                "integrity_constraint": {"kind": "top"},
                "max_candidates": 8,
            },
            policy=_POLICY,
        )

    assert calls == [((("atom:left",), ("atom:right",)), {"kind": "top"}, "sigma", 8)]
