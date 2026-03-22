"""Preference ordering for ASPIC+ argumentation.

Determines which attacks survive as defeats based on argument strength.

References:
    Modgil, S. & Prakken, H. (2018). An abstract framework for
    argumentation with structured arguments. Argument & Computation.
    Def 9 (defeat), Def 19 (set comparisons).
"""

from __future__ import annotations

import math


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
    if comparison == "elitist":
        return any(all(x < y for y in set_b) for x in set_a)
    elif comparison == "democratic":
        if not set_a:
            return True  # vacuously true: forall x in empty set
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


def claim_strength(claim: dict) -> float:
    """Compute ordinal strength from claim metadata.

    Composes from available signals:
      - sample_size: log-scaled (diminishing returns)
      - uncertainty: inverse (lower = stronger)
      - confidence: direct (stance classification confidence)

    Missing metadata is neutral (contributes 0), not penalizing.
    """
    score = 0.0
    components = 0

    sample_size = claim.get("sample_size")
    if sample_size is not None and sample_size > 0:
        score += math.log1p(sample_size)
        components += 1

    uncertainty = claim.get("uncertainty")
    if uncertainty is not None and uncertainty > 0:
        score += 1.0 / uncertainty
        components += 1

    confidence = claim.get("confidence")
    if confidence is not None:
        score += confidence
        components += 1

    if components == 0:
        return 1.0  # neutral default for claims with no metadata

    return score
