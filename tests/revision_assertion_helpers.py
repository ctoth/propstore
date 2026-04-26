from __future__ import annotations

from propstore.core.active_claims import ActiveClaim
from propstore.core.labels import Label
from propstore.support_revision.projection import situated_assertion_from_active_claim
from propstore.support_revision.state import AssertionAtom


def make_assertion_atom(
    name: str,
    *,
    value: object | None = None,
    concept_id: str | None = None,
    source_paper: str | None = None,
    label: Label | None = None,
) -> AssertionAtom:
    claim = ActiveClaim.from_mapping(
        {
            "id": f"claim_{name}",
            "type": "parameter",
            "value": name if value is None else value,
            "concept_id": f"concept_{name}" if concept_id is None else concept_id,
            **({} if source_paper is None else {"source_paper": source_paper}),
        }
    )
    assertion = situated_assertion_from_active_claim(claim, context_id=None)
    return AssertionAtom(
        atom_id=str(assertion.assertion_id),
        assertion=assertion,
        source_claims=(claim,),
        label=label,
    )
