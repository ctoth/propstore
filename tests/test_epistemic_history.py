"""Epistemic snapshot, journal, and semantic diff tests."""

from __future__ import annotations

import pytest
from dataclasses import replace

from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.families.claims.types import ClaimType
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.explanation_types import EntrenchmentReason
from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from propstore.support_revision.snapshot_types import belief_atom_to_canonical_dict
from propstore.support_revision.state import BeliefBase, EpistemicState
from tests.claim_model_helpers import make_claim
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


def test_semantic_diff_applies_assertion_warrant_ranking_provenance_and_dependency_deltas() -> (
    None
):
    from propstore.support_revision.history import (
        apply_epistemic_diff,
        diff_epistemic_snapshots,
        EpistemicSnapshot,
    )

    base, entrenchment, _, ids = _history_sensitive_base()
    source_state = make_epistemic_state(base, entrenchment)
    target_state = _changed_semantic_state(source_state, ids["legacy"])

    source = EpistemicSnapshot.from_state(source_state)
    target = EpistemicSnapshot.from_state(target_state)
    diff = diff_epistemic_snapshots(source, target)

    assert {
        "assertion_acceptance",
        "warrant",
        "ranking",
        "provenance",
        "dependency",
    }.issubset({delta.surface for delta in diff.deltas})
    assert apply_epistemic_diff(source, diff) == target


@pytest.mark.property
@given(source_accepts=st.booleans(), target_accepts=st.booleans())
@settings(max_examples=12)
def test_semantic_diff_apply_roundtrips_generated_tiny_assertion_languages(
    source_accepts: bool,
    target_accepts: bool,
) -> None:
    from propstore.support_revision.history import (
        apply_epistemic_diff,
        diff_epistemic_snapshots,
        EpistemicSnapshot,
    )

    atom = make_assertion_atom("generated")
    base = BeliefBase(scope=_history_sensitive_base()[0].scope, atoms=(atom,))
    entrenchment = EntrenchmentReport(ranked_atom_ids=(atom.atom_id,))
    accepted_source = (atom.atom_id,) if source_accepts else ()
    accepted_target = (atom.atom_id,) if target_accepts else ()
    source_state = replace(
        make_epistemic_state(base, entrenchment),
        accepted_atom_ids=accepted_source,
    )
    target_state = replace(source_state, accepted_atom_ids=accepted_target)
    source = EpistemicSnapshot.from_state(source_state)
    target = EpistemicSnapshot.from_state(target_state)

    assert (
        apply_epistemic_diff(source, diff_epistemic_snapshots(source, target)) == target
    )


def _changed_semantic_state(state: EpistemicState, legacy_id: str) -> EpistemicState:
    changed_atoms = []
    for atom in state.base.atoms:
        if atom.atom_id != legacy_id:
            changed_atoms.append(atom)
            continue
        source_claim = make_claim(
            claim_id="claim_legacy_updated",
            claim_type=ClaimType.PARAMETER,
            concept_id="concept_legacy",
            value=None,
            statement="legacy",
            source_slug="paper:updated",
            source_paper="paper:updated",
        )
        changed_atoms.append(
            replace(
                atom,
                source_claims=(source_claim,),
                source_claim_ids=(str(source_claim.id),),
            )
        )
    changed_base = replace(
        state.base,
        atoms=tuple(changed_atoms),
        support_sets={
            **dict(state.base.support_sets),
            legacy_id: (("assumption:left_path",),),
        },
        essential_support={
            **dict(state.base.essential_support),
            legacy_id: ("assumption:left_path",),
        },
    )
    accepted = tuple(
        atom_id for atom_id in state.accepted_atom_ids if atom_id != legacy_id
    )
    ranked = (legacy_id,) + tuple(
        atom_id for atom_id in state.ranked_atom_ids if atom_id != legacy_id
    )
    return replace(
        state,
        base=changed_base,
        accepted_atom_ids=accepted,
        ranked_atom_ids=ranked,
        ranking={atom_id: index for index, atom_id in enumerate(ranked)},
        entrenchment_reasons={
            **dict(state.entrenchment_reasons),
            legacy_id: EntrenchmentReason(support_count=1),
        },
    )
