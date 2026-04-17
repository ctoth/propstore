"""Example and contract tests for support-incision revision operators.

Diller et al. 2015 revision-postulate grounding:
papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_003.png
papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_004.png
"""

from __future__ import annotations

import ast
from pathlib import Path

from propstore.revision.entrenchment import EntrenchmentReport
from propstore.revision.explanation_types import EntrenchmentReason
from propstore.revision.state import AssumptionAtom, BeliefBase, ClaimAtom, RevisionScope


def _base_with_shared_support() -> tuple[BeliefBase, EntrenchmentReport]:
    base = BeliefBase(
        scope=RevisionScope(bindings={}),
        atoms=(
            AssumptionAtom("assumption:a_strong", {"assumption_id": "a_strong"}),
            AssumptionAtom("assumption:b_medium", {"assumption_id": "b_medium"}),
            AssumptionAtom("assumption:shared_weak", {"assumption_id": "shared_weak"}),
            ClaimAtom("claim:legacy", {"id": "legacy"}),
            ClaimAtom("claim:dependent", {"id": "dependent"}),
            ClaimAtom("claim:independent", {"id": "independent"}),
        ),
        support_sets={
            "claim:legacy": (
                ("assumption:a_strong", "assumption:shared_weak"),
                ("assumption:b_medium", "assumption:shared_weak"),
            ),
            "claim:dependent": (("assumption:shared_weak",),),
            "claim:independent": (("assumption:a_strong",),),
        },
        essential_support={
            "claim:legacy": ("assumption:shared_weak",),
            "claim:dependent": ("assumption:shared_weak",),
            "claim:independent": ("assumption:a_strong",),
        },
    )
    entrenchment = EntrenchmentReport(
        ranked_atom_ids=(
            "assumption:a_strong",
            "claim:independent",
            "assumption:b_medium",
            "claim:legacy",
            "claim:dependent",
            "assumption:shared_weak",
        ),
        reasons={
            "assumption:a_strong": EntrenchmentReason(support_count=3),
            "assumption:b_medium": EntrenchmentReason(support_count=2),
            "assumption:shared_weak": EntrenchmentReason(support_count=1),
        },
    )
    return base, entrenchment


def test_contract_uses_support_sensitive_incision_and_cascades_support_loss() -> None:
    from propstore.revision.operators import contract

    base, entrenchment = _base_with_shared_support()

    result = contract(base, ("claim:legacy",), entrenchment=entrenchment)

    assert result.incision_set == ("assumption:shared_weak",)
    assert "assumption:shared_weak" in result.rejected_atom_ids
    assert "claim:legacy" in result.rejected_atom_ids
    assert "claim:dependent" in result.rejected_atom_ids
    assert "claim:independent" in result.accepted_atom_ids
    assert result.explanation["claim:legacy"].reason == "support_lost"
    assert result.explanation["claim:dependent"].reason == "support_lost"
    assert result.explanation["claim:dependent"].incision_set == ("assumption:shared_weak",)


def test_expand_adds_atom_without_mutating_input_base() -> None:
    from propstore.revision.operators import expand

    base, _ = _base_with_shared_support()
    new_atom = ClaimAtom("claim:new", {"id": "new"})

    result = expand(base, new_atom)

    assert "claim:new" in result.accepted_atom_ids
    assert all(atom.atom_id != "claim:new" for atom in base.atoms)
    assert any(atom.atom_id == "claim:new" for atom in result.revised_base.atoms)


def test_revise_matches_operational_levi_identity() -> None:
    from propstore.revision.operators import contract, expand, revise

    base, entrenchment = _base_with_shared_support()
    new_atom = ClaimAtom("claim:new", {"id": "new"})
    conflicts = {"claim:new": ("claim:legacy",)}

    revised = revise(
        base,
        new_atom,
        entrenchment=entrenchment,
        conflicts=conflicts,
    )
    contracted = contract(
        base,
        conflicts["claim:new"],
        entrenchment=entrenchment,
    )
    expanded = expand(contracted.revised_base, new_atom)

    assert revised.accepted_atom_ids == expanded.accepted_atom_ids
    assert tuple(atom.atom_id for atom in revised.revised_base.atoms) == tuple(
        atom.atom_id for atom in expanded.revised_base.atoms
    )
    assert revised.rejected_atom_ids == contracted.rejected_atom_ids
    assert revised.incision_set == contracted.incision_set


