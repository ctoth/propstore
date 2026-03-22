"""Pure numeric value comparison logic for claims.

Compares values, parses intervals, checks compatibility.
No propstore imports — only stdlib.
"""

from __future__ import annotations

DEFAULT_TOLERANCE = 1e-9


def parse_numeric_values(value_list: list) -> tuple[float, ...]:
    """Extract numeric values from a claim value list (legacy format).

    Returns a tuple of floats. A single-element list is a scalar;
    a two-element list is a range [min, max].
    """
    result = []
    for v in value_list:
        try:
            result.append(float(v))
        except (TypeError, ValueError):
            pass
    return tuple(result)


def extract_interval(claim: dict) -> tuple[float, float, float] | None:
    """Extract (center, lower, upper) from a claim's named value fields.

    Returns None if the claim has no numeric value information.
    Falls back to legacy value list format if named fields absent.
    """
    value = claim.get("value")
    lower_bound = claim.get("lower_bound")
    upper_bound = claim.get("upper_bound")

    is_list_value = isinstance(value, list)

    if value is not None and not is_list_value and lower_bound is not None and upper_bound is not None:
        return (float(value), float(lower_bound), float(upper_bound))
    if value is not None and not is_list_value:
        v = float(value)
        return (v, v, v)
    if lower_bound is not None and upper_bound is not None:
        lo, hi = float(lower_bound), float(upper_bound)
        return ((lo + hi) / 2, lo, hi)

    # Legacy path: value is a list
    if isinstance(value, list):
        nums = parse_numeric_values(value)
        if len(nums) == 1:
            return (nums[0], nums[0], nums[0])
        if len(nums) >= 2:
            lo, hi = min(nums), max(nums)
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


def values_compatible(value_a, value_b, tolerance: float = DEFAULT_TOLERANCE,
                      claim_a: dict | None = None, claim_b: dict | None = None) -> bool:
    """Check if two claim values are compatible.

    Supports both legacy list format and named value fields.
    When claim_a/claim_b are provided, uses named field extraction.
    """
    # Named fields path
    if claim_a is not None and claim_b is not None:
        interval_a = extract_interval(claim_a)
        interval_b = extract_interval(claim_b)
        if interval_a is not None and interval_b is not None:
            return intervals_compatible(interval_a, interval_b, tolerance)

    # Legacy list path
    if isinstance(value_a, list) and isinstance(value_b, list):
        nums_a = parse_numeric_values(value_a)
        nums_b = parse_numeric_values(value_b)

        if not nums_a or not nums_b:
            return value_a == value_b

        if len(nums_a) == 1 and len(nums_b) == 1:
            return abs(nums_a[0] - nums_b[0]) < tolerance

        if len(nums_a) >= 2 and len(nums_b) >= 2:
            min_a, max_a = min(nums_a), max(nums_a)
            min_b, max_b = min(nums_b), max(nums_b)
            return min_a <= max_b and min_b <= max_a

        if len(nums_a) == 1 and len(nums_b) >= 2:
            min_b, max_b = min(nums_b), max(nums_b)
            return min_b - tolerance <= nums_a[0] <= max_b + tolerance

        if len(nums_b) == 1 and len(nums_a) >= 2:
            min_a, max_a = min(nums_a), max(nums_a)
            return min_a - tolerance <= nums_b[0] <= max_a + tolerance

        return value_a == value_b

    # Scalar values (not lists) — compare directly
    if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
        return abs(float(value_a) - float(value_b)) < tolerance

    return value_a == value_b


def value_str(value, claim: dict | None = None) -> str:
    """Convert a claim's value to a string representation.

    Supports both legacy list format and named value fields.
    """
    if claim is not None:
        interval = extract_interval(claim)
        if interval is not None:
            center, lo, hi = interval
            if abs(hi - lo) < DEFAULT_TOLERANCE:
                return str(center)
            v = claim.get("value")
            if v is not None and not isinstance(v, list):
                return f"{v} [{lo}, {hi}]"
            return f"[{lo}, {hi}]"

    if isinstance(value, list):
        if len(value) == 1:
            return str(value[0])
        return str(value)
    return str(value)
