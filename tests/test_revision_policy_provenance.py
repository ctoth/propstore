from __future__ import annotations

from msgspec.structs import replace

from quire.documents import to_document_builtins

from propstore.provenance import ProvenanceStatus
from propstore.support_revision.decision_trace import RankingProvenance
from propstore.support_revision.integrity_constraints import (
    AtomConstraint,
    LiteralsConstraint,
    TopConstraint,
)
from propstore.support_revision.operator_inputs import (
    ContractInput,
    ExpandInput,
    ICMergeInput,
    IteratedReviseInput,
    ReviseInput,
)
from propstore.support_revision.dispatch import dispatch
from propstore.support_revision.history import (
    JournalOperator,
    TransitionJournal,
    TransitionJournalEntry,
    TransitionOperation,
)
from propstore.support_revision.iterated import make_epistemic_state
from tests.support_revision.formal_realization_helpers import revise_via_formal_decision
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_operators import _base_with_shared_support

_POLICY = {
    "revision_policy_version": "revision.v1",
    "ranking_policy_version": "ranking.v1",
    "entrenchment_policy_version": "entrenchment.v1",
}


def test_defaulted_spohn_ranking_is_visible_in_formal_decision_trace() -> None:
    base, entrenchment, ids = _base_with_shared_support()
    new_atom = make_assertion_atom("policy_trace_new")

    result = revise_via_formal_decision(
        base,
        new_atom,
        entrenchment=entrenchment,
        max_candidates=8,
        conflicts={new_atom.atom_id: (ids["legacy"],)},
    )

    assert result.decision is not None
    assert result.decision.ranking_provenance == RankingProvenance(
        status=ProvenanceStatus.DEFAULTED,
        method="hamming_distance",
        input_hash=result.decision.epistemic_state_hash or "",
    )


def test_dispatch_rejects_empty_policy_version_values() -> None:
    base, entrenchment, _ = _base_with_shared_support()
    state = make_epistemic_state(base, entrenchment)
    atom = make_assertion_atom("empty_policy_rejected")

    try:
        dispatch(
            JournalOperator.REVISE,
            state_in=state.to_canonical_dict(),
            operator_input=ReviseInput(formula=atom, max_candidates=8),
            policy={
                "revision_policy_version": "",
                "ranking_policy_version": "",
                "entrenchment_policy_version": "",
            },
        )
    except ValueError as exc:
        assert "policy versions" in str(exc)
    else:
        raise AssertionError("dispatch accepted empty policy versions")


def test_replay_rejects_policy_version_mismatch_before_semantic_replay() -> None:
    base, entrenchment, _ = _base_with_shared_support()
    state_in = make_epistemic_state(base, entrenchment)
    atom = make_assertion_atom("policy_mismatch")
    operator_input = ReviseInput(formula=atom, max_candidates=8)
    state_out = dispatch(
        JournalOperator.REVISE,
        state_in=state_in.to_canonical_dict(),
        operator_input=operator_input,
        policy=_POLICY,
    )
    entry = TransitionJournalEntry.from_states(
        state_in=state_in,
        operation=TransitionOperation(name="revise", input_atom_id=atom.atom_id),
        policy_id="revision.v1",
        operator=JournalOperator.REVISE,
        operator_input=operator_input,
        version_policy_snapshot=_POLICY,
        state_out=state_out,
        explanation={},
    )
    mismatched = replace(
        entry,
        version_policy_snapshot={
            "revision_policy_version": "revision.v1",
            "ranking_policy_version": "ranking.v2",
            "entrenchment_policy_version": "entrenchment.v1",
        },
        # Re-stamp so the drifted entry is internally consistent and replay()
        # must catch the policy mismatch, not the constructor.
        content_hash="",
    )

    report = TransitionJournal(entries=(mismatched,)).replay()

    assert report.ok is False
    assert report.errors
    assert "policy" in report.errors[0]
    assert not report.divergences


def test_ranking_provenance_carries_the_typed_status_not_a_string() -> None:
    """A defaulted ranking says so with the enum (CLAUDE.md honest-ignorance).

    The Hamming-distance fallback supplies a ranking when none was authored.
    That is a *fallback*, and ``ProvenanceStatus.DEFAULTED`` is how the system
    says so. It used to say it with the bare string ``"defaulted"`` buried in an
    untyped trace dict — a second spelling of the one provenance enum, in the one
    place the project is least willing to fabricate confidence.
    """
    from propstore.provenance import ProvenanceStatus
    from propstore.support_revision.decision_trace import RankingProvenance

    provenance = RankingProvenance(
        status=ProvenanceStatus.DEFAULTED,
        method="hamming_distance",
        input_hash="abc",
    )

    # ProvenanceStatus is a StrEnum, so `== "defaulted"` is true either way —
    # that is exactly why the string spelling went unnoticed. What matters is
    # that the value IS the enum member, so the type system can reason about it.
    assert provenance.status is ProvenanceStatus.DEFAULTED
    assert isinstance(provenance.status, ProvenanceStatus)
