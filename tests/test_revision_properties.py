from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.revision.operators import normalize_revision_input
from propstore.revision.state import BeliefAtom, BeliefBase, RevisionScope


_ident = st.text(
    alphabet=st.characters(min_codepoint=ord("a"), max_codepoint=ord("z")),
    min_size=1,
    max_size=12,
)


@given(namespace=_ident, value=_ident)
@settings(deadline=None)
def test_normalize_revision_input_resolves_existing_claim_atom_by_all_user_handles(
    namespace: str,
    value: str,
) -> None:
    artifact_id = "ps:claim:0123456789abcdef"
    logical_id = f"{namespace}:{value}"
    atom = BeliefAtom(
        atom_id=f"claim:{value}",
        kind="claim",
        payload={
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
