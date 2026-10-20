"""Operational support-state history tests."""

from __future__ import annotations

import ast
from msgspec.structs import replace
from pathlib import Path

import pytest

from msgspec.structs import replace as replace_struct

from propstore.core.environment import AssumptionRef
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.explanation_types import EntrenchmentReason
from propstore.support_revision.state import (
    AssumptionAtom,
    BeliefBase,
    RevisionEpisode,
    RevisionScope,
)
from tests.support_revision.formal_realization_helpers import (
    contract_via_formal_decision,
)
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_operators import _base_with_shared_support


def test_make_epistemic_state_captures_base_entrenchment_and_empty_history() -> None:
    from propstore.support_revision.iterated import make_epistemic_state

    base, entrenchment, _ = _base_with_shared_support()

    state = make_epistemic_state(base, entrenchment)

    assert state.scope == base.scope
    assert state.accepted_atom_ids == tuple(atom.atom_id for atom in base.atoms)
    assert state.ranked_atom_ids == entrenchment.ranked_atom_ids
    assert state.ranking["assumption:a_strong"] == 0
    assert state.history == ()


def test_advance_epistemic_state_uses_revision_result_as_next_state() -> None:
    from propstore.support_revision.iterated import (
        advance_epistemic_state,
        make_epistemic_state,
    )

    base, entrenchment, ids = _base_with_shared_support()
    state = make_epistemic_state(base, entrenchment)
    result = contract_via_formal_decision(
        base, (ids["legacy"],), entrenchment=entrenchment, max_candidates=8
    )
    next_entrenchment = EntrenchmentReport(
        ranked_atom_ids=tuple(
            atom_id
            for atom_id in entrenchment.ranked_atom_ids
            if atom_id in result.accepted_atom_ids
        ),
        reasons=dict(entrenchment.reasons),
    )

    next_state = advance_epistemic_state(
        state,
        result,
        next_entrenchment,
        operator="contract",
        target_atom_ids=(ids["legacy"],),
    )

    assert tuple(atom.atom_id for atom in next_state.base.atoms) == tuple(
        atom.atom_id for atom in result.revised_base.atoms
    )
    assert next_state.accepted_atom_ids == result.accepted_atom_ids
    assert next_state.ranked_atom_ids == next_entrenchment.ranked_atom_ids
    assert next_state.history[-1].operator == "contract"
    assert next_state.history[-1].target_atom_ids == (ids["legacy"],)
    assert next_state.history[-1].rejected_atom_ids == result.rejected_atom_ids


def test_epistemic_state_is_serializable_via_dataclass_payload() -> None:
    from propstore.support_revision.iterated import (
        advance_epistemic_state,
        epistemic_state_payload,
        make_epistemic_state,
    )

    base, entrenchment, ids = _base_with_shared_support()
    state = make_epistemic_state(base, entrenchment)
    result = contract_via_formal_decision(
        base, (ids["legacy"],), entrenchment=entrenchment, max_candidates=8
    )
    next_entrenchment = EntrenchmentReport(
        ranked_atom_ids=tuple(
            atom_id
            for atom_id in entrenchment.ranked_atom_ids
            if atom_id in result.accepted_atom_ids
        ),
        reasons=dict(entrenchment.reasons),
    )

    next_state = advance_epistemic_state(
        state,
        result,
        next_entrenchment,
        operator="contract",
        target_atom_ids=(ids["legacy"],),
    )
    payload = epistemic_state_payload(next_state)

    assert payload["schema_version"] == "propstore.epistemic_snapshot.v2"
    assert payload["state"]["accepted_atom_ids"] == list(result.accepted_atom_ids)
    assert payload["state"]["history"][0]["operator"] == "contract"
    assert payload["state"]["history"][0]["incision_set"] == list(result.incision_set)


def test_iterated_revision_module_does_not_import_ic_merge() -> None:
    path = Path("propstore/support_revision/iterated.py")
    assert path.exists()

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
    assert "propstore.storage.ic_merge" not in imports


