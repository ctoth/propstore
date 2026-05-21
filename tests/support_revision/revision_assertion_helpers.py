from __future__ import annotations

from propstore.core.labels import Label
from propstore.support_revision.projection import situated_assertion_from_claim
from propstore.support_revision.state import AssertionAtom
from tests.claim_model_helpers import claim_model


def make_assertion_atom(
    name: str,
    *,
    value: object | None = None,
    concept_id: str | None = None,
    source_paper: str | None = None,
    label: Label | None = None,
) -> AssertionAtom:
    paper = "paper1" if source_paper is None else source_paper
    claim = claim_model(
        claim_id=f"claim_{name}",
        concept_id=f"concept_{name}" if concept_id is None else concept_id,
        value=float(value) if isinstance(value, int | float) else None,
        statement=None if value is None else str(value),
        source_slug=paper,
        source_paper=paper,
    )
    assertion = situated_assertion_from_claim(claim, context_id=None)
    return AssertionAtom(
        atom_id=str(assertion.assertion_id),
        assertion=assertion,
        source_claims=(claim,),
        label=label,
    )
