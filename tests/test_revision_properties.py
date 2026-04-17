"""Generated properties for the operational support-incision surface."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.operators import expand, revise, stabilize_belief_base
from propstore.support_revision.operators import normalize_revision_input
from propstore.support_revision.state import AssumptionAtom, BeliefBase, ClaimAtom, RevisionScope


_ident = st.text(
    alphabet=st.characters(min_codepoint=ord("a"), max_codepoint=ord("z")),
    min_size=1,
    max_size=12,
)


@st.composite
def bounded_revision_bases(draw):
    """Generate small support-bearing belief bases for postulate checks."""
    assumption_count = draw(st.integers(min_value=1, max_value=4))
    claim_count = draw(st.integers(min_value=0, max_value=4))

    assumptions = tuple(
        AssumptionAtom(
            atom_id=f"assumption:a{i}",
            assumption={"assumption_id": f"a{i}"},
        )
        for i in range(assumption_count)
    )
    claims = tuple(
        ClaimAtom(
            atom_id=f"claim:c{i}",
            claim={"id": f"c{i}"},
        )
        for i in range(claim_count)
    )
    support_sets = {
        claim.atom_id: ((assumptions[index % assumption_count].atom_id,),)
        for index, claim in enumerate(claims)
    }
    base = BeliefBase(
        scope=RevisionScope(bindings={}),
        atoms=assumptions + claims,
        support_sets=support_sets,
        essential_support={
            atom_id: support[0]
            for atom_id, support in support_sets.items()
        },
    )
    entrenchment = EntrenchmentReport(
        ranked_atom_ids=tuple(atom.atom_id for atom in base.atoms),
        reasons={},
    )
    return base, entrenchment


@given(namespace=_ident, value=_ident)
@settings(deadline=None)
def test_normalize_revision_input_resolves_existing_claim_atom_by_all_user_handles(
    namespace: str,
    value: str,
) -> None:
    artifact_id = "ps:claim:0123456789abcdef"
    logical_id = f"{namespace}:{value}"
    atom = ClaimAtom(
        atom_id=f"claim:{value}",
        claim={
            "id": artifact_id,
            "logical_id": logical_id,
            "logical_ids": [{"namespace": namespace, "value": value}],
        },
    )
    base = BeliefBase(scope=RevisionScope(bindings={}), atoms=(atom,))

    assert normalize_revision_input(base, artifact_id) == atom
    assert normalize_revision_input(base, logical_id) == atom
    assert normalize_revision_input(base, value) == atom
    assert normalize_revision_input(base, f"claim:{value}") == atom


class TestGeneratedRevisionPostulates:
    """Generated checks for the finite support-incision adapter.

    Formal literature postulate tests live under the ``propstore.belief_set``
    test suites.
    """

    pytestmark = pytest.mark.property

    @given(bounded_revision_bases())
    @settings(deadline=None)
    def test_expand_success_and_inclusion_for_satisfiable_input(self, generated):
        """Expansion succeeds and includes all prior accepted atoms plus the input.

        This is the operational support-incision analogue of success and
        consistency for a satisfiable revision input.
        """
        base, _ = generated
        atom = ClaimAtom("claim:new", {"id": "new"})

        result = expand(base, atom)

        original_ids = {item.atom_id for item in base.atoms}
        revised_ids = {item.atom_id for item in result.revised_base.atoms}
        assert "claim:new" in result.accepted_atom_ids
        assert original_ids | {"claim:new"} <= revised_ids
        assert set(result.accepted_atom_ids).isdisjoint(result.rejected_atom_ids)

    @given(bounded_revision_bases())
    @settings(deadline=None)
    def test_revise_success_for_nonconflicting_satisfiable_input(self, generated):
        """Nonconflicting revision accepts the input and rejects nothing.

        On this exposed finite-base surface, a nonconflicting new atom is
        satisfiable and must be accepted.
        """
        base, entrenchment = generated

        result = revise(
            base,
            {"kind": "claim", "id": "new"},
            entrenchment=entrenchment,
            conflicts={},
        )

        assert "claim:new" in result.accepted_atom_ids
        assert result.rejected_atom_ids == ()
        assert set(result.accepted_atom_ids).isdisjoint(result.rejected_atom_ids)

    @given(bounded_revision_bases())
    @settings(deadline=None)
    def test_syntax_irrelevance_for_equivalent_claim_inputs(self, generated):
        """Equivalent claim inputs produce the same revised base.

        The mapping and domain object name the same claim atom.
        """
        base, entrenchment = generated
        mapping_input = {"kind": "claim", "id": "new"}
        atom_input = ClaimAtom("claim:new", {"id": "new"})

        from_mapping = revise(
            base,
            mapping_input,
            entrenchment=entrenchment,
            conflicts={},
        )
        from_atom = revise(
            base,
            atom_input,
            entrenchment=entrenchment,
            conflicts={},
        )

        assert from_mapping.accepted_atom_ids == from_atom.accepted_atom_ids
        assert tuple(atom.atom_id for atom in from_mapping.revised_base.atoms) == tuple(
            atom.atom_id for atom in from_atom.revised_base.atoms
        )

    @given(bounded_revision_bases())
    @settings(deadline=None)
    def test_stabilization_idempotence_for_generated_bases(self, generated):
        """Stabilizing a stable revised base is idempotent."""
        base, _ = generated
        incision_set = (base.atoms[0].atom_id,)

        once = stabilize_belief_base(base, incision_set=incision_set)
        twice = stabilize_belief_base(
            once.revised_base,
            incision_set=once.incision_set,
        )

        assert tuple(atom.atom_id for atom in once.revised_base.atoms) == tuple(
            atom.atom_id for atom in twice.revised_base.atoms
        )
        assert once.accepted_atom_ids == twice.accepted_atom_ids
        assert set(twice.accepted_atom_ids).isdisjoint(twice.rejected_atom_ids)