def _history_sensitive_base() -> tuple[
    BeliefBase, EntrenchmentReport, EntrenchmentReport, dict[str, str]
]:
    legacy = make_assertion_atom("legacy")
    left_dependent = make_assertion_atom("left_dependent")
    right_dependent = make_assertion_atom("right_dependent")
    ids = {
        "legacy": legacy.atom_id,
        "left_dependent": left_dependent.atom_id,
        "right_dependent": right_dependent.atom_id,
    }
    base = BeliefBase(
        scope=RevisionScope(bindings={}),
        atoms=(
            AssumptionAtom(
                "assumption:left_path",
                AssumptionRef(
                    assumption_id="left_path", kind="test", source="test", cel="true"
                ),
            ),
            AssumptionAtom(
                "assumption:right_path",
                AssumptionRef(
                    assumption_id="right_path", kind="test", source="test", cel="true"
                ),
            ),
            legacy,
            left_dependent,
            right_dependent,
        ),
        support_sets={
            ids["legacy"]: (("assumption:left_path", "assumption:right_path"),),
            ids["left_dependent"]: (("assumption:left_path",),),
            ids["right_dependent"]: (("assumption:right_path",),),
        },
        essential_support={
            ids["legacy"]: ("assumption:left_path", "assumption:right_path"),
            ids["left_dependent"]: ("assumption:left_path",),
            ids["right_dependent"]: ("assumption:right_path",),
        },
    )
    left_first = EntrenchmentReport(
        ranked_atom_ids=(
            ids["left_dependent"],
            "assumption:left_path",
            ids["right_dependent"],
            "assumption:right_path",
            ids["legacy"],
        ),
        reasons={
            "assumption:left_path": EntrenchmentReason(support_count=2),
            "assumption:right_path": EntrenchmentReason(support_count=2),
        },
    )
    right_first = EntrenchmentReport(
        ranked_atom_ids=(
            ids["right_dependent"],
            "assumption:right_path",
            ids["left_dependent"],
            "assumption:left_path",
            ids["legacy"],
        ),
        reasons={
            "assumption:left_path": EntrenchmentReason(support_count=2),
            "assumption:right_path": EntrenchmentReason(support_count=2),
        },
    )
    return base, left_first, right_first, ids


def test_iterated_revise_recomputes_entrenchment_independent_of_stale_history_ranking() -> (
    None
):
    from propstore.support_revision.iterated import (
        iterated_revise,
        make_epistemic_state,
    )

    base, left_first, right_first, ids = _history_sensitive_base()
    state_left = replace(
        make_epistemic_state(base, left_first),
        history=(RevisionEpisode(operator="seed-left"),),
    )
    state_right = replace(
        make_epistemic_state(base, right_first),
        history=(RevisionEpisode(operator="seed-right"),),
    )
    new_atom = make_assertion_atom("new")
    conflicts = {new_atom.atom_id: (ids["legacy"],)}

    _, next_left = iterated_revise(
        state_left,
        new_atom,
        max_candidates=8,
        conflicts=conflicts,
        operator="restrained",
    )
    _, next_right = iterated_revise(
        state_right,
        new_atom,
        max_candidates=8,
        conflicts=conflicts,
        operator="restrained",
    )

    assert next_left.accepted_atom_ids == next_right.accepted_atom_ids
    assert ids["left_dependent"] in next_left.accepted_atom_ids
    assert ids["left_dependent"] in next_right.accepted_atom_ids
    assert ids["right_dependent"] not in next_left.accepted_atom_ids
    assert ids["right_dependent"] not in next_right.accepted_atom_ids
    assert next_left.history[0].operator == "seed-left"
    assert next_right.history[0].operator == "seed-right"


def test_iterated_revise_reports_formal_operator_policy() -> None:
    from propstore.support_revision.iterated import (
        iterated_revise,
        make_epistemic_state,
    )

    base, entrenchment, _, ids = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)
    new_atom = make_assertion_atom("new")
    conflicts = {new_atom.atom_id: (ids["legacy"],)}

    restrained_result, restrained_state = iterated_revise(
        state,
        new_atom,
        max_candidates=8,
        conflicts=conflicts,
        operator="restrained",
    )
    lexicographic_result, lexicographic_state = iterated_revise(
        state,
        new_atom,
        max_candidates=8,
        conflicts=conflicts,
        operator="lexicographic",
    )

    restrained_episode = restrained_state.history[-1]
    lexicographic_episode = lexicographic_state.history[-1]

    assert restrained_episode.operator == "restrained"
    assert lexicographic_episode.operator == "lexicographic"
    assert (
        restrained_episode.accepted_atom_ids == lexicographic_episode.accepted_atom_ids
    )
    assert restrained_result.decision is not None
    assert lexicographic_result.decision is not None
    assert restrained_result.decision.policy == "belief_set.iterated.restrained"
    assert lexicographic_result.decision.policy == "belief_set.iterated.lexicographic"


