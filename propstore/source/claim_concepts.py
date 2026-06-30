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
