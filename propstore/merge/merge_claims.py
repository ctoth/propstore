"""The merge-facing view over the one canonical :class:`Claim`.

A :class:`MergeClaim` is a *field-subset view* over :class:`propstore.families.claims.Claim`
(CLAUDE.md substrate boundary: one canonical claim type, no second spelling), paired
with the per-branch provenance the merge math needs. The rewrite ``Claim`` is
provenance-free — identity is ``claim_id`` and there is no stored paper/page — so the
source paper, page, and the branch a version came from are carried *alongside* the
claim here, supplied as plain inputs to the merge boundary, never folded into claim
identity.

The propositional ``assertion_id`` is computed deterministically from the claim's
content (statement/value/concepts/…), its context, its CEL conditions, and its source
provenance. Two versions of the same proposition that agree on all of these collapse
to one merge argument; versions that disagree — including by source paper or by the
branch they were annotated with — get distinct assertion ids and stay rival.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from propstore.families.claims import Claim


@dataclass(frozen=True)
class MergeClaim:
    """One claim as the repository merge boundary sees it."""

    claim: Claim
    paper: str | None = None
    page: int | None = None
    branch_origin: str | None = None

    @classmethod
    def from_claim(
        cls,
        claim: Claim,
        *,
        paper: str | None = None,
        page: int | None = None,
        branch_origin: str | None = None,
    ) -> MergeClaim | None:
        """Wrap a stored claim, or ``None`` when it has no identity."""

        if not claim.claim_id:
            return None
        return cls(claim=claim, paper=paper, page=page, branch_origin=branch_origin)

    @property
    def artifact_id(self) -> str:
        """The claim's storage identity (``claim_id`` in the provenance-free charter)."""

        return self.claim.claim_id

    @property
    def claim_id(self) -> str:
        return self.claim.claim_id

    @property
    def claim_type(self) -> str | None:
        claim_type = self.claim.claim_type
        return None if claim_type is None else claim_type.value

    @property
    def value_concept_id(self) -> str:
        if self.claim.output_concept:
            return self.claim.output_concept
        if self.claim.target_concept:
            return self.claim.target_concept
        for concept_id in self.claim.concepts:
            if concept_id:
                return concept_id
        return ""

    @property
    def conditions(self) -> tuple[str, ...]:
        return tuple(self.claim.conditions)

    def provenance_mapping(self) -> dict[str, object]:
        """The source provenance carried for this version (no claim-identity fields)."""

        provenance: dict[str, object] = {}
        if self.paper is not None:
            provenance["paper"] = self.paper
        if self.page is not None:
            provenance["page"] = self.page
        if self.branch_origin is not None:
            provenance["branch_origin"] = self.branch_origin
        return provenance

    @property
    def assertion_id(self) -> str:
        """Stable propositional identity over content + context + conditions + source."""

        return f"ps:assertion:{_digest(self._assertion_key())}"

    def _assertion_key(self) -> dict[str, object]:
        return {
            "content": semantic_content(self.claim),
            "context_id": self.claim.context_id,
            "conditions": sorted(self.conditions),
            "provenance": {
                "paper": self.paper,
                "page": self.page,
                "branch_origin": self.branch_origin,
            },
        }

    def semantic_key(self) -> dict[str, object]:
        """Content used to decide whether two versions are the same proposition."""

        return {
            "content": semantic_content(self.claim),
            "context_id": self.claim.context_id,
            "conditions": sorted(self.conditions),
        }

    def candidate_key(self) -> dict[str, object]:
        """Content used to cluster cross-claim semantic candidates (ignores conditions)."""

        return {"content": semantic_content(self.claim), "context_id": self.claim.context_id}


def semantic_content(claim: Claim) -> dict[str, object]:
    """The propositional content of a claim, excluding identity and lifecycle."""

    return {
        "claim_type": None if claim.claim_type is None else claim.claim_type.value,
        "statement": claim.statement,
        "name": claim.name,
        "body": claim.body,
        "expression": claim.expression,
        "sympy": claim.sympy,
        "measure": claim.measure,
        "methodology": claim.methodology,
        "notes": claim.notes,
        "output_concept": claim.output_concept,
        "target_concept": claim.target_concept,
        "concepts": list(claim.concepts),
        "equations": list(claim.equations),
        "value": claim.value,
        "lower_bound": claim.lower_bound,
        "upper_bound": claim.upper_bound,
        "uncertainty": claim.uncertainty,
        "uncertainty_type": claim.uncertainty_type,
        "confidence": claim.confidence,
        "unit": claim.unit,
        "sample_size": claim.sample_size,
    }


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = ["MergeClaim", "semantic_content"]
