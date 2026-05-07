from __future__ import annotations

from propstore.support_revision.belief_set_adapter import project_formal_bundle
from tests.test_revision_operators import _base_with_shared_support


def test_formal_projection_bundle_maps_revision_base_bijectively() -> None:
    base, _, _ = _base_with_shared_support()

    bundle = project_formal_bundle(base)

    atom_ids = tuple(atom.atom_id for atom in base.atoms)
    assert bundle.alphabet == frozenset(atom_ids)
    assert set(bundle.formula_by_atom_id) == set(atom_ids)
    assert bundle.atom_id_by_formula_name == {atom_id: atom_id for atom_id in atom_ids}
    assert bundle.budget_config == {"max_alphabet_size": 16}
    assert bundle.epistemic_state is not None
    assert bundle.entrenchment is not None
    for atom_id, formula in bundle.formula_by_atom_id.items():
        assert bundle.belief_set.entails(formula), atom_id