def test_normalize_revision_input_resolves_existing_claim_ids() -> None:
    from propstore.revision.operators import normalize_revision_input

    base, _ = _base_with_shared_support()

    atom = normalize_revision_input(base, "legacy")

    assert atom.atom_id == "claim:legacy"
    assert isinstance(atom, ClaimAtom)


def test_normalize_revision_input_builds_synthetic_claim_atoms() -> None:
    from propstore.revision.operators import normalize_revision_input

    base, _ = _base_with_shared_support()

    atom = normalize_revision_input(
        base,
        {
            "kind": "claim",
            "id": "new",
            "value": 3.0,
        },
    )

    assert atom.atom_id == "claim:new"
    assert isinstance(atom, ClaimAtom)
    assert atom.claim_id == "new"
    assert atom.claim.value == 3.0


def test_normalize_revision_input_builds_assumption_atoms() -> None:
    from propstore.revision.operators import normalize_revision_input

    base, _ = _base_with_shared_support()

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


def test_expand_accepts_synthetic_claim_mapping_via_adapter() -> None:
    from propstore.revision.operators import expand

    base, _ = _base_with_shared_support()

    result = expand(
        base,
        {
            "kind": "claim",
            "id": "new_from_adapter",
            "value": 9.0,
        },
    )

    assert "claim:new_from_adapter" in result.accepted_atom_ids
    assert any(atom.atom_id == "claim:new_from_adapter" for atom in result.revised_base.atoms)


def test_stabilize_belief_base_applies_support_loss_cascade_from_incision_set() -> None:
    from propstore.revision.operators import stabilize_belief_base

    base, _ = _base_with_shared_support()

    result = stabilize_belief_base(base, incision_set=("assumption:shared_weak",))

    assert "assumption:shared_weak" in result.rejected_atom_ids
    assert "claim:legacy" in result.rejected_atom_ids
    assert "claim:dependent" in result.rejected_atom_ids
    assert "claim:independent" in result.accepted_atom_ids
    assert result.explanation["claim:legacy"].reason == "support_lost"


def test_stabilize_belief_base_is_idempotent_on_stable_result() -> None:
    from propstore.revision.operators import stabilize_belief_base

    base, _ = _base_with_shared_support()

    stabilized = stabilize_belief_base(base, incision_set=("assumption:shared_weak",))
    rerun = stabilize_belief_base(stabilized.revised_base, incision_set=stabilized.incision_set)

    assert tuple(atom.atom_id for atom in stabilized.revised_base.atoms) == tuple(
        atom.atom_id for atom in rerun.revised_base.atoms
    )
    assert rerun.accepted_atom_ids == stabilized.accepted_atom_ids


def test_contract_matches_explicit_stabilization_of_chosen_incision_set() -> None:
    from propstore.revision.operators import contract, stabilize_belief_base

    base, entrenchment = _base_with_shared_support()

    contracted = contract(base, ("claim:legacy",), entrenchment=entrenchment)
    stabilized = stabilize_belief_base(base, incision_set=contracted.incision_set)

    assert contracted.accepted_atom_ids == stabilized.accepted_atom_ids
    assert contracted.rejected_atom_ids == stabilized.rejected_atom_ids
    assert tuple(atom.atom_id for atom in contracted.revised_base.atoms) == tuple(
        atom.atom_id for atom in stabilized.revised_base.atoms
    )


def test_revision_operators_do_not_import_ic_merge() -> None:
    path = Path("propstore/revision/operators.py")
    assert path.exists()

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
    assert "propstore.repo.ic_merge" not in imports