def test_iterated_revise_linear_sequence_appends_history_and_uses_next_state() -> None:
    from propstore.support_revision.iterated import (
        iterated_revise,
        make_epistemic_state,
    )

    base, entrenchment, _, ids = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)
    new_a = make_assertion_atom("new_a")
    new_b = make_assertion_atom("new_b")

    _, next_state = iterated_revise(
        state,
        new_a,
        max_candidates=8,
        conflicts={new_a.atom_id: (ids["legacy"],)},
        operator="restrained",
    )
    _, final_state = iterated_revise(
        next_state,
        new_b,
        max_candidates=8,
        conflicts={new_b.atom_id: (new_a.atom_id,)},
        operator="restrained",
    )

    assert len(next_state.history) == 1
    assert len(final_state.history) == 2
    assert final_state.history[0].input_atom_id == new_a.atom_id
    assert final_state.history[1].input_atom_id == new_b.atom_id
    assert new_a.atom_id not in final_state.accepted_atom_ids
    assert new_b.atom_id in final_state.accepted_atom_ids


def test_iterated_revise_refuses_merge_point_states() -> None:
    import pytest

    from propstore.support_revision.iterated import (
        iterated_revise,
        make_epistemic_state,
    )

    base, entrenchment, _, ids = _history_sensitive_base()
    new_atom = make_assertion_atom("new")
    merge_base = replace_struct(
        base,
        scope=RevisionScope(
            bindings=base.scope.bindings,
            branch="topic",
            merge_parent_commits=("abc123", "def456"),
        ),
    )
    state = make_epistemic_state(merge_base, entrenchment)

    with pytest.raises(ValueError, match="merge point"):
        iterated_revise(
            state,
            new_atom,
            max_candidates=8,
            conflicts={new_atom.atom_id: (ids["legacy"],)},
            operator="restrained",
        )


@pytest.mark.parametrize("operator", ("lexicographic", "restrained"))
def test_iterated_revision_can_reaccept_an_earlier_rejected_atom(operator: str) -> None:
    from propstore.support_revision.entrenchment import compute_entrenchment
    from propstore.support_revision.iterated import iterated_revise, make_epistemic_state

    a, b, c, d = tuple(make_assertion_atom(name) for name in ("a", "b", "c", "d"))
    base = BeliefBase(scope=RevisionScope(bindings={}), atoms=(a, b))
    state = make_epistemic_state(base, compute_entrenchment(None, base))
    _, first = iterated_revise(
        state, c, conflicts={c.atom_id: (a.atom_id,)},
        operator=operator, max_candidates=8,
    )
    _, second = iterated_revise(
        first, d, conflicts={d.atom_id: (b.atom_id,)},
        operator=operator, max_candidates=8,
    )

    assert set(first.accepted_atom_ids) == {b.atom_id, c.atom_id}
    assert set(second.accepted_atom_ids) == {a.atom_id, c.atom_id, d.atom_id}
    assert next(atom for atom in second.base.atoms if atom.atom_id == a.atom_id) == a


@pytest.mark.parametrize("operator", ("lexicographic", "restrained"))
def test_snapshot_continuation_restores_original_support_records(operator: str) -> None:
    import json

    from propstore.support_revision.history import EpistemicSnapshot
    from propstore.support_revision.iterated import iterated_revise, make_epistemic_state

    base, entrenchment, _, ids = _history_sensitive_base()
    new, incoming = make_assertion_atom("new"), make_assertion_atom("next")
    state = make_epistemic_state(base, entrenchment)
    first_result, first = iterated_revise(
        state, new, conflicts={new.atom_id: (ids["legacy"],)},
        operator=operator, max_candidates=8,
    )
    assert first_result.incision_set == ("assumption:right_path",)
    assert ids["right_dependent"] not in first.accepted_atom_ids
    snapshot = EpistemicSnapshot.from_state(first)
    restored = EpistemicSnapshot.from_mapping(
        json.loads(snapshot.to_canonical_json())
    ).state
    result, second = iterated_revise(
        restored, incoming,
        conflicts={incoming.atom_id: (ids["left_dependent"],)},
        operator=operator, max_candidates=8,
    )

    assert set(second.accepted_atom_ids) == {
        "assumption:right_path", ids["right_dependent"], new.atom_id, incoming.atom_id,
    }
    assert result.incision_set == ("assumption:left_path",)
    assert second.base.support_sets[ids["right_dependent"]] == (
        ("assumption:right_path",),
    )
    assert next(
        atom for atom in second.base.atoms if atom.atom_id == ids["right_dependent"]
    ) == next(atom for atom in base.atoms if atom.atom_id == ids["right_dependent"])


