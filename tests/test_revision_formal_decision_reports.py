from __future__ import annotations

from dataclasses import asdict

from belief_set import expand as formal_expand

from propstore.support_revision.belief_set_adapter import decide_expand, project_formal_bundle
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_operators import _base_with_shared_support


def test_expand_decision_report_matches_direct_belief_set_call() -> None:
    base, _, _ = _base_with_shared_support()
    new_atom = make_assertion_atom("new")
    bundle = project_formal_bundle(base, extra_atoms=(new_atom,))

    decision = decide_expand(base, new_atom, max_alphabet_size=16)
    direct = formal_expand(bundle.belief_set, bundle.formula_by_atom_id[new_atom.atom_id])

    direct_accepted = tuple(
        atom_id
        for atom_id, formula in bundle.formula_by_atom_id.items()
        if direct.entails(formula)
    )
    assert decision.report.operation == "expand"
    assert decision.report.policy == "belief_set.expand"
    assert decision.report.accepted_formula_ids == direct_accepted
    assert new_atom.atom_id in decision.report.input_formula_ids

    payload = asdict(decision.report)
    assert "incision_set" not in payload
    assert "accepted_atom_ids" not in payload
    assert "rejected_atom_ids" not in payload
