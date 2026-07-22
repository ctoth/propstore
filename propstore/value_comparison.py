"""Unit-aware numeric value comparison for claims.

Compares claim values as intervals. When a form is supplied and the claims carry
``unit`` fields, both intervals are normalized to SI (via
``propstore.dimensions``) before comparison, so ``200 Hz`` and ``0.2 kHz`` read as
equal. A claim is anything exposing ``value`` / ``lower_bound`` / ``upper_bound``
/ ``unit`` as attributes (``ConflictClaim`` and ``DerivedConflictValue`` both
do), so this stays usable across the entity layers without a DTO.
"""

from __future__ import annotations

from collections.abc import Mapping

from propstore.dimensions import normalize_to_si
from propstore.families.forms import FormDefinition

DEFAULT_TOLERANCE = 1e-9

Interval = tuple[float, float, float]


def _claim_field(claim: object, key: str) -> object:
    """Read ``key`` off a claim-shaped object by attribute access."""

    return getattr(claim, key, None)


def _as_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _as_unit(value: object) -> str | None:
    return value if isinstance(value, str) else None


def extract_interval(claim: object) -> Interval | None:
    """Extract ``(center, lower, upper)`` from a claim's named value fields."""

    value = _as_float(_claim_field(claim, "value"))
    lower = _as_float(_claim_field(claim, "lower_bound"))
    upper = _as_float(_claim_field(claim, "upper_bound"))

    if value is not None and lower is not None and upper is not None:
        return (value, lower, upper)
    if value is not None:
        return (value, value, value)
    if lower is not None and upper is not None:
        return ((lower + upper) / 2, lower, upper)
    return None


def intervals_compatible(
    interval_a: Interval,
    interval_b: Interval,
    tolerance: float = DEFAULT_TOLERANCE,
) -> bool:
    """Whether two ``(center, lower, upper)`` intervals are compatible.

    Two points: equal within tolerance. Otherwise: the ranges overlap.
    """

    _, lo_a, hi_a = interval_a
    _, lo_b, hi_b = interval_b
    is_point_a = abs(hi_a - lo_a) < tolerance
    is_point_b = abs(hi_b - lo_b) < tolerance
    if is_point_a and is_point_b:
        return abs(lo_a - lo_b) < tolerance
    return lo_a <= hi_b + tolerance and lo_b <= hi_a + tolerance


def _normalize_interval(
    interval: Interval, unit: str | None, form: FormDefinition
) -> Interval:
    center, lo, hi = interval
    return (
        normalize_to_si(center, unit, form),
        normalize_to_si(lo, unit, form),
        normalize_to_si(hi, unit, form),
    )


def values_compatible(
    value_a: object,
    value_b: object,
    tolerance: float = DEFAULT_TOLERANCE,
    *,
    claim_a: object | None = None,
    claim_b: object | None = None,
    forms: Mapping[str, FormDefinition] | None = None,
    concept_form: str | None = None,
) -> bool:
    """Whether two claim values are compatible.

    With ``claim_a`` / ``claim_b``, values are extracted as intervals; if ``forms``
    and ``concept_form`` resolve a form and the claims carry units, the intervals
    are normalized to SI first. Otherwise scalars are compared directly.
    """

    if claim_a is not None and claim_b is not None:
        interval_a = extract_interval(claim_a)
        interval_b = extract_interval(claim_b)
        if interval_a is not None and interval_b is not None:
            if forms is not None and concept_form is not None and concept_form in forms:
                form_def = forms[concept_form]
                unit_a = _as_unit(_claim_field(claim_a, "unit"))
                unit_b = _as_unit(_claim_field(claim_b, "unit"))
                if (
                    unit_a is not None or unit_b is not None
                ) and form_def.unit_symbol is not None:
                    interval_a = _normalize_interval(interval_a, unit_a, form_def)
                    interval_b = _normalize_interval(interval_b, unit_b, form_def)
            return intervals_compatible(interval_a, interval_b, tolerance)

    float_a = _as_float(value_a)
    float_b = _as_float(value_b)
    if float_a is not None and float_b is not None:
        return abs(float_a - float_b) < tolerance
    return type(value_a) is type(value_b) and value_a == value_b


def value_str(
    value: object, claim: object | None = None, *, with_unit: bool = False
) -> str:
    """Render a claim's value as a string.

    With ``with_unit``, the claim's unit is appended when it carries one. Use it
    wherever the two rendered sides are not in the same unit system — a
    parameterization record compares an authored value against an SI-normalized
    derived one, so unlabelled numbers there read as disagreeing when they do
    not. Comparisons between two authored claims are already symmetric and pass
    the default.
    """

    rendered = _value_str(value, claim)
    if not with_unit or claim is None:
        return rendered
    unit = _as_unit(_claim_field(claim, "unit"))
    return f"{rendered} {unit}" if unit else rendered


def _value_str(value: object, claim: object | None) -> str:
    if claim is not None:
        interval = extract_interval(claim)
        if interval is not None:
            center, lo, hi = interval
            if abs(hi - lo) < DEFAULT_TOLERANCE:
                return str(center)
            raw = _claim_field(claim, "value")
            if _as_float(raw) is not None:
                return f"{raw} [{lo}, {hi}]"
            return f"[{lo}, {hi}]"
    return str(value)