@pytest.mark.parametrize("first_operator", ("lexicographic", "restrained"))
@pytest.mark.parametrize("second_operator", ("lexicographic", "restrained"))
@pytest.mark.parametrize("future_conflict", (False, True))
def test_continuation_preserves_every_world_rank(
    first_operator: str, second_operator: str, future_conflict: bool,
) -> None:
    import json

    from belief_set import (
        AlphabetBudgetExceeded, Atom, RevisionOutcome, conjunction,
        lexicographic_revise, negate,
        restrained_revise,
    )
    from propstore.support_revision.belief_set_adapter import (
        decide_iterated_revise, project_formal_bundle,
    )
    from propstore.support_revision.entrenchment import compute_entrenchment
    from propstore.support_revision.history import EpistemicSnapshot
    from propstore.support_revision.iterated import iterated_revise, make_epistemic_state

    a, b, c, d = tuple(make_assertion_atom(name) for name in ("a", "b", "c", "d"))
    base = BeliefBase(scope=RevisionScope(bindings={}), atoms=(a, b))
    state = make_epistemic_state(base, compute_entrenchment(None, base))
    operators = {"lexicographic": lexicographic_revise, "restrained": restrained_revise}
    seed = project_formal_bundle(base, extra_atoms=(c,)).epistemic_state
    assert seed is not None
    expected_first = operators[first_operator](seed, conjunction(
        Atom(b.atom_id), Atom(c.atom_id), negate(Atom(a.atom_id)),
    ))
    expected_second = operators[second_operator](expected_first.state, conjunction(
        Atom(c.atom_id), Atom(d.atom_id), negate(Atom(b.atom_id)),
    ))
    _, first = iterated_revise(
        state, c,
        conflicts={c.atom_id: (a.atom_id, d.atom_id) if future_conflict else (a.atom_id,)},
        operator=first_operator, max_candidates=8,
    )
    restored = EpistemicSnapshot.from_mapping(json.loads(
        EpistemicSnapshot.from_state(first).to_canonical_json()
    )).state
    decision = decide_iterated_revise(
        restored, d, conflicts=(b.atom_id,), operator=second_operator,
        max_alphabet_size=4,
    )

    assert isinstance(decision.outcome, RevisionOutcome)
    assert decision.outcome.state.alphabet == expected_second.state.alphabet
    assert decision.outcome.state.ranks == expected_second.state.ranks
    assert decision.report.ranking_provenance is not None
    assert decision.report.ranking_provenance.method == "hamming_seed_with_iterated_history"

    with pytest.raises(AlphabetBudgetExceeded):
        decide_iterated_revise(
            restored, d, conflicts=(b.atom_id,), operator=second_operator,
            max_alphabet_size=3,
        )

    # An ID rejected from the active base still resolves to its original record.
    result, _ = iterated_revise(
        restored, a.atom_id, operator=second_operator, max_candidates=8,
    )
    assert a.atom_id in result.accepted_atom_ids


@pytest.mark.parametrize("operator", ("lexicographic", "restrained"))
def test_transition_journal_roundtrip_keeps_formal_continuation(operator: str) -> None:
    from quire.documents import convert_document_value, to_document_builtins

    from propstore.support_revision.dispatch import dispatch
    from propstore.support_revision.entrenchment import compute_entrenchment
    from propstore.support_revision.history import (
        JournalOperator, TransitionJournal, TransitionJournalEntry, TransitionOperation,
    )
    from propstore.support_revision.iterated import make_epistemic_state
    from propstore.support_revision.operator_inputs import IteratedReviseInput

    a, b, c, d = tuple(make_assertion_atom(name) for name in ("a", "b", "c", "d"))
    base = BeliefBase(scope=RevisionScope(bindings={}), atoms=(a, b))
    state = make_epistemic_state(base, compute_entrenchment(None, base))
    policy = {
        "revision_policy_version": "revision.v1",
        "ranking_policy_version": "ranking.v1",
        "entrenchment_policy_version": "entrenchment.v1",
    }
    entries = []
    for incoming, target in ((c, a), (d, b)):
        operator_input = IteratedReviseInput(
            formula=incoming, targets=(target.atom_id,),
            revision_operator=operator, max_candidates=8,
        )
        next_state = dispatch(
            JournalOperator.ITERATED_REVISE,
            state_in=state.to_canonical_dict(), operator_input=operator_input,
            policy=policy,
        )
        entries.append(TransitionJournalEntry.from_states(
            state_in=state,
            operation=TransitionOperation(
                name="iterated_revise", input_atom_id=incoming.atom_id,
                target_atom_ids=(target.atom_id,),
            ),
            policy_id="revision.v1", operator=JournalOperator.ITERATED_REVISE,
            operator_input=operator_input, version_policy_snapshot=policy,
            state_out=next_state, explanation={},
        ))
        state = next_state
    journal = convert_document_value(
        to_document_builtins(TransitionJournal(entries=tuple(entries))),
        TransitionJournal, source="continuation journal roundtrip",
    )

    assert set(journal.entries[-1].state_out.state.accepted_atom_ids) == {
        a.atom_id, c.atom_id, d.atom_id,
    }
    assert journal.check_chain_integrity().ok
    assert journal.replay().ok
