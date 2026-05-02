"""Typed literal identity objects for ASPIC bridge internment.

References:
    Modgil & Prakken 2018, Def. 1 (p.8): the logical language L contains
    formulas and their contradictories; identity should therefore be defined
    over formula structure rather than serialized UI strings.
    Diller, Borg, Bex 2025, Def. 7 (p.3): a ground atom is a predicate symbol
    applied to a tuple of ground terms. That tuple is part of the atom's
    identity, so the bridge models it directly in the key type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from argumentation.aspic import GroundAtom, Scalar
from propstore.core.id_types import ClaimId, ContextId, to_claim_id, to_context_id


REPOSITORY_ROOT_CONTEXT_ID = to_context_id("propstore:context:root")


@dataclass(frozen=True)
class ClaimLiteralKey:
    """Identity key for a claim-backed propositional literal."""

    claim_id: str


@dataclass(frozen=True)
class IstLiteralKey:
    """Identity key for a context-scoped proposition literal."""

    context_id: ContextId
    proposition_id: ClaimId

    def __post_init__(self) -> None:
        object.__setattr__(self, "context_id", to_context_id(self.context_id))
        object.__setattr__(self, "proposition_id", to_claim_id(self.proposition_id))


@dataclass(frozen=True)
class GroundLiteralKey:
    """Identity key for a grounded predicate literal.

    The polarity bit is explicit because ASPIC literals are atoms or their
    negations, not a single atom object with out-of-band sign metadata
    [Modgil & Prakken 2018, Def. 1, p.8].
    """

    predicate: str
    arguments: tuple[Scalar, ...]
    negated: bool


LiteralKey: TypeAlias = ClaimLiteralKey | IstLiteralKey | GroundLiteralKey


def claim_key(
    claim_id: str,
    *,
    context_id: ContextId | str = REPOSITORY_ROOT_CONTEXT_ID,
) -> IstLiteralKey:
    """Return the canonical typed key for a situated claim literal."""

    return IstLiteralKey(
        context_id=to_context_id(context_id),
        proposition_id=to_claim_id(claim_id),
    )


def ground_key(atom: GroundAtom, negated: bool) -> GroundLiteralKey:
    """Return the canonical typed key for a grounded literal."""

    return GroundLiteralKey(
        predicate=atom.predicate,
        arguments=atom.arguments,
        negated=negated,
    )


__all__ = [
    "ClaimLiteralKey",
    "GroundLiteralKey",
    "IstLiteralKey",
    "LiteralKey",
    "REPOSITORY_ROOT_CONTEXT_ID",
    "claim_key",
    "ground_key",
]
