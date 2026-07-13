"""The claim as the relation heuristics read it.

A :class:`RelatableClaim` is a frozen field-subset VIEW over the canonical
:class:`~propstore.families.claims.Claim` charter — the counterpart of
:class:`~propstore.core.active_claims.ActiveClaim` for the heuristic layer. The
relation heuristics need three things about a claim: which claim it is, what it
says, and which concept it is about.

They used to receive that as ``dict[str, Any]`` with the keys ``"id"``,
``"text"``, and ``"concept_id"``, read back by subscript at ~25 call sites, and
the store protocol that supplied them was declared in dicts end to end. Nothing
untyped ever produced one: the claim is a charter document and the similarity
candidate is a :class:`~propstore.core.store_results.ClaimSimilarityHit`.
"""

from __future__ import annotations

import msgspec

from propstore.families.claims import Claim


class RelatableClaim(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """One claim, as the embedding/NLI relation heuristics see it."""

    claim_id: str
    text: str
    concept_id: str | None = None
    # The paper the claim came from. It is *not* a field of the ``Claim`` charter
    # — like ``ActiveClaim.source_paper``, it is stamped by whoever knows the
    # provenance, and its missing substrate is already an open gap. The prompt
    # says "unknown" when it is absent rather than inventing an attribution.
    source_paper: str | None = None

    @classmethod
    def from_claim(
        cls,
        claim: Claim,
        *,
        concept_id: str | None = None,
        source_paper: str | None = None,
    ) -> RelatableClaim:
        """Project the canonical charter into the heuristic view.

        Pure attribute access. ``text`` is the authored statement — what the
        classifier actually reads to the model. A claim with no statement says
        nothing a relation could be drawn from, and an empty string is the honest
        representation of that rather than a fabricated summary.
        """

        return cls(
            claim_id=str(claim.claim_id),
            text=claim.statement or "",
            concept_id=concept_id,
            source_paper=source_paper,
        )


__all__ = ["RelatableClaim"]
