"""Claim-graph argumentation backend.

This module does not build full structured ASPIC+ arguments. The "arguments"
here are active claim rows, preferences come from heuristic claim metadata,
and conditions only decide which claims are active before AF construction.
The result is a claim-graph backend inspired by Dung and ASPIC+ ideas.
"""

from __future__ import annotations

from pathlib import Path

from propstore.dung import (
    ArgumentationFramework,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from propstore.preference import claim_strength, defeat_holds
from propstore.world.types import ArtifactStore

_ATTACK_TYPES = frozenset({"rebuts", "undercuts", "undermines", "supersedes"})
_UNCONDITIONAL_TYPES = frozenset({"undercuts", "supersedes"})
_PREFERENCE_TYPES = frozenset({"rebuts", "undermines"})
_SUPPORT_TYPES = frozenset({"supports", "explains"})
_NON_ATTACK_TYPES = frozenset({"supports", "explains", "none"})


def _transitive_support_targets(
    source: str,
    supports: set[tuple[str, str]],
    visited: set[str] | None = None,
) -> set[str]:
    """Compute all arguments reachable from source via support edges."""
    if visited is None:
        visited = set()
    visited.add(source)
    targets: set[str] = set()
    for a, b in supports:
        if a == source and b not in visited:
            targets.add(b)
            targets |= _transitive_support_targets(b, supports, visited)
    return targets


def _cayrol_derived_defeats(
    defeats: set[tuple[str, str]],
    supports: set[tuple[str, str]],
) -> set[tuple[str, str]]:
    """Compute derived defeats per Cayrol 2005 Definition 3.

    Supported defeat: A →sup ... →sup B →def C  ⟹  (A, C)
      A supports B (transitively), B defeats C.

    Indirect defeat: A →def B →sup ... →sup C  ⟹  (A, C)
      A defeats B, B supports C (transitively).

    Derived defeats can chain: if (A,C) is a derived defeat and C
    supports D, then (A,D) is also a derived indirect defeat. This
    requires fixpoint iteration — each pass may produce new defeats
    that enable further derivations in the next pass.
    """
    # Pre-compute transitive support reachability for each argument
    all_support_sources = {a for a, _ in supports}
    support_reach: dict[str, set[str]] = {}
    for src in all_support_sources:
        support_reach[src] = _transitive_support_targets(src, supports)

    # Working set: original defeats plus all derived defeats found so far
    working_defeats = set(defeats)
    all_derived: set[tuple[str, str]] = set()

    while True:
        new_derived: set[tuple[str, str]] = set()

        # Supported defeat: A supports* B, B defeats C → (A, C)
        for b, c in working_defeats:
            for a, targets in support_reach.items():
                if b in targets:
                    pair = (a, c)
                    if pair not in working_defeats:
                        new_derived.add(pair)

        # Indirect defeat: A defeats B, B supports* C → (A, C)
        for a, b in working_defeats:
            if b in support_reach:
                for c in support_reach[b]:
                    pair = (a, c)
                    if pair not in working_defeats:
                        new_derived.add(pair)

        if not new_derived:
            break

        working_defeats |= new_derived
        all_derived |= new_derived

    return all_derived


def build_argumentation_framework(
    store: ArtifactStore,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
) -> ArgumentationFramework:
    """Build a bipolar AF over active claim rows.

    Steps:
      1. Load all stances between active claims with confidence >= threshold
      2. Classify into attacks and supports
      3. Filter attacks through preferences to get defeats (Modgil 2018 Def 9)
      4. Compute derived defeats from support chains (Cayrol 2005 Def 3)
      5. Return AF with attacks (pre-preference) and defeats (post-preference + derived)

    **Design note:** Grounded extension computation uses defeat-based iteration
    with post-hoc attack-conflict-free pruning (re-iterate defense after removing
    attack-conflicting arguments). This is not a standard least fixed point of
    a single well-defined characteristic function. Modgil & Prakken 2018 expect
    the defeat relation to already encode preference information. The post-hoc
    reconciliation may diverge from standard semantics in edge cases with
    complex attack/defeat interactions.
    """
    # Load claim metadata for strength computation
    claims_by_id = store.claims_by_ids(active_claim_ids)

    # Load stances between active claims above confidence threshold
    stances = store.stances_between(active_claim_ids)

    attacks: set[tuple[str, str]] = set()
    defeats: set[tuple[str, str]] = set()
    supports: set[tuple[str, str]] = set()

    for stance in stances:
        source_id = stance["claim_id"]
        target_id = stance["target_claim_id"]
        stance_type = stance["stance_type"]
        confidence = stance.get("confidence")

        # Skip stances referencing claims not in the active set — these are
        # stale references that should not participate in the AF.
        if source_id not in claims_by_id or target_id not in claims_by_id:
            continue

        # Collect support relations for Cayrol derived defeats
        if stance_type in _SUPPORT_TYPES:
            supports.add((source_id, target_id))
            continue

        if stance_type not in _ATTACK_TYPES:
            continue

        # All attack-type stances go into attacks (pre-preference)
        attacks.add((source_id, target_id))

        # Filter through preferences to determine defeats
        if stance_type in _UNCONDITIONAL_TYPES:
            defeats.add((source_id, target_id))
        elif stance_type in _PREFERENCE_TYPES:
            attacker_claim = claims_by_id.get(source_id, {})
            target_claim = claims_by_id.get(target_id, {})
            attacker_s = claim_strength(attacker_claim)  # already returns list[float]
            target_s = claim_strength(target_claim)
            if defeat_holds(stance_type, attacker_s, target_s, comparison):
                defeats.add((source_id, target_id))

    # Compute Cayrol 2005 derived defeats from support chains
    if supports:
        derived = _cayrol_derived_defeats(defeats, supports)
        defeats |= derived

    return ArgumentationFramework(
        arguments=frozenset(active_claim_ids),
        defeats=frozenset(defeats),
        attacks=frozenset(attacks),
    )


def build_praf(
    store: ArtifactStore,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
) -> "ProbabilisticAF":
    """Build PrAF by annotating AF with opinion-derived probabilities.

    Per Li et al. (2012, Def 2): PrAF = (A, P_A, D, P_D).
    P_A from p_arg_from_claim() (default: dogmatic true).
    P_D from stance opinion columns (Jøsang 2001, Def 6: E(ω) = b + a·u).

    Steps:
      1. Call build_argumentation_framework() to get the AF
      2. Load opinion data for each stance from the store
      3. Map opinions to P_D (fallback: opinion columns → confidence → dogmatic true)
      4. Set P_A = p_arg_from_claim(claim) for each argument
      5. Return ProbabilisticAF
    """
    from propstore.praf import ProbabilisticAF, p_arg_from_claim, p_defeat_from_stance

    # Step 1: Build full AF
    af = build_argumentation_framework(store, active_claim_ids, comparison=comparison)

    # Step 2-3: Load stances and map to P_D
    claims_by_id = store.claims_by_ids(active_claim_ids)
    stances = store.stances_between(active_claim_ids)

    # Index stances by (source, target) for defeat lookup
    stance_by_pair: dict[tuple[str, str], dict] = {}
    for stance in stances:
        source_id = stance["claim_id"]
        target_id = stance["target_claim_id"]
        stance_type = stance["stance_type"]
        if stance_type in _ATTACK_TYPES:
            stance_by_pair[(source_id, target_id)] = stance

    # Build P_D for each defeat in the AF
    p_defeats: dict[tuple[str, str], "Opinion"] = {}
    for defeat in af.defeats:
        stance = stance_by_pair.get(defeat)
        if stance is not None:
            p_defeats[defeat] = p_defeat_from_stance(stance)
        else:
            # Derived defeat (Cayrol 2005) or no stance found — certain defeat
            from propstore.opinion import Opinion as _Opinion
            p_defeats[defeat] = _Opinion.dogmatic_true()

    # Step 4: P_A for each argument
    p_args: dict[str, "Opinion"] = {}
    for arg_id in af.arguments:
        claim = claims_by_id.get(arg_id, {"claim_id": arg_id})
        p_args[arg_id] = p_arg_from_claim(claim)

    return ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)


