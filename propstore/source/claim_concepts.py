"""The claim side of source reference lowering: concept-handle rewriting.

A source claim references concepts by their source-local handle (a proposed
concept name). When the source branch is promoted those handles must be lowered
to canonical concept references. :func:`rewrite_claim_concept_refs` performs that
substitution over every concept-bearing field of a :class:`SourceClaimDocument`,
recording any handle it could not resolve. It is a pure function — the
import/promote normalizers that build canonical claim documents from the result
live with the promote subsystem (Phase 8-3 / 8-5).
"""

from __future__ import annotations

from collections.abc import Mapping

import msgspec

from propstore.families.claims import Claim, ClaimStatus, ClaimVariable
from propstore.families.sources import SourceClaimDocument

_CANONICAL_CONCEPT_PREFIXES = ("ps:concept:", "tag:")


def source_concept_ref_requires_mapping(value: str) -> bool:
    """Whether *value* is a source-local handle that must be lowered.

    A reference already in canonical form (``ps:concept:`` or a ``tag:`` URI) is
    left untouched; anything else is a source-local handle to resolve.
    """

    return not any(value.startswith(prefix) for prefix in _CANONICAL_CONCEPT_PREFIXES)


def rewrite_claim_concept_refs(
    claim: SourceClaimDocument,
    concept_map: Mapping[str, str],
    *,
    unresolved: set[str],
) -> SourceClaimDocument:
    """Return *claim* with every source-local concept handle lowered via *concept_map*.

    A handle absent from *concept_map* is left in place and recorded in
    *unresolved* (the non-committal discipline: never drop, surface the gap).
    """

    def resolve_optional(value: str | None) -> str | None:
        if value is None or not source_concept_ref_requires_mapping(value):
            return value
        mapped = concept_map.get(value)
        if mapped is None:
            unresolved.add(value)
            return value
        return mapped

    def resolve_required(value: str) -> str:
        resolved = resolve_optional(value)
        return value if resolved is None else resolved

    return msgspec.structs.replace(
        claim,
        concept=resolve_optional(claim.concept),
        target_concept=resolve_optional(claim.target_concept),
        concepts=tuple(resolve_required(value) for value in claim.concepts),
        variables=tuple(
            msgspec.structs.replace(variable, concept=resolve_required(variable.concept))
            for variable in claim.variables
        ),
        parameters=tuple(
            msgspec.structs.replace(
                parameter, concept=resolve_required(parameter.concept)
            )
            for parameter in claim.parameters
        ),
    )


def build_promoted_claim(
    claim: SourceClaimDocument,
    *,
    concept_map: Mapping[str, str],
    unresolved: set[str],
) -> Claim:
    """Rebuild a source claim as the immutable canonical :class:`Claim`.

    A promoted claim is a NEW immutable artifact — source-of-truth storage is
    immutable except by explicit migration — rebuilt from the source claim with
    every concept handle lowered to its canonical concept FK. The canonical
    ``claim_id`` is the source claim's already-derived ``artifact_id`` (the
    logical-handle identity stamped at authoring), so promotion does not mint a
    new identity. Any concept handle that could not be lowered is recorded in
    *unresolved* (never dropped); the caller quarantines such claims.

    Variable bindings are re-materialised onto the canonical claim as
    :class:`~propstore.families.claims.ClaimVariable` with their concept refs
    lowered — equation claims are meaningless to compare without their
    symbol→concept bindings. Parameter bindings are still lowered only for the
    resolvability check and not re-materialised (tracked in ``docs/gaps.md``).
    """

    artifact_id = claim.artifact_id
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError("promoted claim is missing artifact_id")
    lowered = rewrite_claim_concept_refs(claim, concept_map, unresolved=unresolved)
    return Claim(
        claim_id=artifact_id,
        context_id=lowered.context,
        claim_type=lowered.type,
        status=ClaimStatus.AUTHORED,
        statement=lowered.statement,
        name=lowered.name,
        body=lowered.body,
        expression=lowered.expression,
        sympy=lowered.sympy,
        measure=lowered.measure,
        methodology=lowered.methodology,
        notes=lowered.notes,
        output_concept=lowered.concept,
        target_concept=lowered.target_concept,
        concepts=lowered.concepts,
        variables=tuple(
            ClaimVariable(
                concept=variable.concept,
                symbol=variable.symbol,
                role=variable.role,
                name=variable.name,
            )
            for variable in lowered.variables
        ),
        equations=lowered.equations,
        conditions=lowered.conditions,
        value=lowered.value,
        lower_bound=lowered.lower_bound,
        upper_bound=lowered.upper_bound,
        uncertainty=lowered.uncertainty,
        uncertainty_type=lowered.uncertainty_type,
        unit=lowered.unit,
        sample_size=lowered.sample_size,
    )
