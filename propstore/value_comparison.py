"""Pure numeric value comparison logic for claims."""

from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from propstore.families.forms.stages import FormDefinition

DEFAULT_TOLERANCE = 1e-9


def extract_interval(claim: object) -> tuple[float, float, float] | None:
    """Extract (center, lower, upper) from a claim's named value fields."""
    value = _claim_field(claim, "value")
    lower_bound = _claim_field(claim, "lower_bound")
    upper_bound = _claim_field(claim, "upper_bound")

    if value is not None and not isinstance(value, list) and lower_bound is not None and upper_bound is not None:
        return (float(value), float(lower_bound), float(upper_bound))
    if value is not None and not isinstance(value, list):
        v = float(value)
        return (v, v, v)
    if lower_bound is not None and upper_bound is not None:
        lo, hi = float(lower_bound), float(upper_bound)
        return ((lo + hi) / 2, lo, hi)

    return None


def intervals_compatible(
    interval_a: tuple[float, float, float],
    interval_b: tuple[float, float, float],
    tolerance: float = DEFAULT_TOLERANCE,
) -> bool:
    """Check if two intervals are compatible.

    Each interval is (center, lower, upper).
    - Both points: abs difference within tolerance
    - Range vs range: ranges overlap
    - Point vs range: point falls within range
    """
    _, lo_a, hi_a = interval_a
    _, lo_b, hi_b = interval_b

    is_point_a = abs(hi_a - lo_a) < tolerance
    is_point_b = abs(hi_b - lo_b) < tolerance

    # Both points
    if is_point_a and is_point_b:
        return abs(lo_a - lo_b) < tolerance

    # Both ranges (or one point, one range)
    # Overlap check: ranges overlap if one starts before the other ends
    return lo_a <= hi_b + tolerance and lo_b <= hi_a + tolerance


def _normalize_interval(
    interval: tuple[float, float, float],
    unit: str | None,
    form: "FormDefinition",
) -> tuple[float, float, float]:
    """Normalize all three components of an interval to SI units."""
    from propstore.dimensions import normalize_to_si

    center, lo, hi = interval
    return (
        normalize_to_si(center, unit, form),
        normalize_to_si(lo, unit, form),
        normalize_to_si(hi, unit, form),
    )


def values_compatible(
    value_a,
    value_b,
    tolerance: float = DEFAULT_TOLERANCE,
    claim_a: object | None = None,
    claim_b: object | None = None,
    forms: dict[str, "FormDefinition"] | None = None,
    concept_form: str | None = None,
) -> bool:
    """Check if two claim values are compatible.

    When claim_a/claim_b are provided, uses named field extraction.

    When *forms* and *concept_form* are supplied and the claims carry ``unit``
    fields, intervals are normalised to SI before comparison.
    """
    # Named fields path
    if claim_a is not None and claim_b is not None:
        interval_a = extract_interval(claim_a)
        interval_b = extract_interval(claim_b)
        if interval_a is not None and interval_b is not None:
            # Unit-aware normalisation when form metadata is available
            if forms is not None and concept_form is not None and concept_form in forms:
                form_def = forms[concept_form]
                unit_a = _claim_field(claim_a, "unit")
                unit_b = _claim_field(claim_b, "unit")
                if unit_a is not None or unit_b is not None:
                    interval_a = _normalize_interval(interval_a, unit_a, form_def)
                    interval_b = _normalize_interval(interval_b, unit_b, form_def)
            return intervals_compatible(interval_a, interval_b, tolerance)

    # Scalar values (not lists) — compare directly
    if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
        return abs(float(value_a) - float(value_b)) < tolerance

    return value_a == value_b


def value_str(value, claim: object | None = None) -> str:
    """Convert a claim's value to a string representation."""
    if claim is not None:
        interval = extract_interval(claim)
        if interval is not None:
            center, lo, hi = interval
            if abs(hi - lo) < DEFAULT_TOLERANCE:
                return str(center)
            v = _claim_field(claim, "value")
            if v is not None and not isinstance(v, list):
                return f"{v} [{lo}, {hi}]"
            return f"[{lo}, {hi}]"
    return str(value)


def _claim_field(claim: object, key: str) -> Any:
    getter = getattr(claim, "get", None)
    if callable(getter):
        return getter(key)
    return getattr(claim, key, None)