def compute_claim_graph_justified_claims(
    store: ArtifactStore,
    active_claim_ids: set[str],
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
) -> frozenset[str] | list[frozenset[str]]:
    """Compute justified active claims for the claim-graph backend.

    For grounded: returns a single frozenset (the unique grounded extension).
    For preferred/stable: returns a list of frozensets.
    """
    af = build_argumentation_framework(
        store, active_claim_ids,
        comparison=comparison,
    )

    if semantics == "grounded":
        return grounded_extension(af)
    elif semantics == "preferred":
        return [frozenset(e) for e in preferred_extensions(af)]
    elif semantics == "stable":
        return [frozenset(e) for e in stable_extensions(af)]
    else:
        raise ValueError(f"Unknown semantics: {semantics}")



def stance_summary(
    store: ArtifactStore,
    active_claim_ids: set[str],
) -> dict:
    """Summarize stances used in AF construction for render explanation.

    Returns counts, opinion statistics, and model info so the render
    layer can explain which stances were included under what policy.

    All stances participate in AF construction regardless of opinion
    uncertainty, per Li et al. (2012, Def 2) and the CLAUDE.md design
    checklist (no gates before render time). Vacuous opinions
    (Josang 2001, p.8) are counted but not pruned — filtering is
    deferred to render/resolution time.
    """
    rows = store.stances_between(active_claim_ids)

    total = 0
    included = 0
    vacuous_count = 0
    excluded_non_attack = 0
    models: set[str] = set()
    uncertainties: list[float] = []

    for row in rows:
        total += 1
        stype = row["stance_type"]
        model = row.get("resolution_model")
        opinion_u = row.get("opinion_uncertainty")

        if stype in _NON_ATTACK_TYPES:
            excluded_non_attack += 1
            continue

        included += 1
        if model:
            models.add(model)
        if opinion_u is not None:
            uncertainties.append(opinion_u)
            if opinion_u > 0.99:
                vacuous_count += 1

    result: dict = {
        "total_stances": total,
        "included_as_attacks": included,
        "vacuous_count": vacuous_count,
        "excluded_non_attack": excluded_non_attack,
        "models": sorted(models),
    }
    if uncertainties:
        result["mean_uncertainty"] = sum(uncertainties) / len(uncertainties)

    return result


