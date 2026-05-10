"""Example and contract tests for operational support-incision operators."""

from __future__ import annotations

import ast
from pathlib import Path

from propstore.core.labels import EnvironmentKey, Label
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.explanation_types import EntrenchmentReason
from propstore.support_revision.state import AssumptionAtom, BeliefBase, RevisionScope
from tests.support_revision.revision_assertion_helpers import make_assertion_atom


def _base_with_shared_support() -> tuple[BeliefBase, EntrenchmentReport, dict[str, str]]:
    legacy = make_assertion_atom("legacy")
    dependent = make_assertion_atom("dependent")
    independent = make_assertion_atom("independent")
    ids = {
        "legacy": legacy.atom_id,
        "dependent": dependent.atom_id,
        "independent": independent.atom_id,
    }
    base = BeliefBase(
        scope=RevisionScope(bindings={}),
        atoms=(
            AssumptionAtom("assumption:a_strong", {"assumption_id": "a_strong"}),
            AssumptionAtom("assumption:b_medium", {"assumption_id": "b_medium"}),
            AssumptionAtom("assumption:shared_weak", {"assumption_id": "shared_weak"}),
            legacy,
            dependent,
            independent,
        ),
        support_sets={
            ids["legacy"]: (
                ("assumption:a_strong", "assumption:shared_weak"),
                ("assumption:b_medium", "assumption:shared_weak"),
            ),
            ids["dependent"]: (("assumption:shared_weak",),),
            ids["independent"]: (("assumption:a_strong",),),
        },
        essential_support={
            ids["legacy"]: ("assumption:shared_weak",),
            ids["dependent"]: ("assumption:shared_weak",),
            ids["independent"]: ("assumption:a_strong",),
        },
    )
    entrenchment = EntrenchmentReport(
        ranked_atom_ids=(
            "assumption:a_strong",
            ids["independent"],
            "assumption:b_medium",
            ids["legacy"],
            ids["dependent"],
            "assumption:shared_weak",
        ),
        reasons={
            "assumption:a_strong": EntrenchmentReason(support_count=3),
            "assumption:b_medium": EntrenchmentReason(support_count=2),
            "assumption:shared_weak": EntrenchmentReason(support_count=1),
        },
    )
    return base, entrenchment, ids


def test_contract_uses_support_sensitive_incision_and_cascades_support_loss() -> None:
    from propstore.support_revision.belief_dynamics import contract_belief_base

    base, entrenchment, ids = _base_with_shared_support()

    result = contract_belief_base(base, (ids["legacy"],), entrenchment=entrenchment, max_candidates=8)

    assert result.incision_set == ("assumption:shared_weak",)
    assert "assumption:shared_weak" in result.rejected_atom_ids
    assert ids["legacy"] in result.rejected_atom_ids
    assert ids["dependent"] in result.rejected_atom_ids
    assert ids["independent"] in result.accepted_atom_ids
    assert result.explanation[ids["legacy"]].reason == "support_lost"
    assert result.explanation[ids["dependent"]].reason == "support_lost"
    assert result.explanation[ids["dependent"]].incision_set == ("assumption:shared_weak",)


def test_contract_uses_computed_entrenchment_order_for_equal_size_cuts() -> None:
    from propstore.support_revision.entrenchment import compute_entrenchment
    from propstore.support_revision.realization import _support_realization_cuts

    target = make_assertion_atom("equal_size_target")
    base = BeliefBase(
        scope=RevisionScope(bindings={}),
        atoms=(
            AssumptionAtom(
                "assumption:a_weak",
                {"assumption_id": "a_weak"},
                label=Label((EnvironmentKey(("a_weak",)),)),
            ),
            AssumptionAtom(
                "assumption:z_strong",
                {"assumption_id": "z_strong"},
                label=Label(
                    (
                        EnvironmentKey(("z_strong_primary",)),
                        EnvironmentKey(("z_strong_secondary",)),
                    )
                ),
            ),
            target,
        ),
        support_sets={
            target.atom_id: (("assumption:a_weak", "assumption:z_strong"),),
        },
    )

    entrenchment = compute_entrenchment(None, base)
    incision_set = _support_realization_cuts(
        base,
        (target.atom_id,),
        support_entrenchment=entrenchment,
        max_candidates=8,
    )

    assert entrenchment.ranked_atom_ids.index("assumption:z_strong") < entrenchment.ranked_atom_ids.index(
        "assumption:a_weak"
    )
    assert incision_set == ("assumption:a_weak",)


def test_expand_adds_atom_without_mutating_input_base() -> None:
    from propstore.support_revision.belief_dynamics import expand_belief_base

    base, _, _ = _base_with_shared_support()
    new_atom = make_assertion_atom("new")

    result = expand_belief_base(base, new_atom)

    assert new_atom.atom_id in result.accepted_atom_ids
    assert all(atom.atom_id != new_atom.atom_id for atom in base.atoms)
    assert any(atom.atom_id == new_atom.atom_id for atom in result.revised_base.atoms)


