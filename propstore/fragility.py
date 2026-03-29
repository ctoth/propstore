"""Epistemic fragility engine.

Ranks epistemic targets by fragility: "What is the cheapest thing I could
learn that would most change what I believe?"

Sits at the render layer (layer 5). Reads from argumentation and theory
layers but never mutates source storage. Produces ranked recommendations.

Phase 1: FragilityTarget / FragilityReport, combine_fragility(), rank_fragility() skeleton.
Phase 2: Conflict topology scoring (Hamming distance on hypothetical extensions),
         probability-weighted epistemic scoring (Howard 1966 clairvoyance weighting),
         pairwise interaction detection (Howard 1966 non-additivity).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any


class FragilityWarning(UserWarning):
    """Warning emitted when fragility analysis encounters a recoverable error."""

    pass


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

    # Cost and ROI (Phase 4A)
    cost_tier: int | None = None          # 1=trivial, 2=cheap, 3=moderate, 4=expensive
    epistemic_roi: float | None = None    # fragility / cost_tier (higher = better ROI)

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
    interactions: tuple[dict, ...] = ()  # Phase 2: pairwise interaction results


def assign_cost_tier(target: FragilityTarget) -> int:
    """Assign ordinal cost tier based on target kind and properties.

    Cost tiers:
      1 (trivial): Check existing data, add an assumption (Tier 1 queryables)
      2 (cheap): Read a paper, run a calculation, measure a known concept
      3 (moderate): Commission new analysis, collect new samples
      4 (expensive): Run an experiment, replicate a study
    """
    if target.target_kind == "assumption":
        return 1
    if target.target_kind == "conflict":
        return 2
    if target.target_kind == "concept":
        if target.parametric_score is not None:
            return 2  # has existing claims / parametric data
        return 3  # no claims — need to find/produce data
    # Default for unknown kinds
    return 3


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


def score_conflict(
    framework: Any,
    claim_a_id: str,
    claim_b_id: str,
    *,
    semantics: str = "grounded",
) -> float:
    """Score a conflict by hypothetical world evaluation.

    Computes the Hamming distance (symmetric difference size) between
    the current extension and hypothetical extensions where each
    conflicting claim is removed in turn. Returns the max normalized
    distance, clamped to [0, 1].

    Parameters
    ----------
    framework : ArgumentationFramework
        The argumentation framework containing both claims.
    claim_a_id, claim_b_id : str
        The two conflicting argument/claim IDs.
    semantics : str
        Extension semantics to use (currently only "grounded" supported).

    Returns
    -------
    float
        Conflict score in [0, 1]. 0 = removing either claim changes nothing.
        1 = removing one claim maximally changes the extension.

    References
    ----------
    AlAnaissy 2024: ImpS^rev — revised impact measure via hypothetical
    removal. Hamming distance on extensions is a discrete analogue.
    """
    from propstore.dung import ArgumentationFramework, grounded_extension

    if not framework.arguments:
        return 0.0

    total = len(framework.arguments)

    # Current extension
    current = grounded_extension(framework)

    # Hypothetical: remove claim_a (B wins)
    def _remove(arg_id: str) -> frozenset[str]:
        args = frozenset(a for a in framework.arguments if a != arg_id)
        defeats = frozenset(
            (x, y) for x, y in framework.defeats
            if x != arg_id and y != arg_id
        )
        hyp = ArgumentationFramework(arguments=args, defeats=defeats)
        return grounded_extension(hyp)

    ext_remove_a = _remove(claim_a_id)
    ext_remove_b = _remove(claim_b_id)

    # Hamming distance = |symmetric difference|
    dist_a = len(current.symmetric_difference(ext_remove_a))
    dist_b = len(current.symmetric_difference(ext_remove_b))

    score = max(dist_a, dist_b) / total
    return min(1.0, score)


def weighted_epistemic_score(
    witnesses: list[dict],
    consistent_future_count: int,
    *,
    probability_weights: list[float] | None = None,
    witness_indices: list[int] | None = None,
    current_in_extension: bool = True,
) -> float:
    """Compute epistemic score with optional probability weighting.

    When probability_weights is None, returns the unweighted ratio
    len(witnesses) / consistent_future_count (current Phase 1 behavior).

    When probability_weights is provided, sums the weights of witness
    futures and divides by total weight of all futures.

    The ``current_in_extension`` flag controls sign correction (I5 fix):
    - For IN nodes: flip witnesses = futures where concept drops OUT.
      Score = witnesses / consistent (high flips = fragile).
    - For OUT nodes: flip witnesses = futures where concept enters IN.
      Score = 1 - witnesses / consistent (many entries = well-supported = low fragility).

    Parameters
    ----------
    witnesses : list[dict]
        Witness dicts from concept_stability()["witnesses"].
    consistent_future_count : int
        Total number of consistent futures.
    probability_weights : list[float] | None
        Per-future probability weights, indexed by future index.
        If None, uniform weighting (falls back to counting).
    witness_indices : list[int] | None
        Indices into probability_weights for which futures are witnesses.
        Required when probability_weights is provided.
    current_in_extension : bool
        Whether the concept is currently in the extension / determined.
        Defaults to True (preserving backward compat for IN nodes).

    Returns
    -------
    float
        Epistemic score in [0, 1]. Higher = more fragile.

    References
    ----------
    Howard 1966: clairvoyance formula averages over prior distribution.
    Gärdenfors & Makinson 1988: entrenchment deficit = 1 - support ratio.
    """
    if consistent_future_count <= 0:
        return 0.0

    if probability_weights is None:
        # Uniform: simple ratio
        raw = len(witnesses) / max(consistent_future_count, 1)
    elif total_weight := sum(probability_weights):
        if witness_indices is None:
            raw = len(witnesses) / max(consistent_future_count, 1)
        else:
            witness_weight = sum(probability_weights[i] for i in witness_indices)
            raw = witness_weight / total_weight
    else:
        return 0.0

    # I5: sign correction for OUT nodes
    if current_in_extension:
        return raw
    else:
        return 1.0 - raw


def detect_interactions(
    targets: list[FragilityTarget],
    bound: Any,
    queryables: list | None = None,
    *,
    top_k: int = 5,
    atms_limit: int = 8,
) -> list[dict]:
    """Detect pairwise interactions among top-k fragility targets.

    Uses ATMS concept_stability witnesses to detect real joint effects.
    A flip that requires 2+ queryables is synergistic (neither alone
    suffices). A concept flipped by two separate singleton witnesses
    indicates redundancy (both can flip it alone).

    Parameters
    ----------
    targets : list[FragilityTarget]
        Fragility targets to analyze.
    bound : Any
        BoundWorld for ATMS access. May be None for degraded operation.
    queryables : list | None
        Queryable CELs. Auto-discovered from ATMS if None.
    top_k : int
        Only consider the top-k targets by epistemic_score.
    atms_limit : int
        Bound on ATMS replay (2^atms_limit futures explored).

    Returns
    -------
    list[dict]
        Each dict has: target_a_id, target_b_id, interaction_type,
        concepts_affected.

    References
    ----------
    Howard 1966: V_c(x,y) != V_cx + V_cy in general — joint clairvoyance
    value may exceed or fall below sum of individual values.
    """
    if not targets:
        return []

    # Filter to assumption-type targets with epistemic scores
    scored = [
        t for t in targets
        if t.target_kind == "assumption" and t.epistemic_score is not None
    ]
    scored.sort(key=lambda t: t.epistemic_score or 0.0, reverse=True)
    scored = scored[:top_k]

    if len(scored) < 2:
        return []

    # Try ATMS-native interaction detection
    return _atms_interaction_detection(scored, bound, queryables, atms_limit)


def _atms_interaction_detection(
    scored: list[FragilityTarget],
    bound: Any,
    queryables: list | None,
    atms_limit: int,
) -> list[dict]:
    """Detect interactions via ATMS witness structure.

    For each concept affected by multiple targets, examines witnesses
    from concept_stability. Multi-queryable witnesses indicate synergy;
    multiple singleton witnesses for the same concept indicate redundancy.
    """
    # Collect target IDs as a set for fast lookup
    target_ids = {t.target_id for t in scored}

    # Try to get ATMS engine
    engine = None
    if bound is not None:
        try:
            engine = bound.atms_engine()
            if queryables is None:
                queryables = list(engine._all_parameterizations)
        except Exception:
            pass

    if engine is None or not queryables:
        # No ATMS available — return unknown interactions for each pair
        results: list[dict] = []
        for a, b in combinations(scored, 2):
            results.append({
                "target_a_id": a.target_id,
                "target_b_id": b.target_id,
                "interaction_type": "unknown",
                "concepts_affected": [],
            })
        return results

    # Build mapping: target_id -> queryable CELs that match
    target_queryables: dict[str, list] = {}
    for t in scored:
        matching = [q for q in queryables if t.target_id in str(q)]
        target_queryables[t.target_id] = matching

    # For each concept in the epistemic details, get stability witnesses
    # and examine which queryables they require
    synergistic_pairs: dict[tuple[str, str], list[str]] = {}
    redundant_pairs: dict[tuple[str, str], list[str]] = {}

    # Collect concepts from epistemic details of scored targets
    concept_ids: set[str] = set()
    for t in scored:
        if t.epistemic_detail and t.epistemic_detail.get("witnesses", 0) > 0:
            concept_ids.add(t.target_id)

    all_queryables_for_targets = []
    for t in scored:
        all_queryables_for_targets.extend(target_queryables.get(t.target_id, []))

    if not all_queryables_for_targets:
        all_queryables_for_targets = queryables

    for cid in concept_ids:
        try:
            stability = engine.concept_stability(
                cid, all_queryables_for_targets, limit=atms_limit
            )
        except Exception:
            continue

        witnesses = stability.get("witnesses", [])

        # Classify witnesses by their queryable sets
        singleton_qcels: dict[str, list[str]] = {}  # qcel -> [concept_ids]
        multi_qcels: list[tuple[list[str], str]] = []  # (qcels, concept_id)

        for witness in witnesses:
            qcels = witness.get("queryable_cels", [])
            if len(qcels) == 1:
                q = str(qcels[0])
                singleton_qcels.setdefault(q, []).append(cid)
            elif len(qcels) >= 2:
                multi_qcels.append(([str(q) for q in qcels], cid))

        # Synergistic: multi-queryable witnesses
        for qcels, concept in multi_qcels:
            # Find which target pairs these queryables belong to
            for qi, qj in combinations(qcels, 2):
                ti = _find_target_for_queryable(qi, scored, target_queryables)
                tj = _find_target_for_queryable(qj, scored, target_queryables)
                if ti and tj and ti != tj:
                    pair = (min(ti, tj), max(ti, tj))
                    synergistic_pairs.setdefault(pair, []).append(concept)

        # Redundant: same concept flipped by singleton witnesses of different targets
        for qi, qi_concepts in singleton_qcels.items():
            for qj, qj_concepts in singleton_qcels.items():
                if qi >= qj:
                    continue
                shared_concepts = set(qi_concepts) & set(qj_concepts)
                if shared_concepts:
                    ti = _find_target_for_queryable(qi, scored, target_queryables)
                    tj = _find_target_for_queryable(qj, scored, target_queryables)
                    if ti and tj and ti != tj:
                        pair = (min(ti, tj), max(ti, tj))
                        redundant_pairs.setdefault(pair, []).extend(shared_concepts)

    # Build results
    results: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()

    for pair, concepts in synergistic_pairs.items():
        seen_pairs.add(pair)
        results.append({
            "target_a_id": pair[0],
            "target_b_id": pair[1],
            "interaction_type": "synergistic",
            "concepts_affected": sorted(set(concepts)),
        })

    for pair, concepts in redundant_pairs.items():
        if pair in seen_pairs:
            # Already reported as synergistic — add redundancy note
            for r in results:
                if r["target_a_id"] == pair[0] and r["target_b_id"] == pair[1]:
                    r["interaction_type"] = "mixed"
                    r["concepts_affected"] = sorted(
                        set(r["concepts_affected"]) | set(concepts)
                    )
            continue
        seen_pairs.add(pair)
        results.append({
            "target_a_id": pair[0],
            "target_b_id": pair[1],
            "interaction_type": "redundant",
            "concepts_affected": sorted(set(concepts)),
        })

    # Add independent pairs not seen
    for a, b in combinations(scored, 2):
        pair = (min(a.target_id, b.target_id), max(a.target_id, b.target_id))
        if pair not in seen_pairs:
            results.append({
                "target_a_id": pair[0],
                "target_b_id": pair[1],
                "interaction_type": "independent",
                "concepts_affected": [],
            })

    return results


def _find_target_for_queryable(
    qcel: str,
    targets: list[FragilityTarget],
    target_queryables: dict[str, list],
) -> str | None:
    """Find which target a queryable CEL belongs to."""
    for t in targets:
        for tq in target_queryables.get(t.target_id, []):
            if str(tq) == qcel:
                return t.target_id
    return None


_TOL = 1e-9


def _try_perturb(opinion: Any, delta_u: float, a: float) -> Any | None:
    """Try to construct a perturbed opinion. Returns Opinion or None.

    Preserves the expectation E = b + a*u while shifting u by delta_u.
    Returns None if the resulting opinion would be invalid.
    """
    from propstore.opinion import Opinion

    E = opinion.expectation()
    u_new = opinion.u + delta_u
    if u_new < _TOL or u_new > 1.0 - _TOL:
        return None
    b_new = E - a * u_new
    d_new = 1.0 - u_new - b_new
    if b_new < -_TOL or d_new < -_TOL:
        return None
    b_new = max(0.0, b_new)
    d_new = max(0.0, d_new)
    try:
        return Opinion(b_new, d_new, u_new, a)
    except ValueError:
        return None


def opinion_sensitivity(
    opinions: list,
    index: int,
    *,
    delta: float = 0.01,
) -> float | None:
    """Marginal derivative dE(wbf)/du_i at current operating point.

    Computes central finite difference of the fused expectation
    with respect to the uncertainty of opinions[index].

    Uses adaptive delta: tries central difference first, falls back to
    one-sided difference, and shrinks delta on failure (up to 3 retries).

    Returns None if fewer than 2 opinions (no fusion partner),
    or if all perturbation attempts fail.

    References
    ----------
    Jøsang 2001: E(omega) = b + a*u. WBF fuses N opinions.
    """
    from propstore.opinion import wbf

    if len(opinions) < 2:
        return None

    # Check if any opinion is dogmatic (u essentially zero) — WBF can't handle it
    for op in opinions:
        if op.u < _TOL:
            return None

    oi = opinions[index]
    a_i = oi.a

    def _try_fuse(perturbed_op: Any) -> float | None:
        """Substitute perturbed opinion and compute fused expectation."""
        ops = list(opinions)
        ops[index] = perturbed_op
        try:
            return wbf(*ops).expectation()
        except ValueError:
            return None

    # Try with shrinking delta, up to 3 attempts
    current_delta = delta
    for _attempt in range(3):
        op_minus = _try_perturb(oi, -current_delta, a_i)
        op_plus = _try_perturb(oi, +current_delta, a_i)

        # Central difference: both sides valid
        if op_minus is not None and op_plus is not None:
            e_minus = _try_fuse(op_minus)
            e_plus = _try_fuse(op_plus)
            if e_minus is not None and e_plus is not None:
                actual_delta = 2.0 * current_delta
                if actual_delta < 1e-15:
                    return None
                return abs(e_plus - e_minus) / actual_delta

        # One-sided forward: only plus valid
        if op_plus is not None:
            e_base = _try_fuse(oi)
            e_plus = _try_fuse(op_plus)
            if e_base is not None and e_plus is not None:
                if current_delta < 1e-15:
                    return None
                return abs(e_plus - e_base) / current_delta

        # One-sided backward: only minus valid
        if op_minus is not None:
            e_base = _try_fuse(oi)
            e_minus = _try_fuse(op_minus)
            if e_base is not None and e_minus is not None:
                if current_delta < 1e-15:
                    return None
                return abs(e_base - e_minus) / current_delta

        # Both sides failed — shrink delta and retry
        current_delta /= 2.0

    return None


def imps_rev(
    framework: Any,
    supports: dict[tuple[str, str], float],
    base_scores: dict[str, float],
    attack: tuple[str, str],
) -> float:
    """AlAnaissy 2024 revised impact: sigma(B | remove A->B) - sigma(B).

    Measures how much removing attack (A,B) changes B's DF-QuAD strength.
    Positive = B gets stronger without the attack (A was harming B).

    Parameters
    ----------
    framework : ArgumentationFramework
        The argumentation framework containing attacks.
    supports : dict
        Support edges as (src, tgt) -> weight.
    base_scores : dict
        Base scores per argument for DF-QuAD.
    attack : tuple[str, str]
        The (attacker, target) defeat to evaluate.

    Returns
    -------
    float
        Strength difference. Positive means target is stronger without the attack.

    References
    ----------
    AlAnaissy 2024: ImpS^rev revised impact measure.
    Freedman et al. 2025: DF-QuAD gradual semantics.
    """
    from propstore.dung import ArgumentationFramework as AF
    from propstore.opinion import Opinion
    from propstore.praf import ProbabilisticAF
    from propstore.praf_dfquad import compute_dfquad_strengths

    if attack not in framework.defeats:
        return 0.0

    # Build PrAF with deterministic argument/defeat existence
    p_args = {arg: Opinion.dogmatic_true() for arg in framework.arguments}
    p_defeats = {d: Opinion.dogmatic_true() for d in framework.defeats}
    praf = ProbabilisticAF(framework=framework, p_args=p_args, p_defeats=p_defeats)

    # Full strengths
    strengths_full = compute_dfquad_strengths(praf, supports, base_scores=base_scores)

    # Build modified framework with attack removed
    new_defeats = frozenset(d for d in framework.defeats if d != attack)
    new_af = AF(arguments=framework.arguments, defeats=new_defeats)
    new_p_defeats = {k: v for k, v in p_defeats.items() if k != attack}
    new_praf = ProbabilisticAF(framework=new_af, p_args=p_args, p_defeats=new_p_defeats)

    # Strengths without the attack
    strengths_removed = compute_dfquad_strengths(new_praf, supports, base_scores=base_scores)

    target = attack[1]
    return strengths_removed[target] - strengths_full[target]


def _discover_tier2_concepts(bound: Any) -> list[FragilityTarget]:
    """Find concepts with no claims that appear in parameterization relationships.

    These are 'known unknowns' — concepts the system knows about
    (they appear in formulas) but has no measurements for.
    """
    try:
        store = bound._store
        # Collect all concept IDs that appear as inputs in parameterizations
        all_cids = store.concept_ids() if hasattr(store, "concept_ids") else []
        input_counts: dict[str, int] = {}

        for cid in all_cids:
            params = store.parameterizations_for(cid) if hasattr(store, "parameterizations_for") else []
            for param in params:
                concept_ids_json = param.get("concept_ids")
                if not concept_ids_json:
                    continue
                import json
                input_ids = json.loads(concept_ids_json) if isinstance(concept_ids_json, str) else concept_ids_json
                for iid in input_ids:
                    input_counts[iid] = input_counts.get(iid, 0) + 1

        # Find inputs that have no active claims
        targets: list[FragilityTarget] = []
        for iid, count in input_counts.items():
            try:
                claims = bound.active_claims(iid)
            except Exception:
                claims = []
            if not claims:
                cost = 3
                frag = 1.0
                roi = frag / cost
                targets.append(FragilityTarget(
                    target_id=iid,
                    target_kind="concept",
                    description=f"No measurements \u2014 input to {count} parameterizations",
                    parametric_score=None,
                    epistemic_score=None,
                    conflict_score=None,
                    fragility=frag,
                    cost_tier=cost,
                    epistemic_roi=roi,
                ))
        return targets
    except Exception:
        return []


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
    sort_by: str = "fragility",  # "fragility" or "roi"
    discovery_tier: int = 1,  # 1 = ATMS queryables only, 2 = also unknown concepts
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

    # Collect per-concept raw scores and details first
    raw_data: list[dict] = []
    raw_parametric: dict[str, float] = {}

    for cid in concept_ids:
        p_score, p_detail = (None, None)
        e_score, e_detail = (None, None)
        c_score, c_detail = (None, None)

        if include_parametric:
            p_score, p_detail = _parametric_dimension(bound, cid)
            if p_score is not None:
                raw_parametric[cid] = p_score

        if include_epistemic:
            e_score, e_detail = _epistemic_dimension(
                bound, cid, queryables, atms_limit
            )

        if include_conflict:
            c_score, c_detail = _conflict_dimension(bound, cid)

        raw_data.append({
            "cid": cid,
            "p_score": p_score, "p_detail": p_detail,
            "e_score": e_score, "e_detail": e_detail,
            "c_score": c_score, "c_detail": c_detail,
        })

    # C1 fix: normalize parametric scores across all concepts
    normalized_parametric = _normalize_parametric_scores(raw_parametric)

    for entry in raw_data:
        cid = entry["cid"]
        p_score = normalized_parametric.get(cid, entry["p_score"])
        e_score = entry["e_score"]
        c_score = entry["c_score"]

        frag = combine_fragility(p_score, e_score, c_score, combination)

        t = FragilityTarget(
                target_id=cid,
                target_kind="concept",
                description=f"Concept {cid}",
                parametric_score=p_score,
                epistemic_score=e_score,
                conflict_score=c_score,
                fragility=frag,
                parametric_detail=entry["p_detail"],
                epistemic_detail=entry["e_detail"],
                conflict_detail=entry["c_detail"],
            )
        cost = assign_cost_tier(t)
        roi = t.fragility / cost if cost else None
        targets.append(FragilityTarget(
            target_id=t.target_id,
            target_kind=t.target_kind,
            description=t.description,
            parametric_score=t.parametric_score,
            epistemic_score=t.epistemic_score,
            conflict_score=t.conflict_score,
            fragility=t.fragility,
            cost_tier=cost,
            epistemic_roi=roi,
            parametric_detail=t.parametric_detail,
            epistemic_detail=t.epistemic_detail,
            conflict_detail=t.conflict_detail,
        ))

    # Tier 2 discovery: find concepts with no claims
    if discovery_tier >= 2:
        tier2 = _discover_tier2_concepts(bound)
        targets.extend(tier2)

    # Sort by chosen criterion
    if sort_by == "roi":
        targets.sort(key=lambda t: t.epistemic_roi if t.epistemic_roi is not None else -1.0, reverse=True)
    else:
        targets.sort(key=lambda t: t.fragility, reverse=True)
    targets = targets[:top_k]

    # World fragility = mean of top min(10, len) scores
    top_scores = [t.fragility for t in targets[: min(10, len(targets))]]
    world_frag = sum(top_scores) / len(top_scores) if top_scores else 0.0

    # Phase 2: detect pairwise interactions among top targets
    interactions = detect_interactions(
        targets, bound, queryables, top_k=min(top_k, 5), atms_limit=atms_limit
    )

    scope = f"concept:{concept_id}" if concept_id else "all"
    return FragilityReport(
        targets=tuple(targets),
        world_fragility=world_frag,
        analysis_scope=scope,
        interactions=tuple(interactions),
    )


def _normalize_parametric_scores(raw_scores: dict[str, float]) -> dict[str, float]:
    """Normalize raw parametric scores across all concepts to [0, 1].

    Divides each raw max-elasticity score by the global maximum.
    If all scores are zero, returns all zeros.

    Parameters
    ----------
    raw_scores : dict[str, float]
        Mapping of concept_id -> raw max absolute elasticity.

    Returns
    -------
    dict[str, float]
        Mapping of concept_id -> normalized score in [0, 1].
    """
    if not raw_scores:
        return {}
    global_max = max(raw_scores.values())
    if global_max < 1e-12:
        return {k: 0.0 for k in raw_scores}
    return {k: v / global_max for k, v in raw_scores.items()}


# ── Internal dimension helpers ──────────────────────────────────────


def _derived_concepts(bound: Any) -> list[str]:
    """Get all concept IDs that have parameterizations (derived concepts)."""
    try:
        store = bound._store
        concepts = store.concept_ids() if hasattr(store, "concept_ids") else []
        return list(concepts)
    except Exception as exc:
        warnings.warn(
            f"Concept discovery failed: {exc}",
            FragilityWarning,
            stacklevel=2,
        )
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

        # C1 fix: return raw max absolute elasticity, not self-normalized.
        # rank_fragility normalizes across all concepts afterward.
        score = max_abs
        return score, {
            "elasticities": elasticities,
            "max_abs": max_abs,
            "formula": result.formula,
        }
    except Exception as exc:
        warnings.warn(
            f"Parametric dimension failed for concept: {exc}",
            FragilityWarning,
            stacklevel=2,
        )
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

        # I5/I1: determine current status and delegate to weighted_epistemic_score
        current_status = stability.get("current_status", "determined")
        in_extension = current_status in ("determined", "in")

        score = weighted_epistemic_score(
            witnesses,
            consistent,
            current_in_extension=in_extension,
        )
        score = min(1.0, score)  # Clamp to [0, 1]

        return score, {
            "witnesses": len(witnesses),
            "consistent_futures": consistent,
            "stable": stability.get("stable", True),
            "current_status": current_status,
        }
    except Exception as exc:
        warnings.warn(
            f"Epistemic dimension failed for concept: {exc}",
            FragilityWarning,
            stacklevel=2,
        )
        return None, None


def _conflict_dimension(
    bound: Any, concept_id: str
) -> tuple[float | None, dict | None]:
    """Compute conflict fragility via hypothetical world evaluation.

    Phase 2: scores each conflict by downstream impact on the grounded
    extension. Uses Hamming distance between current and hypothetical
    extensions (AlAnaissy 2024 ImpS^rev discrete analogue).
    """
    try:
        conflicts = bound.conflicts(concept_id)
        if not conflicts:
            return None, None

        active_graph = getattr(bound, "_active_graph", None)
        if active_graph is not None:
            # Build AF from the active graph for topology scoring
            from propstore.core.analyzers import shared_analyzer_input_from_active_graph

            try:
                shared = shared_analyzer_input_from_active_graph(active_graph)
                framework = shared.argumentation_framework
                max_score = 0.0
                for c in conflicts:
                    a_id = c.get("claim_a_id", "")
                    b_id = c.get("claim_b_id", "")
                    if a_id and b_id:
                        s = score_conflict(framework, a_id, b_id)
                        max_score = max(max_score, s)
                score = max_score if max_score > 0.0 else 1.0
            except Exception as exc:
                warnings.warn(
                    f"Conflict scoring fell back to 1.0: {exc}",
                    FragilityWarning,
                    stacklevel=2,
                )
                score = 1.0
        else:
            # No active graph available — fall back to placeholder
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
    except Exception as exc:
        warnings.warn(
            f"Conflict dimension failed for concept: {exc}",
            FragilityWarning,
            stacklevel=2,
        )
        return None, None
