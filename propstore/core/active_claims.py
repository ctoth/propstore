"""The active-claim value the resolution and argumentation layers consume.

An :class:`ActiveClaim` is a frozen field-subset VIEW over the canonical
:class:`~propstore.families.claims.Claim` charter — built by attribute access
in :meth:`ActiveClaim.from_claim`, never by re-typing a payload mapping. It
adds the participation facts a claim only has *inside* one argumentation pass
(``premise_kind``, ``branch``, ``source_assertion_ids``) and the per-claim
epistemic slots (``date``, the Jøsang opinion components, ``source_paper``)
whose production substrates are tracked in ``docs/gaps.md``; absence is honest
ignorance, never a fabricated value.
"""

from __future__ import annotations

import msgspec
from doxa import Opinion

from propstore.families.claims import Claim, ClaimType, ClaimVariable

_DOGMATIC_TOL = 1e-12


def _value_concept_id(claim: Claim) -> str | None:
    """The concept a claim's value is about: output, else target, else first ref."""

    for candidate in (claim.output_concept, claim.target_concept, *claim.concepts):
        if candidate:
            return str(candidate)
    return None


class ActiveClaim(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, omit_defaults=True
):
    """One claim as the resolution and argumentation layers see it."""

    claim_id: str
    context_id: str | None = None
    premise_kind: str = "ordinary"
    concept_id: str | None = None
    canonical_name: str | None = None
    statement: str | None = None
    claim_type: ClaimType | None = None
    value: float | str | None = None
    body: str | None = None
    expression: str | None = None
    variables: tuple[ClaimVariable, ...] = ()
    conditions: tuple[str, ...] = ()
    sample_size: float | None = None
    uncertainty: float | None = None
    confidence: float | None = None
    branch: str | None = None
    source_assertion_ids: tuple[str, ...] = ()
    date: str | None = None
    opinion_belief: float | None = None
    opinion_disbelief: float | None = None
    opinion_uncertainty: float | None = None
    opinion_base_rate: float | None = None
    source_paper: str | None = None

    @classmethod
    def from_claim(
        cls,
        claim: Claim,
        *,
        claim_id: str | None = None,
        concept_id: str | None = None,
        branch: str | None = None,
        source_assertion_ids: tuple[str, ...] = (),
        premise_kind: str = "ordinary",
        source_paper: str | None = None,
    ) -> ActiveClaim:
        """Project the canonical :class:`Claim` charter into the active view.

        Pure attribute access. ``claim_id``/``concept_id`` overrides exist for
        the merge path, whose active identity is the branch-scoped artifact id
        rather than the document's own ``claim_id``.
        """

        return cls(
            claim_id=str(claim.claim_id) if claim_id is None else claim_id,
            context_id=claim.context_id,
            premise_kind=premise_kind,
            concept_id=_value_concept_id(claim) if concept_id is None else concept_id,
            canonical_name=claim.name,
            statement=claim.statement,
            claim_type=claim.claim_type,
            value=claim.value,
            body=claim.body,
            expression=claim.expression,
            variables=claim.variables,
            conditions=claim.conditions,
            sample_size=None if claim.sample_size is None else float(claim.sample_size),
            uncertainty=claim.uncertainty,
            confidence=claim.confidence,
            branch=branch,
            source_assertion_ids=source_assertion_ids,
            source_paper=source_paper,
        )

    def opinion(self) -> Opinion | None:
        """Rebuild the attached opinion as ``doxa.Opinion``, or ``None``.

        Returns ``None`` unless all four Jøsang components are present — a
        partial opinion is treated as no opinion, never completed with a
        fabricated mass (mirrors ``Stance.opinion``).
        """

        b = self.opinion_belief
        d = self.opinion_disbelief
        u = self.opinion_uncertainty
        a = self.opinion_base_rate
        if b is None or d is None or u is None or a is None:
            return None
        return Opinion(b, d, u, a, allow_dogmatic=u < _DOGMATIC_TOL)


__all__ = ["ActiveClaim"]
