from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.importing.equivalence import EquivalenceWitnessStore


def test_equivalence_witness_store_composes_without_identity_collapse() -> None:
    store = EquivalenceWitnessStore()
    left = store.record_witness(
        "urn:example:candidate:a",
        "urn:example:candidate:b",
        mapping_policy_id="urn:propstore:mapping-policy:test",
        evidence_statement_ids=("urn:example:statement:1",),
    )
    right = store.record_witness(
        "urn:example:candidate:b",
        "urn:example:candidate:c",
        mapping_policy_id="urn:propstore:mapping-policy:test",
        evidence_statement_ids=("urn:example:statement:2",),
    )

    composed = store.compose(left.witness_id, right.witness_id)

    assert composed is not None
    assert composed.candidate_ids == (
        "urn:example:candidate:a",
        "urn:example:candidate:c",
    )
    assert composed.status == "derived_unresolved"
    assert composed.source_witness_ids == (left.witness_id, right.witness_id)
    assert store.identity_for("urn:example:candidate:a") == "urn:example:candidate:a"
    assert store.identity_for("urn:example:candidate:b") == "urn:example:candidate:b"
    assert store.identity_for("urn:example:candidate:c") == "urn:example:candidate:c"


_uri_token = st.from_regex(r"[a-z][a-z0-9]{0,8}", fullmatch=True)


@settings(deadline=None)
@pytest.mark.property
@given(first=_uri_token, middle=_uri_token, last=_uri_token)
def test_equivalence_witness_composition_keeps_candidates_distinct(
    first: str,
    middle: str,
    last: str,
) -> None:
    store = EquivalenceWitnessStore()
    a = f"urn:example:candidate:{first}"
    b = f"urn:example:candidate:{middle}"
    c = f"urn:example:candidate:{last}"
    assume(len({a, b, c}) == 3)
    witness_ab = store.record_witness(
        a,
        b,
        mapping_policy_id="urn:propstore:mapping-policy:test",
        evidence_statement_ids=("urn:example:statement:1",),
    )
    witness_bc = store.record_witness(
        b,
        c,
        mapping_policy_id="urn:propstore:mapping-policy:test",
        evidence_statement_ids=("urn:example:statement:2",),
    )

    composed = store.compose(witness_ab.witness_id, witness_bc.witness_id)

    assert composed is not None
    assert set(composed.candidate_ids) == {a, c}
    assert store.identity_for(a) == a
    assert store.identity_for(b) == b
    assert store.identity_for(c) == c
