"""Auto-generate human-readable descriptions for claims.

Produces a one-line summary for parameter, equation, measurement, model, and
algorithm claims that lack an explicit ``statement``. A claim that already
carries a ``statement`` is returned unchanged. This is the charter-typed port of
the reference dict-shaped generator: it reads the one canonical
:class:`~propstore.families.claims.Claim` and a ``concept_id -> Concept`` registry,
not a YAML dict.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept

_EQUALITY_RE = re.compile(r"""^(\w+)\s*==\s*(['"])(.+?)\2$""")


def generate_description(
    claim: Claim, concept_registry: Mapping[str, Concept]
) -> str | None:
    """Return a human-readable description for ``claim``, or ``None``.

    An explicit ``statement`` is preserved verbatim. Otherwise the claim type
    selects a formatter; an unrecognized type yields ``None`` (honest: no
    description is fabricated for a shape this generator does not model).
    """

    if claim.statement:
        return claim.statement

    claim_type = claim.claim_type
    if claim_type is ClaimType.PARAMETER:
        return _describe_parameter(claim, concept_registry)
    if claim_type is ClaimType.EQUATION:
        return claim.expression or ""
    if claim_type is ClaimType.OBSERVATION:
        return claim.statement
    if claim_type is ClaimType.MEASUREMENT:
        return _describe_measurement(claim, concept_registry)
    if claim_type is ClaimType.MODEL:
        return f"Model: {claim.name or 'unnamed'}"
    if claim_type is ClaimType.ALGORITHM:
        return _describe_algorithm(claim)
    return None


def _resolve_concept_name(
    concept_id: str | None, concept_registry: Mapping[str, Concept]
) -> str:
    if not concept_id:
        return "unknown"
    concept = concept_registry.get(concept_id)
    return concept_id if concept is None else concept.canonical_name


def _format_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return str(value)


def _describe_parameter(
    claim: Claim, concept_registry: Mapping[str, Concept]
) -> str:
    name = _resolve_concept_name(claim.output_concept, concept_registry)
    if (
        claim.value is not None
        and claim.uncertainty is not None
        and claim.uncertainty_type
    ):
        body = (
            f"{name} = {_format_number(claim.value)} ± "
            f"{_format_number(claim.uncertainty)} ({claim.uncertainty_type})"
        )
    elif claim.value is not None:
        body = f"{name} = {_format_number(claim.value)}"
    elif claim.lower_bound is not None and claim.upper_bound is not None:
        body = (
            f"{name} ∈ [{_format_number(claim.lower_bound)}, "
            f"{_format_number(claim.upper_bound)}]"
        )
    else:
        body = name
    return _with_unit_and_conditions(claim, body)


def _describe_measurement(
    claim: Claim, concept_registry: Mapping[str, Concept]
) -> str:
    target = _resolve_concept_name(claim.target_concept, concept_registry)
    measure = claim.measure or "measure"
    if claim.value is not None:
        body = f"{measure} of {target} = {_format_number(claim.value)}"
    elif claim.lower_bound is not None and claim.upper_bound is not None:
        body = (
            f"{measure} of {target} ∈ [{_format_number(claim.lower_bound)}, "
            f"{_format_number(claim.upper_bound)}]"
        )
    else:
        body = f"{measure} of {target}"
    return _with_unit_and_conditions(claim, body)


def _describe_algorithm(claim: Claim) -> str:
    name = claim.name or "unnamed"
    if claim.output_concept:
        return f"Algorithm: {name} -> {claim.output_concept}"
    return f"Algorithm: {name}"


def _with_unit_and_conditions(claim: Claim, body: str) -> str:
    if claim.unit:
        body = f"{body} {claim.unit}"
    if claim.conditions:
        summary = _format_conditions_prose(claim.conditions)
        if summary:
            body = f"{body} ({summary})"
    return body


def _format_conditions_prose(conditions: tuple[str, ...]) -> str:
    parts: list[str] = []
    for condition in conditions:
        match = _EQUALITY_RE.match(condition.strip())
        if match:
            parts.append(f"{match.group(3)} {match.group(1)}")
        else:
            parts.append(condition)
    return ", ".join(parts)
