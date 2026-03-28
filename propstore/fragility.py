"""Epistemic fragility engine — Phase 1 skeleton.

Ranks epistemic targets by fragility: "What is the cheapest thing I could
learn that would most change what I believe?"

Sits at the render layer (layer 5). Reads from argumentation and theory
layers but never mutates source storage. Produces ranked recommendations.

Phase 1 implements:
- FragilityTarget / FragilityReport data structures
- combine_fragility() score combination with configurable policies
- rank_fragility() skeleton wiring parametric, epistemic, conflict dimensions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FragilityTarget:
    """One thing you could learn, scored by epistemic leverage."""

    target_id: str
    target_kind: str  # "concept" | "claim" | "assumption" | "conflict"
    description: str

    # Individual dimension scores (each in [0, 1], higher = more fragile)
    parametric_score: float | None = None
    epistemic_score: float | None = None
    conflict_score: float | None = None

    # Combined score
    fragility: float = 0.0

    # Provenance
    parametric_detail: dict[str, Any] | None = None
    epistemic_detail: dict[str, Any] | None = None
    conflict_detail: dict[str, Any] | None = None


@dataclass(frozen=True)
class FragilityReport:
    """Complete fragility analysis for a bound world."""

    targets: tuple[FragilityTarget, ...] = ()
    world_fragility: float = 0.0
    analysis_scope: str = ""


def combine_fragility(
    parametric: float | None,
    epistemic: float | None,
    conflict: float | None,
    combination: str = "top2",
) -> float:
    """Combine dimension scores into a single fragility score.

    Parameters
    ----------
    parametric, epistemic, conflict : float | None
        Individual dimension scores in [0, 1]. None means not applicable.
    combination : str
        Policy for combining scores:
        - "top2": average of two highest available scores (default)
        - "mean": average of all available scores
        - "max": maximum of available scores
        - "product": product of available scores
    """
    scores = sorted(
        [s for s in (parametric, epistemic, conflict) if s is not None],
        reverse=True,
    )
    if not scores:
        return 0.0

    if combination == "top2":
        if len(scores) == 1:
            return scores[0]
        return (scores[0] + scores[1]) / 2.0
    elif combination == "mean":
        return sum(scores) / len(scores)
    elif combination == "max":
        return scores[0]  # already sorted descending
    elif combination == "product":
        result = 1.0
        for s in scores:
            result *= s
        return result
    else:
        raise ValueError(f"Unknown combination policy: {combination!r}")


def rank_fragility(
    bound: Any,  # BoundWorld — string annotation to avoid circular import
    *,
    concept_id: str | None = None,
    queryables: list | None = None,
    top_k: int = 20,
    include_parametric: bool = True,
    include_epistemic: bool = True,
    include_conflict: bool = True,
    combination: str = "top2",
    atms_limit: int = 8,
) -> FragilityReport:
    """Rank epistemic targets by fragility.

    Parameters
    ----------
    bound : BoundWorld
        The current world view to analyze.
    concept_id : str, optional
        Focus on a single concept. If None, analyze all derived concepts.
    queryables : list, optional
        Assumptions that could be resolved. If None, auto-discovered
        from the ATMS engine.
    top_k : int
        Return only the top-k most fragile targets.
    include_parametric : bool
        Whether to compute parametric sensitivity dimension.
    include_epistemic : bool
        Whether to compute epistemic stability dimension.
    include_conflict : bool
        Whether to compute conflict topology dimension.
    combination : str
        How to combine dimension scores: "top2", "mean", "max", "product".
    atms_limit : int
        Bound on ATMS replay (2^atms_limit futures explored).
    """
    targets: list[FragilityTarget] = []

    # Determine which concepts to analyze
    concept_ids = [concept_id] if concept_id else _derived_concepts(bound)

    for cid in concept_ids:
        p_score, p_detail = (None, None)
        e_score, e_detail = (None, None)
        c_score, c_detail = (None, None)

        if include_parametric:
            p_score, p_detail = _parametric_dimension(bound, cid)

        if include_epistemic:
            e_score, e_detail = _epistemic_dimension(
                bound, cid, queryables, atms_limit
            )

        if include_conflict:
            c_score, c_detail = _conflict_dimension(bound, cid)

        frag = combine_fragility(p_score, e_score, c_score, combination)

        targets.append(
            FragilityTarget(
                target_id=cid,
                target_kind="concept",
                description=f"Concept {cid}",
                parametric_score=p_score,
                epistemic_score=e_score,
                conflict_score=c_score,
                fragility=frag,
                parametric_detail=p_detail,
                epistemic_detail=e_detail,
                conflict_detail=c_detail,
            )
        )

    # Sort by fragility descending, take top_k
    targets.sort(key=lambda t: t.fragility, reverse=True)
    targets = targets[:top_k]

    # World fragility = mean of top min(10, len) scores
    top_scores = [t.fragility for t in targets[: min(10, len(targets))]]
    world_frag = sum(top_scores) / len(top_scores) if top_scores else 0.0

    scope = f"concept:{concept_id}" if concept_id else "all"
    return FragilityReport(
        targets=tuple(targets),
        world_fragility=world_frag,
        analysis_scope=scope,
    )


# ── Internal dimension helpers ──────────────────────────────────────


def _derived_concepts(bound: Any) -> list[str]:
    """Get all concept IDs that have parameterizations (derived concepts)."""
    try:
        store = bound._store
        concepts = store.concept_ids() if hasattr(store, "concept_ids") else []
        return list(concepts)
    except Exception:
        return []


def _parametric_dimension(
    bound: Any, concept_id: str
) -> tuple[float | None, dict | None]:
    """Compute parametric fragility via sensitivity analysis.

    Normalizes elasticities to [0, 1] by dividing by the max absolute
    elasticity across all inputs.
    """
    try:
        from propstore.sensitivity import analyze_sensitivity

        store = bound._store
        result = analyze_sensitivity(store, concept_id, bound)
        if result is None or not result.entries:
            return None, None

        elasticities = [
            e.elasticity for e in result.entries if e.elasticity is not None
        ]
        if not elasticities:
            return None, None

        max_abs = max(abs(e) for e in elasticities)
        if max_abs < 1e-12:
            return 0.0, {"elasticities": elasticities, "max_abs": 0.0}

        # Normalized score = max elasticity / max elasticity = 1.0 for this concept
        # (the concept with the highest elasticity input gets score 1.0)
        score = max(abs(e) for e in elasticities) / max_abs
        return score, {
            "elasticities": elasticities,
            "max_abs": max_abs,
            "formula": result.formula,
        }
    except Exception:
        return None, None


def _epistemic_dimension(
    bound: Any,
    concept_id: str,
    queryables: list | None,
    limit: int,
) -> tuple[float | None, dict | None]:
    """Compute epistemic fragility via ATMS stability.

    Score = number of flip witnesses / consistent future count.
    """
    try:
        atms = bound.atms_engine()
        if queryables is None:
            queryables = list(atms._all_parameterizations)
        if not queryables:
            return None, None

        stability = atms.concept_stability(concept_id, queryables, limit=limit)
        witnesses = stability.get("witnesses", [])
        consistent = stability.get("consistent_future_count", 1)
        if consistent == 0:
            consistent = 1

        score = len(witnesses) / consistent
        score = min(1.0, score)  # Clamp to [0, 1]

        return score, {
            "witnesses": len(witnesses),
            "consistent_futures": consistent,
            "stable": stability.get("stable", True),
        }
    except Exception:
        return None, None


def _conflict_dimension(
    bound: Any, concept_id: str
) -> tuple[float | None, dict | None]:
    """Compute conflict fragility.

    Phase 1 placeholder: score = 1.0 for each conflict present.
    Phase 2 will compute actual downstream impact.
    """
    try:
        conflicts = bound.conflicts(concept_id)
        if not conflicts:
            return None, None

        # Placeholder: presence of conflict = fragility 1.0
        score = 1.0
        return score, {
            "conflict_count": len(conflicts),
            "conflicts": [
                {
                    "claim_a": c.get("claim_a_id", ""),
                    "claim_b": c.get("claim_b_id", ""),
                }
                for c in conflicts[:5]  # Limit detail size
            ],
        }
    except Exception:
        return None, None
