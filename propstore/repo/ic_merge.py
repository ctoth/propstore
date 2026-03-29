"""Scalar adaptations of Konieczny 2002 aggregation operators.

Implements render-time aggregation kernels inspired by Konieczny & Pino Pérez
2002. Each operator takes a profile mapping source IDs to scalar claim values
and returns the winning value that minimizes aggregated distance.

- Sigma: minimizes sum of distances
- Max: minimizes maximum distance
- GMax: lexicographically compares sorted distance vectors

Konieczny 2002 defines merging over propositional belief bases with
min-over-models distance and an integrity constraint ``mu`` over models. This
module preserves the aggregation families (sum/max/leximax) but adapts them to
a scalar-value domain: numeric claims use absolute difference and categorical
claims use Hamming distance (0/1).

This module does not yet implement assignment-level integrity constraints and
therefore must not be read as satisfying IC0-IC8 as stated in the paper. It
currently provides scalar distance kernels plus an unconstrained dispatcher.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any


class MergeOperator(StrEnum):
    SIGMA = "sigma"
    MAX = "max"
    GMAX = "gmax"


def claim_distance(a: Any, b: Any) -> float:
    """Distance between two claim values.

    Numeric values: absolute difference.
    Non-numeric: Hamming distance (0 if equal, 1 if different).

    Per Konieczny 2002 claim13/17: d(I, phi) is a distance metric
    between interpretations.
    """
    try:
        return abs(float(a) - float(b))
    except (ValueError, TypeError):
        return 0.0 if a == b else 1.0


def sigma_merge(profile: dict[str, Any]) -> Any:
    """Select the value minimizing sum distance to all profile values.

    Per Konieczny 2002 claim13-15: d_Sigma(I, Psi) = sum d(I, phi).

    Candidates are drawn from the profile values themselves (discrete selection,
    no interpolation). The majority value wins because it has the lowest total
    distance when counted with multiplicity.
    """
    candidates = list(profile.values())
    best_value = None
    best_score = float("inf")
    for candidate in candidates:
        score = sum(claim_distance(candidate, v) for v in candidates)
        if score < best_score:
            best_score = score
            best_value = candidate
        elif score == best_score and best_value is not None:
            # Stable tie-breaking: pick the smaller value for IC3 syntax independence.
            # Ensures result depends only on the multi-set of values, not key order.
            try:
                if float(candidate) < float(best_value):
                    best_value = candidate
            except (ValueError, TypeError):
                if str(candidate) < str(best_value):
                    best_value = candidate
    return best_value


def _unique_values(profile: dict[str, Any]) -> list[Any]:
    """Deduplicate profile values, preserving order of first occurrence.

    Max and GMax satisfy the Arb property (Konieczny 2002 claim18-19):
    duplicating a source must not change the result. This requires computing
    distances against unique values only, so multiplicity is ignored.
    """
    result: list[Any] = []
    for v in profile.values():
        if not any(existing == v for existing in result):
            result.append(v)
    return result


def max_merge(profile: dict[str, Any]) -> Any:
    """Select the value minimizing maximum distance to the profile values.

    Per Konieczny 2002 claim17-18: d_Max(I, Psi) = max d(I, phi).

    Uses deduplicated values for both candidates and distance targets,
    ensuring the Arb property (insensitivity to source multiplicity).
    """
    unique = _unique_values(profile)
    best_value = None
    best_score = float("inf")
    for candidate in unique:
        score = max(claim_distance(candidate, v) for v in unique)
        if score < best_score:
            best_score = score
            best_value = candidate
        elif score == best_score and best_value is not None:
            try:
                if float(candidate) < float(best_value):
                    best_value = candidate
            except (ValueError, TypeError):
                if str(candidate) < str(best_value):
                    best_value = candidate
    return best_value


def gmax_merge(profile: dict[str, Any]) -> Any:
    """Lexicographically compare sorted distance vectors over profile values.

    Per Konieczny 2002 claim19-20: GMax refines Max.

    Uses deduplicated values for both candidates and distance targets,
    ensuring the Arb property (insensitivity to source multiplicity).
    For each candidate, compute its distance to every unique value, sort
    descending, then pick the candidate with the lexicographically smallest
    sorted vector.
    """
    unique = _unique_values(profile)
    best_value = None
    best_vector: list[float] | None = None
    for candidate in unique:
        distances = sorted(
            [claim_distance(candidate, v) for v in unique],
            reverse=True,
        )
        if best_vector is None or distances < best_vector:
            best_vector = distances
            best_value = candidate
        elif distances == best_vector and best_value is not None:
            try:
                if float(candidate) < float(best_value):
                    best_value = candidate
            except (ValueError, TypeError):
                if str(candidate) < str(best_value):
                    best_value = candidate
    return best_value


def ic_merge(profile: dict[str, Any], *, operator: str = "sigma") -> Any:
    """Dispatch to the appropriate merge operator.

    Default is the Sigma aggregation kernel (Konieczny 2002 claim15).
    """
    # TODO: branch_weights from RenderPolicy not yet consumed.
    # When implemented, weighted_sigma would use w_i * d(I, phi_i)
    # per Konieczny 2002 weighted profile extension.
    dispatch = {
        "sigma": sigma_merge,
        "max": max_merge,
        "gmax": gmax_merge,
    }
    fn = dispatch.get(operator)
    if fn is None:
        raise ValueError(f"Unknown merge operator: {operator}")
    return fn(profile)
