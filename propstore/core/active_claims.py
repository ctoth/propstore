"""The active-claim value the ASPIC+ bridge consumes.

An :class:`ActiveClaim` is the bridge-facing view of a claim participating in an
argumentation pass: its identity, the context it is used in, whether it is a
necessary or ordinary premise, and the metadata the preference heuristic reads.
The bridge accepts either an :class:`ActiveClaim` or a plain mapping and
normalizes with :func:`coerce_active_claims` — there is no row-model DTO and no
``to_payload``/``from_payload`` pair; a mapping is lowered once, at the boundary.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, TypeAlias

_RESERVED_KEYS = frozenset(
    {
        "id",
        "claim_id",
        "context_id",
        "premise_kind",
        "concept_id",
        "canonical_name",
        "statement",
        "sample_size",
        "uncertainty",
        "confidence",
    }
)


@dataclass(frozen=True)
class ActiveClaim:
    """One claim as the ASPIC+ bridge sees it."""

    claim_id: str
    context_id: str | None = None
    premise_kind: str = "ordinary"
    concept_id: str | None = None
    canonical_name: str | None = None
    statement: str | None = None
    sample_size: float | None = None
    uncertainty: float | None = None
    confidence: float | None = None
    attributes: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def attribute_value(self, key: str) -> Any:
        """Return an extra attribute by name, or ``None``."""

        for attribute_key, value in self.attributes:
            if attribute_key == key:
                return value
        return None

    def metadata_mapping(self) -> dict[str, object]:
        """The metadata the preference heuristic reads (omitting absent values)."""

        mapping: dict[str, object] = {}
        if self.sample_size is not None:
            mapping["sample_size"] = self.sample_size
        if self.uncertainty is not None:
            mapping["uncertainty"] = self.uncertainty
        if self.confidence is not None:
            mapping["confidence"] = self.confidence
        return mapping


ActiveClaimInput: TypeAlias = ActiveClaim | Mapping[str, Any]


def _float_or_none(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) else None


def _active_claim_from_mapping(claim: Mapping[str, Any]) -> ActiveClaim:
    identity = claim.get("id")
    if identity is None:
        identity = claim.get("claim_id")
    if identity is None:
        raise ValueError("active claim mapping requires an 'id' or 'claim_id'")
    context_id = claim.get("context_id")
    concept_id = claim.get("concept_id")
    canonical_name = claim.get("canonical_name")
    statement = claim.get("statement")
    attributes = tuple(
        sorted(
            (str(key), value)
            for key, value in claim.items()
            if str(key) not in _RESERVED_KEYS
        )
    )
    return ActiveClaim(
        claim_id=str(identity),
        context_id=None if context_id is None else str(context_id),
        premise_kind=str(claim.get("premise_kind") or "ordinary"),
        concept_id=None if concept_id is None else str(concept_id),
        canonical_name=None if canonical_name is None else str(canonical_name),
        statement=None if statement is None else str(statement),
        sample_size=_float_or_none(claim.get("sample_size")),
        uncertainty=_float_or_none(claim.get("uncertainty")),
        confidence=_float_or_none(claim.get("confidence")),
        attributes=attributes,
    )


def coerce_active_claims(
    active_claims: Sequence[ActiveClaimInput],
) -> tuple[ActiveClaim, ...]:
    """Normalize a sequence of claims-or-mappings into ``ActiveClaim`` values."""

    return tuple(
        claim if isinstance(claim, ActiveClaim) else _active_claim_from_mapping(claim)
        for claim in active_claims
    )


__all__ = ["ActiveClaim", "ActiveClaimInput", "coerce_active_claims"]
