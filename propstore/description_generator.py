"""Auto-generate human-readable descriptions for claims.

Produces a one-line summary for parameter, equation, measurement, and model
claims that lack an explicit ``statement`` field. Observation claims return
their existing statement unchanged.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from propstore.families.claims.types import ClaimType
from propstore.families.claims.declaration import ClaimDocument


def generate_description(
    claim: ClaimDocument,
    *,
    resolve_concept_name: Callable[[str | None], str] | None = None,
) -> str | None:
    """Generate a human-readable description for a claim.

    Args:
        claim: A typed claim document.
        concept_registry: Mapping from concept ID to concept metadata.

    Returns:
        A description string, or None if the claim type is unrecognized.
    """
    # If the claim already has an explicit statement, preserve it
    if claim.statement:
        return claim.statement

    if claim.type is ClaimType.PARAMETER:
        return _describe_parameter(claim, resolve_concept_name)
    elif claim.type is ClaimType.EQUATION:
        return _expression_as_description(claim)
    elif claim.type is ClaimType.OBSERVATION:
        # Observation claims require statement — return it (or None)
        return claim.statement
    elif claim.type is ClaimType.MEASUREMENT:
        return _describe_measurement(claim, resolve_concept_name)
    elif claim.type is ClaimType.MODEL:
        name = claim.name or "unnamed"
        return f"Model: {name}"
    elif claim.type is ClaimType.ALGORITHM:
        return _describe_algorithm(claim)
    else:
        return None


def _resolve_concept_name(
    concept_id: str | None,
    resolve_concept_name: Callable[[str | None], str] | None,
) -> str:
    """Look up canonical_name for a concept ID; fall back to the ID itself."""
    if resolve_concept_name is not None:
        return resolve_concept_name(concept_id)
    if not concept_id:
        return "unknown"
    return concept_id


def _format_number(n: float | int) -> str:
    """Format a number, dropping trailing zeros for clean display."""
    if isinstance(n, int) or (isinstance(n, float) and n == int(n)):
        return str(int(n))
    return str(n)


def _describe_parameter(
    claim: ClaimDocument,
    resolve_concept_name: Callable[[str | None], str] | None,
) -> str:
    """Generate description for a parameter claim."""
    name = _resolve_concept_name(claim.output_concept, resolve_concept_name)
    unit = claim.unit or ""

    # Build the value part
    if (
        claim.value is not None
        and claim.uncertainty is not None
        and claim.uncertainty_type
    ):
        val_str = (
            f"{name} = {_format_number(claim.value)} \u00b1 "
            f"{_format_number(claim.uncertainty)} ({claim.uncertainty_type})"
        )
    elif claim.value is not None:
        val_str = f"{name} = {_format_number(claim.value)}"
    elif claim.lower_bound is not None and claim.upper_bound is not None:
        val_str = (
            f"{name} \u2208 "
            f"[{_format_number(claim.lower_bound)}, {_format_number(claim.upper_bound)}]"
        )
    else:
        val_str = name

    # Append unit
    if unit:
        val_str = f"{val_str} {unit}"

    # Append condition summary
    if claim.conditions:
        summary = _format_conditions_prose(
            tuple(str(condition) for condition in claim.conditions)
        )
        if summary:
            val_str = f"{val_str} ({summary})"

    return val_str


def _expression_as_description(claim: ClaimDocument) -> str:
    """Generate description for an equation claim."""
    return claim.expression or ""


def _describe_measurement(
    claim: ClaimDocument,
    resolve_concept_name: Callable[[str | None], str] | None,
) -> str:
    """Generate description for a measurement claim."""
    target_name = _resolve_concept_name(claim.target_concept, resolve_concept_name)
    measure = claim.measure or "measure"
    unit = claim.unit or ""

    if claim.value is not None:
        val_str = f"{measure} of {target_name} = {_format_number(claim.value)}"
    elif claim.lower_bound is not None and claim.upper_bound is not None:
        val_str = (
            f"{measure} of {target_name} \u2208 "
            f"[{_format_number(claim.lower_bound)}, {_format_number(claim.upper_bound)}]"
        )
    else:
        val_str = f"{measure} of {target_name}"

    if unit:
        val_str = f"{val_str} {unit}"

    if claim.conditions:
        summary = _format_conditions_prose(
            tuple(str(condition) for condition in claim.conditions)
        )
        if summary:
            val_str = f"{val_str} ({summary})"

    return val_str


def _describe_algorithm(claim: ClaimDocument) -> str:
    """Generate description for an algorithm claim."""
    name = claim.name or "unnamed"
    if claim.stage:
        if claim.output_concept:
            return f"Algorithm: {name} -> {claim.output_concept} [{claim.stage}]"
        return f"Algorithm: {name} [{claim.stage}]"
    if claim.output_concept:
        return f"Algorithm: {name} -> {claim.output_concept}"
    return f"Algorithm: {name}"


# ── Condition summarization ───────────────────────────────────────────

# Patterns for common CEL equality conditions
_EQUALITY_RE = re.compile(r"""^(\w+)\s*==\s*(['"])(.+?)\2$""")


def _format_conditions_prose(conditions: Sequence[str]) -> str:
    """Convert CEL conditions to readable text.

    Simple equality conditions (``concept == 'value'``) become
    ``"value concept_name"``; complex conditions pass through as-is.

    Args:
        conditions: List of CEL expression strings.

    Returns:
        A comma-separated summary string.
    """
    parts: list[str] = []
    for cond in conditions:
        m = _EQUALITY_RE.match(cond.strip())
        if m:
            concept_name, value = m.group(1), m.group(3)
            parts.append(f"{value} {concept_name}")
        else:
            parts.append(cond)
    return ", ".join(parts)
