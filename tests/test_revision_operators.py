from __future__ import annotations

import ast
from pathlib import Path

from propstore.revision.entrenchment import EntrenchmentReport
from propstore.revision.state import BeliefAtom, BeliefBase, RevisionScope


def _base_with_shared_support() -> tuple[BeliefBase, EntrenchmentReport]:
    base = BeliefBase(
        scope=RevisionScope(bindings={}),
        atoms=(
            BeliefAtom("assumption:a_strong", "assumption", {"assumption_id": "a_strong"}),
            BeliefAtom("assumption:b_medium", "assumption", {"assumption_id": "b_medium"}),
            BeliefAtom("assumption:shared_weak", "assumption", {"assumption_id": "shared_weak"}),
            BeliefAtom("claim:legacy", "claim", {"id": "legacy"}),
            BeliefAtom("claim:dependent", "claim", {"id": "dependent"}),
            BeliefAtom("claim:independent", "claim", {"id": "independent"}),
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
            "assumption:a_strong": {"support_count": 3},
            "assumption:b_medium": {"support_count": 2},
            "assumption:shared_weak": {"support_count": 1},
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
    assert result.explanation["claim:dependent"]["reason"] == "support_lost"
    assert result.explanation["claim:dependent"]["incision_set"] == ("assumption:shared_weak",)


def test_expand_adds_atom_without_mutating_input_base() -> None:
    from propstore.revision.operators import expand

    base, _ = _base_with_shared_support()
    new_atom = BeliefAtom("claim:new", "claim", {"id": "new"})

    result = expand(base, new_atom)

    assert "claim:new" in result.accepted_atom_ids
    assert all(atom.atom_id != "claim:new" for atom in base.atoms)
    assert any(atom.atom_id == "claim:new" for atom in result.revised_base.atoms)


def test_revise_matches_operational_levi_identity() -> None:
    from propstore.revision.operators import contract, expand, revise

    base, entrenchment = _base_with_shared_support()
    new_atom = BeliefAtom("claim:new", "claim", {"id": "new"})
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
