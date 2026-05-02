from __future__ import annotations

import pytest
from argumentation.aspic import GroundAtom

from propstore.aspic_bridge.translate import claims_to_literals
import propstore.core.literal_keys as literal_keys


def test_contextual_claim_projects_to_ist_literal_key_and_backend_atom() -> None:
    """McCarthy 1993 page image pngs/page-000 and Guha 1991 pngs/page-007:
    propositions hold through `ist(context, proposition)`, not as unqualified
    proposition atoms. Guha pngs/page-033 and page-034 show lifting is explicit
    DCR-T/DCR-P machinery, not metadata loss.
    """

    assert hasattr(literal_keys, "IstLiteralKey")
    ist_key_type = getattr(literal_keys, "IstLiteralKey")

    literals = claims_to_literals(
        [
            {
                "id": "claim_x",
                "context_id": "ctx_a",
                "source_assertion_ids": ["assertion_x"],
            }
        ]
    )

    key = ist_key_type(context_id="ctx_a", proposition_id="claim_x")
    assert key in literals
    assert literals[key].atom == GroundAtom("ist", ("ctx_a", "claim_x"))
    assert literals[key].negated is False


def test_contextual_claim_does_not_project_to_unqualified_claim_atom() -> None:
    """Same page-image anchors as above: context is part of the formal atom."""

    literals = claims_to_literals(
        [
            {
                "id": "claim_x",
                "context_id": "ctx_a",
                "source_assertion_ids": ["assertion_x"],
            }
        ]
    )

    assert all(literal.atom != GroundAtom("claim_x") for literal in literals.values())


def test_non_contextual_claim_requires_explicit_projection_policy() -> None:
    """Guha 1991 pngs/page-007: the first `ist` argument denotes a context."""

    with pytest.raises(ValueError, match="context"):
        claims_to_literals([{"id": "claim_without_context"}])
