"""Operational support-state history tests."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.explanation_types import EntrenchmentReason
from propstore.support_revision.operators import contract
from propstore.support_revision.state import AssumptionAtom, BeliefBase, RevisionEpisode, RevisionScope
from tests.revision_assertion_helpers import make_assertion_atom
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
    from propstore.support_revision.iterated import advance_epistemic_state, make_epistemic_state

    base, entrenchment, ids = _base_with_shared_support()
    state = make_epistemic_state(base, entrenchment)
    result = contract(base, (ids["legacy"],), entrenchment=entrenchment, max_candidates=8)
    next_entrenchment = EntrenchmentReport(
        ranked_atom_ids=tuple(
            atom_id for atom_id in entrenchment.ranked_atom_ids if atom_id in result.accepted_atom_ids
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
    from propstore.support_revision.iterated import advance_epistemic_state, epistemic_state_payload, make_epistemic_state

    base, entrenchment, ids = _base_with_shared_support()
    state = make_epistemic_state(base, entrenchment)
    result = contract(base, (ids["legacy"],), entrenchment=entrenchment, max_candidates=8)
    next_entrenchment = EntrenchmentReport(
        ranked_atom_ids=tuple(
            atom_id for atom_id in entrenchment.ranked_atom_ids if atom_id in result.accepted_atom_ids
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

    assert payload["schema_version"] == "propstore.epistemic_snapshot.v1"
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


def _history_sensitive_base() -> tuple[BeliefBase, EntrenchmentReport, EntrenchmentReport, dict[str, str]]:
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
            AssumptionAtom("assumption:left_path", {"assumption_id": "left_path"}),
            AssumptionAtom("assumption:right_path", {"assumption_id": "right_path"}),
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


def test_iterated_revise_is_history_sensitive_even_with_same_current_acceptance() -> None:
    from propstore.support_revision.iterated import iterated_revise, make_epistemic_state

    base, left_first, right_first, ids = _history_sensitive_base()
    state_left = replace(
        make_epistemic_state(base, left_first),
        history=(
            RevisionEpisode(operator="seed-left"),
        ),
    )
    state_right = replace(
        make_epistemic_state(base, right_first),
        history=(
            RevisionEpisode(operator="seed-right"),
        ),
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

    assert next_left.accepted_atom_ids != next_right.accepted_atom_ids
    assert ids["left_dependent"] in next_left.accepted_atom_ids
    assert ids["right_dependent"] not in next_left.accepted_atom_ids
    assert ids["right_dependent"] in next_right.accepted_atom_ids
    assert ids["left_dependent"] not in next_right.accepted_atom_ids


def test_iterated_revise_supports_operator_specific_ranking_updates() -> None:
    from propstore.support_revision.iterated import iterated_revise, make_epistemic_state

    base, entrenchment, _, ids = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)
    new_atom = make_assertion_atom("new")
    conflicts = {new_atom.atom_id: (ids["legacy"],)}

    _, restrained_state = iterated_revise(
        state,
        new_atom,
        max_candidates=8,
        conflicts=conflicts,
        operator="restrained",
    )
    _, lexicographic_state = iterated_revise(
        state,
        new_atom,
        max_candidates=8,
        conflicts=conflicts,
        operator="lexicographic",
    )

    assert restrained_state.ranked_atom_ids[0] != lexicographic_state.ranked_atom_ids[0]
    assert lexicographic_state.ranked_atom_ids[0] == new_atom.atom_id


def test_iterated_revise_linear_sequence_appends_history_and_uses_next_state() -> None:
    from propstore.support_revision.iterated import iterated_revise, make_epistemic_state

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

    from propstore.support_revision.iterated import iterated_revise, make_epistemic_state

    base, entrenchment, _, ids = _history_sensitive_base()
    new_atom = make_assertion_atom("new")
    merge_base = replace(
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
