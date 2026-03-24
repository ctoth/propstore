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
    confidence_threshold: float = 0.5,
) -> ArgumentationFramework:
    """Build a bipolar AF over active claim rows.

    Steps:
      1. Load all stances between active claims with confidence >= threshold
      2. Classify into attacks and supports
      3. Filter attacks through preferences to get defeats (Modgil 2018 Def 9)
      4. Compute derived defeats from support chains (Cayrol 2005 Def 3)
      5. Return AF with attacks (pre-preference) and defeats (post-preference + derived)
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

        if confidence is not None and confidence < confidence_threshold:
            continue

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


def compute_claim_graph_justified_claims(
    store: ArtifactStore,
    active_claim_ids: set[str],
    *,
    semantics: str = "grounded",
    comparison: str = "elitist",
    confidence_threshold: float = 0.5,
) -> frozenset[str] | list[frozenset[str]]:
    """Compute justified active claims for the claim-graph backend.

    For grounded: returns a single frozenset (the unique grounded extension).
    For preferred/stable: returns a list of frozensets.
    """
    af = build_argumentation_framework(
        store, active_claim_ids,
        comparison=comparison,
        confidence_threshold=confidence_threshold,
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
    confidence_threshold: float = 0.5,
) -> dict:
    """Summarize stances used in AF construction for render explanation.

    Returns counts and model info so the render layer can explain
    which stances were included under what policy.
    """
    rows = store.stances_between(active_claim_ids)

    total = 0
    included = 0
    excluded_by_threshold = 0
    excluded_non_attack = 0
    models: set[str] = set()

    for row in rows:
        total += 1
        stype = row["stance_type"]
        conf = row.get("confidence")
        model = row.get("resolution_model")

        if stype in _NON_ATTACK_TYPES:
            excluded_non_attack += 1
            continue
        if conf is not None and conf < confidence_threshold:
            excluded_by_threshold += 1
            continue
        included += 1
        if model:
            models.add(model)

    return {
        "total_stances": total,
        "included_as_attacks": included,
        "excluded_by_threshold": excluded_by_threshold,
        "excluded_non_attack": excluded_non_attack,
        "confidence_threshold": confidence_threshold,
        "models": sorted(models),
    }


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
