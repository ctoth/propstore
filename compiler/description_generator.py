"""Auto-generate human-readable descriptions for claims.

Produces a one-line summary for parameter, equation, measurement, and model
claims that lack an explicit ``statement`` field. Observation claims return
their existing statement unchanged.
"""

from __future__ import annotations

import re


def generate_description(claim: dict, concept_registry: dict) -> str | None:
    """Generate a human-readable description for a claim.

    Args:
        claim: A claim dict (as loaded from YAML).
        concept_registry: Mapping from concept ID to concept data dict.

    Returns:
        A description string, or None if the claim type is unrecognized.
    """
    # If the claim already has an explicit statement, preserve it
    statement = claim.get("statement")
    if statement:
        return statement

    ctype = claim.get("type")

    if ctype == "parameter":
        return _describe_parameter(claim, concept_registry)
    elif ctype == "equation":
        return _expression_as_description(claim)
    elif ctype == "observation":
        # Observation claims require statement — return it (or None)
        return claim.get("statement")
    elif ctype == "measurement":
        return _describe_measurement(claim, concept_registry)
    elif ctype == "model":
        name = claim.get("name", "unnamed")
        return f"Model: {name}"
    else:
        return None


def _resolve_concept_name(concept_id: str | None, concept_registry: dict) -> str:
    """Look up canonical_name for a concept ID; fall back to the ID itself."""
    if not concept_id:
        return "unknown"
    concept_data = concept_registry.get(concept_id)
    if concept_data:
        return concept_data.get("canonical_name", concept_id)
    return concept_id


def _format_number(n: float) -> str:
    """Format a number, dropping trailing zeros for clean display."""
    if isinstance(n, int) or (isinstance(n, float) and n == int(n)):
        return str(int(n))
    return str(n)


def _describe_parameter(claim: dict, concept_registry: dict) -> str:
    """Generate description for a parameter claim."""
    concept_id = claim.get("concept")
    name = _resolve_concept_name(concept_id, concept_registry)
    unit = claim.get("unit", "")

    value = claim.get("value")
    lower = claim.get("lower_bound")
    upper = claim.get("upper_bound")
    uncertainty = claim.get("uncertainty")
    uncertainty_type = claim.get("uncertainty_type")

    # Build the value part
    if value is not None and uncertainty is not None and uncertainty_type:
        val_str = f"{name} = {_format_number(value)} \u00b1 {_format_number(uncertainty)} ({uncertainty_type})"
    elif value is not None:
        val_str = f"{name} = {_format_number(value)}"
    elif lower is not None and upper is not None:
        val_str = f"{name} \u2208 [{_format_number(lower)}, {_format_number(upper)}]"
    else:
        val_str = name

    # Append unit
    if unit:
        val_str = f"{val_str} {unit}"

    # Append condition summary
    conditions = claim.get("conditions")
    if conditions:
        summary = _format_conditions_prose(conditions)
        if summary:
            val_str = f"{val_str} ({summary})"

    return val_str


def _expression_as_description(claim: dict) -> str:
    """Generate description for an equation claim."""
    expression = claim.get("expression", "")
    return expression


def _describe_measurement(claim: dict, concept_registry: dict) -> str:
    """Generate description for a measurement claim."""
    target_id = claim.get("target_concept")
    target_name = _resolve_concept_name(target_id, concept_registry)
    measure = claim.get("measure", "measure")
    unit = claim.get("unit", "")

    value = claim.get("value")
    lower = claim.get("lower_bound")
    upper = claim.get("upper_bound")

    if value is not None:
        val_str = f"{measure} of {target_name} = {_format_number(value)}"
    elif lower is not None and upper is not None:
        val_str = f"{measure} of {target_name} \u2208 [{_format_number(lower)}, {_format_number(upper)}]"
    else:
        val_str = f"{measure} of {target_name}"

    if unit:
        val_str = f"{val_str} {unit}"

    conditions = claim.get("conditions")
    if conditions:
        summary = _format_conditions_prose(conditions)
        if summary:
            val_str = f"{val_str} ({summary})"

    return val_str


# ── Condition summarization ───────────────────────────────────────────

# Patterns for common CEL equality conditions
_EQUALITY_RE = re.compile(r"""^(\w+)\s*==\s*(['"])(.+?)\2$""")

# Human-readable labels for known concept names in conditions
_CONDITION_LABELS = {
    "voice_quality_type": lambda v: f"{v} voice",
    "speaker_sex": lambda v: f"{v} speakers",
    "phonation_type": lambda v: f"{v} phonation",
    "vowel_height": lambda v: f"{v} vowels",
    "vowel_backness": lambda v: f"{v} vowels",
    "speaking_style": lambda v: f"{v} speech",
    "language": lambda v: v,
    "context": lambda v: v,
    "register": lambda v: f"{v} register",
    "task": lambda v: v,
}


def _format_conditions_prose(conditions: list[str]) -> str:
    """Convert CEL conditions to readable text.

    Simple equality conditions (``concept == 'value'``) are mapped to
    human-readable labels where the concept name is recognized. Complex
    conditions pass through as-is.

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
            labeler = _CONDITION_LABELS.get(concept_name)
            if labeler:
                parts.append(labeler(value))
            else:
                parts.append(f"{value} {concept_name}")
        else:
            parts.append(cond)
    return ", ".join(parts)
