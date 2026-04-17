"""Preference helpers for claim-graph and structured argumentation.

References:
    Modgil, S. & Prakken, H. (2018). An abstract framework for
    argumentation with structured arguments. Argument & Computation.
    Def 9 (defeat), Def 19 (set comparisons).

This module contains two distinct layers:

- literature-backed set-comparison helpers (`strictly_weaker`,
  `defeat_holds`) used for generic strength-set comparisons; and
- a metadata-derived heuristic (`metadata_strength_vector`) for
  flat claim graphs.

The metadata heuristic is not a full ASPIC+ Def. 19 / Defs. 20-21
structured-argument ordering over premises and defeasible rules.
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Iterable, Mapping
from typing import Any, TypeVar

from propstore.core.active_claims import ActiveClaim

TOrder = TypeVar("TOrder", bound=Hashable)


def strict_partial_order_closure(
    pairs: Iterable[tuple[TOrder, TOrder]],
) -> frozenset[tuple[TOrder, TOrder]]:
    """Return the transitive closure of a strict partial order.

    Pairs are oriented ``(weaker, stronger)``, matching
    ``PreferenceConfig.rule_order`` in ``propstore.aspic``. The result is
    the smallest transitive relation containing the authored pairs. Any
    reflexive edge or cycle is rejected because Modgil & Prakken Def 22
    requires a strict partial order.
    """

    closure: set[tuple[TOrder, TOrder]] = set()
    for weaker, stronger in pairs:
        if weaker == stronger:
            raise ValueError("strict partial order cannot contain a reflexive pair")
        closure.add((weaker, stronger))

    changed = True
    while changed:
        changed = False
        new_pairs: set[tuple[TOrder, TOrder]] = set()
        for left, mid in closure:
            for source, right in closure:
                if mid == source and (left, right) not in closure:
                    if left == right:
                        raise ValueError("strict partial order contains a cycle")
                    new_pairs.add((left, right))
        if new_pairs:
            closure |= new_pairs
            changed = True

    for weaker, stronger in closure:
        if (stronger, weaker) in closure:
            raise ValueError("strict partial order contains a cycle")
    return frozenset(closure)

def strictly_weaker(
    set_a: list[float],
    set_b: list[float],
    comparison: str,
) -> bool:
    """Test if set_a is strictly weaker than set_b.

    Def 19 (Modgil & Prakken 2018, p.21):
      Elitist: set_a < set_b iff EXISTS x in set_a s.t. FORALL y in set_b, x < y
      Democratic: set_a < set_b iff FORALL x in set_a EXISTS y in set_b, x < y
    """
    if not set_a or not set_b:
        return False  # empty set cannot be strictly weaker or stronger
    if comparison == "elitist":
        return any(all(x < y for y in set_b) for x in set_a)
    elif comparison == "democratic":
        return all(any(x < y for y in set_b) for x in set_a)
    else:
        raise ValueError(f"Unknown comparison: {comparison}")


def defeat_holds(
    attack_type: str,
    attacker_strengths: list[float],
    target_strengths: list[float],
    comparison: str,
) -> bool:
    """Determine if an attack succeeds as a defeat.

    Def 9 (Modgil & Prakken 2018, p.12):
      - Undercutting/supersedes: always succeeds (preference-independent)
      - Rebutting/undermining: succeeds iff attacker is NOT strictly weaker
    """
    if attack_type in ("undercuts", "supersedes"):
        return True
    if attack_type in ("rebuts", "undermines"):
        return not strictly_weaker(attacker_strengths, target_strengths, comparison)
    raise ValueError(f"Unknown attack type: {attack_type}")


def metadata_strength_vector(claim: ActiveClaim | Mapping[str, Any]) -> list[float]:
    """Compute a heuristic fixed-length strength vector from claim metadata.

    Always returns exactly 3 dimensions so that Def 19 (Modgil & Prakken
    2018, p.21) Elitist/Democratic set comparisons are commensurable
    across claims with different metadata profiles.

    Fixed dimensions:
      [0] log_sample_size:    log1p(sample_size), default 0.0 (no samples)
      [1] inverse_uncertainty: 1/uncertainty,      default 1.0 (max uncertainty)
      [2] confidence:          direct value,        default 0.5 (coin flip)

    Neutral defaults represent honest ignorance — they neither advantage
    nor disadvantage a claim in pairwise comparison.

    References:
        Modgil & Prakken 2018, Def 19: Elitist/Democratic set comparison
        requires commensurable vectors of the same dimensionality.
    """
    if isinstance(claim, ActiveClaim):
        sample_size = claim.sample_size
        uncertainty = claim.uncertainty
        confidence = claim.attributes.get("confidence")
    else:
        sample_size = claim.get("sample_size")
        uncertainty = claim.get("uncertainty")
        confidence = claim.get("confidence")
    return [
        math.log1p(sample_size) if sample_size and sample_size > 0 else 0.0,
        1.0 / uncertainty if uncertainty and uncertainty > 0 else 1.0,
        confidence if confidence is not None else 0.5,
    ]


def claim_strength(claim: ActiveClaim | Mapping[str, Any]) -> list[float]:
    """Backward-compatible alias for the metadata heuristic.

    This name remains for compatibility with the existing claim-graph code,
    but the behavior is heuristic rather than literature-equivalent.
    Prefer ``metadata_strength_vector`` in new code and tests.
    """
    return metadata_strength_vector(claim)