def test_revise_matches_operational_levi_identity() -> None:
    from propstore.support_revision.belief_dynamics import (
        contract_belief_base,
        expand_belief_base,
        revise_belief_base,
    )

    base, entrenchment, ids = _base_with_shared_support()
    new_atom = make_assertion_atom("new")
    conflicts = {new_atom.atom_id: (ids["legacy"],)}

    revised = revise_belief_base(
        base,
        new_atom,
        entrenchment=entrenchment,
        max_candidates=8,
        conflicts=conflicts,
    )
    contracted = contract_belief_base(
        base,
        conflicts[new_atom.atom_id],
        entrenchment=entrenchment,
        max_candidates=8,
    )
    expanded = expand_belief_base(contracted.revised_base, new_atom)

    assert revised.accepted_atom_ids == expanded.accepted_atom_ids
    assert tuple(atom.atom_id for atom in revised.revised_base.atoms) == tuple(
        atom.atom_id for atom in expanded.revised_base.atoms
    )
    assert revised.rejected_atom_ids == contracted.rejected_atom_ids
    assert revised.incision_set == contracted.incision_set


def test_normalize_revision_input_resolves_existing_assertion_ids() -> None:
    from propstore.support_revision.input_normalization import normalize_revision_input

    base, _, ids = _base_with_shared_support()

    atom = normalize_revision_input(base, ids["legacy"])

    assert atom.atom_id == ids["legacy"]


def test_normalize_revision_input_rejects_claim_mapping_adapters() -> None:
    from propstore.support_revision.input_normalization import normalize_revision_input

    base, _, _ = _base_with_shared_support()

    try:
        normalize_revision_input(base, {"kind": "claim", "id": "new", "value": 3.0})
    except ValueError as exc:
        assert "Assertion revision input requires an AssertionAtom" in str(exc)
    else:
        raise AssertionError("claim-shaped revision mappings must not be accepted")


def test_normalize_revision_input_builds_assumption_atoms() -> None:
    from propstore.support_revision.input_normalization import normalize_revision_input

    base, _, _ = _base_with_shared_support()

    atom = normalize_revision_input(
        base,
        {
            "kind": "assumption",
            "assumption_id": "queryable:extra",
            "cel": "x == 2",
        },
    )

    assert atom.atom_id == "assumption:queryable:extra"
    assert isinstance(atom, AssumptionAtom)
    assert atom.assumption.assumption_id == "queryable:extra"
    assert atom.assumption.cel == "x == 2"


def test_expand_rejects_synthetic_claim_mapping_adapter() -> None:
    from propstore.support_revision.belief_dynamics import expand_belief_base

    base, _, _ = _base_with_shared_support()

    try:
        expand_belief_base(base, {"kind": "claim", "id": "new_from_adapter", "value": 9.0})
    except ValueError as exc:
        assert "Assertion revision input requires an AssertionAtom" in str(exc)
    else:
        raise AssertionError("claim-shaped expand mappings must not be accepted")


def test_stabilize_belief_base_applies_support_loss_cascade_from_incision_set() -> None:
    from propstore.support_revision.realization import stabilize_belief_base

    base, _, ids = _base_with_shared_support()

    result = stabilize_belief_base(base, incision_set=("assumption:shared_weak",))

    assert "assumption:shared_weak" in result.rejected_atom_ids
    assert ids["legacy"] in result.rejected_atom_ids
    assert ids["dependent"] in result.rejected_atom_ids
    assert ids["independent"] in result.accepted_atom_ids
    assert result.explanation[ids["legacy"]].reason == "support_lost"


def test_stabilize_belief_base_is_idempotent_on_stable_result() -> None:
    from propstore.support_revision.realization import stabilize_belief_base

    base, _, _ = _base_with_shared_support()

    stabilized = stabilize_belief_base(base, incision_set=("assumption:shared_weak",))
    rerun = stabilize_belief_base(stabilized.revised_base, incision_set=stabilized.incision_set)

    assert tuple(atom.atom_id for atom in stabilized.revised_base.atoms) == tuple(
        atom.atom_id for atom in rerun.revised_base.atoms
    )
    assert rerun.accepted_atom_ids == stabilized.accepted_atom_ids


def test_contract_matches_explicit_stabilization_of_chosen_incision_set() -> None:
    from propstore.support_revision.belief_dynamics import contract_belief_base
    from propstore.support_revision.realization import stabilize_belief_base

    base, entrenchment, ids = _base_with_shared_support()

    contracted = contract_belief_base(base, (ids["legacy"],), entrenchment=entrenchment, max_candidates=8)
    stabilized = stabilize_belief_base(base, incision_set=contracted.incision_set)

    assert contracted.accepted_atom_ids == stabilized.accepted_atom_ids
    assert contracted.rejected_atom_ids == stabilized.rejected_atom_ids
    assert tuple(atom.atom_id for atom in contracted.revised_base.atoms) == tuple(
        atom.atom_id for atom in stabilized.revised_base.atoms
    )


def test_revision_operators_do_not_import_ic_merge() -> None:
    path = Path("propstore/support_revision/belief_dynamics.py")
    assert path.exists()

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
    assert "propstore.storage.ic_merge" not in imports