def compute_consistent_beliefs(
    store: ArtifactStore,
    active_claim_ids: set[str],
) -> frozenset[str]:
    """Find maximally consistent claim subset using MaxSMT.

    Loads claims, detects conflicts via the conflict detector, computes
    claim strengths, then calls the MaxSMT resolver to find the largest
    weighted conflict-free subset.
    """
    from propstore.conflict_detector import ConflictClass, detect_conflicts
    from propstore.maxsat_resolver import resolve_conflicts
    from propstore.validate_claims import LoadedClaimFile

    if not active_claim_ids:
        return frozenset()

    # Load claim rows from DB
    claims_by_id = store.claims_by_ids(active_claim_ids)

    # Compute strengths — scalar aggregation for MaxSMT weight.
    # claim_strength returns list[float]; multi-dim strength reduced to mean.
    strengths = {
        cid: sum(dims) / len(dims)
        for cid in active_claim_ids
        if cid in claims_by_id
        for dims in [claim_strength(claims_by_id[cid])]
    }

    # Detect conflicts — build synthetic LoadedClaimFile wrappers
    # We need the claim data in the format detect_conflicts expects
    synthetic = LoadedClaimFile(
        filename="<in-memory>",
        filepath=Path("<in-memory>"),
        data={"claims": list(claims_by_id.values())},
    )

    # Build a minimal concept registry from claims
    concept_ids = {
        c.get("concept") or c.get("target_concept")
        for c in claims_by_id.values()
        if c.get("concept") or c.get("target_concept")
    }
    concept_registry = {cid: {} for cid in concept_ids if cid}

    records = detect_conflicts([synthetic], concept_registry)

    # Extract conflict pairs (only true conflicts, not phi-nodes)
    conflict_types = {ConflictClass.CONFLICT, ConflictClass.OVERLAP, ConflictClass.PARAM_CONFLICT}
    conflict_pairs = [
        (r.claim_a_id, r.claim_b_id)
        for r in records
        if r.warning_class in conflict_types
    ]

    return resolve_conflicts(conflict_pairs, strengths)
