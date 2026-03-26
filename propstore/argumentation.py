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
from propstore.probabilistic_relations import (
    ClaimGraphRelations,
    ProbabilisticRelation,
    relation_from_row,
    relation_map,
)
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

        # Filter self-loops: derived self-defeats (A,A) are degenerate —
        # a self-defeating argument is already excluded from all admissible
        # extensions by Dung 1995 Def 6 (conflict-free). Allowing self-loops
        # to seed further derivation creates spurious defeats: e.g.
        # A defeats A (self), A supports B → derived (A,B). This conflates
        # structural impossibility with directed attack.
        new_derived = {(a, c) for a, c in new_derived if a != c}

        if not new_derived:
            break

        working_defeats |= new_derived
        all_derived |= new_derived

    return {(a, c) for a, c in all_derived if a != c}


def _collect_claim_graph_relations(
    store: ArtifactStore,
    active_claim_ids: set[str],
    *,
    comparison: str,
) -> tuple[dict[str, dict], list[dict], ClaimGraphRelations]:
    """Collect primitive and derived graph relations for active claims."""
    from propstore.praf import p_relation_from_stance

    claims_by_id = store.claims_by_ids(active_claim_ids)
    stances = store.stances_between(active_claim_ids)

    # --- Synthesize rebuts from conflict records (Phase 2) ---
    # Conflicts represent structural value disagreements detected by the
    # conflict detector. When no LLM-classified stance covers a conflict
    # pair, we inject a symmetric "rebuts" stance with a vacuous opinion
    # (b=0, d=0, u=1, a=0.5) — honest ignorance per Jøsang 2001 p.8.
    # Synthetic stances are ephemeral: generated at render time, never
    # persisted. Real stances always take precedence (Pollock 1987 p.485).
    _REAL_CONFLICT_CLASSES = {"CONFLICT", "OVERLAP", "PARAM_CONFLICT"}
    try:
        all_conflicts = store.conflicts()
    except (AttributeError, TypeError):
        all_conflicts = []

    existing_stance_pairs = {
        (s["claim_id"], s["target_claim_id"]) for s in stances
    }
    # Undirected pairs with any real stance between them.
    existing_stance_undirected: set[frozenset[str]] = {
        frozenset({s["claim_id"], s["target_claim_id"]}) for s in stances
    }
    # Undirected pairs with a real attack-type stance.
    existing_attack_undirected: set[frozenset[str]] = {
        frozenset({s["claim_id"], s["target_claim_id"]})
        for s in stances if s["stance_type"] in _ATTACK_TYPES
    }
    # Claims that participate in any real stance (as source or target).
    # Used to detect when an LLM has classified a claim with other claims
    # but intentionally omitted a stance for a particular pair.
    claims_with_stances: set[str] = set()
    for s in stances:
        claims_with_stances.add(s["claim_id"])
        claims_with_stances.add(s["target_claim_id"])

    for conflict in all_conflicts:
        wc = conflict.get("warning_class", "")
        if wc not in _REAL_CONFLICT_CLASSES:
            continue
        a_id = conflict["claim_a_id"]
        b_id = conflict["claim_b_id"]
        if a_id not in active_claim_ids or b_id not in active_claim_ids:
            continue
        pair_key = frozenset({a_id, b_id})
        # If a real attack stance covers this pair → fully handled, skip.
        if pair_key in existing_attack_undirected:
            continue
        # If the pair has a non-attack stance: the LLM classified the
        # pair but not as an attack. Synthesize only the uncovered direction
        # (the LLM's classification in the covered direction takes precedence).
        if pair_key in existing_stance_undirected:
            for src, tgt in [(a_id, b_id), (b_id, a_id)]:
                if (src, tgt) not in existing_stance_pairs:
                    stances.append({
                        "claim_id": src,
                        "target_claim_id": tgt,
                        "stance_type": "rebuts",
                        "confidence": 0.5,
                        "opinion_belief": 0.0,
                        "opinion_disbelief": 0.0,
                        "opinion_uncertainty": 1.0,
                        "opinion_base_rate": 0.5,
                    })
            continue
        # No stance between this pair at all. If either claim participates
        # in stances with OTHER claims, the LLM had the opportunity to
        # classify this pair and chose not to — skip. Only synthesize for
        # truly unclassified (orphan) claim pairs.
        if a_id in claims_with_stances or b_id in claims_with_stances:
            continue
        # Synthesize two directed stances (a→b and b→a).
        for src, tgt in [(a_id, b_id), (b_id, a_id)]:
            stances.append({
                "claim_id": src,
                "target_claim_id": tgt,
                "stance_type": "rebuts",
                "confidence": 0.5,
                "opinion_belief": 0.0,
                "opinion_disbelief": 0.0,
                "opinion_uncertainty": 1.0,
                "opinion_base_rate": 0.5,
            })

    attacks: set[tuple[str, str]] = set()
    direct_defeats: set[tuple[str, str]] = set()
    supports: set[tuple[str, str]] = set()
    attack_relations: list[ProbabilisticRelation] = []
    support_relations: list[ProbabilisticRelation] = []
    direct_defeat_relations: list[ProbabilisticRelation] = []

    for stance in stances:
        source_id = stance["claim_id"]
        target_id = stance["target_claim_id"]
        stance_type = stance["stance_type"]

        if source_id not in claims_by_id or target_id not in claims_by_id:
            continue

        if stance_type in _SUPPORT_TYPES:
            supports.add((source_id, target_id))
            support_relations.append(
                relation_from_row(
                    kind="support",
                    source=source_id,
                    target=target_id,
                    opinion=p_relation_from_stance(stance),
                    row=stance,
                )
            )
            continue

        if stance_type not in _ATTACK_TYPES:
            continue

        attacks.add((source_id, target_id))
        attack_opinion = p_relation_from_stance(stance)
        attack_relations.append(
            relation_from_row(
                kind="attack",
                source=source_id,
                target=target_id,
                opinion=attack_opinion,
                row=stance,
            )
        )

        if stance_type in _UNCONDITIONAL_TYPES:
            direct_defeats.add((source_id, target_id))
            direct_defeat_relations.append(
                relation_from_row(
                    kind="direct_defeat",
                    source=source_id,
                    target=target_id,
                    opinion=attack_opinion,
                    row=stance,
                )
            )
        elif stance_type in _PREFERENCE_TYPES:
            attacker_claim = claims_by_id.get(source_id, {})
            target_claim = claims_by_id.get(target_id, {})
            attacker_s = claim_strength(attacker_claim)
            target_s = claim_strength(target_claim)
            if defeat_holds(stance_type, attacker_s, target_s, comparison):
                direct_defeats.add((source_id, target_id))
                direct_defeat_relations.append(
                    relation_from_row(
                        kind="direct_defeat",
                        source=source_id,
                        target=target_id,
                        opinion=attack_opinion,
                        row=stance,
                    )
                )

    return claims_by_id, stances, ClaimGraphRelations(
        arguments=frozenset(active_claim_ids),
        attacks=frozenset(attacks),
        direct_defeats=frozenset(direct_defeats),
        supports=frozenset(supports),
        attack_relations=tuple(attack_relations),
        support_relations=tuple(support_relations),
        direct_defeat_relations=tuple(direct_defeat_relations),
    )


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

    **Design note:** When attacks and defeats diverge, this produces a hybrid
    attack/defeat framework rather than a standard Dung AF. Grounded evaluation
    must therefore avoid synthesizing a post-hoc "grounded" set by pruning a
    defeat-only fixpoint; that can yield non-complete results.
    """
    _, _, relations = _collect_claim_graph_relations(
        store,
        active_claim_ids,
        comparison=comparison,
    )
    defeats = set(relations.direct_defeats)
    if relations.supports and relations.direct_defeats:
        defeats |= _cayrol_derived_defeats(set(relations.direct_defeats), set(relations.supports))

    return ArgumentationFramework(
        arguments=frozenset(active_claim_ids),
        defeats=frozenset(defeats),
        attacks=relations.attacks,
    )


def build_praf(
    store: ArtifactStore,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
) -> "ProbabilisticAF":
    """Build a primitive-relation probabilistic model over the claim graph.

    P_A comes from p_arg_from_claim() (default: dogmatic true).
    Primitive attacks and supports carry opinion-derived existence probabilities.
    Direct defeats are the primitive semantic relation after preference filtering.
    Cayrol derived defeats remain world-derived consequences and are not stored
    as authoritative probabilistic inputs.

    Steps:
      1. Collect primitive attacks/supports and direct defeats
      2. Build the semantic AF envelope with Cayrol closure for deterministic evaluation
      3. Attach provenance-bearing primitive relation records
      4. Set P_A for each argument
      5. Return ProbabilisticAF
    """
    from propstore.praf import ProbabilisticAF, p_arg_from_claim

    claims_by_id, _, relations = _collect_claim_graph_relations(
        store,
        active_claim_ids,
        comparison=comparison,
    )

    derived_defeats = (
        _cayrol_derived_defeats(set(relations.direct_defeats), set(relations.supports))
        if relations.supports and relations.direct_defeats
        else set()
    )
    af = ArgumentationFramework(
        arguments=frozenset(active_claim_ids),
        defeats=frozenset(set(relations.direct_defeats) | derived_defeats),
        attacks=relations.attacks,
    )
    p_defeats = relation_map(relations.direct_defeat_relations)

    # Step 4: P_A for each argument
    p_args: dict[str, "Opinion"] = {}
    for arg_id in af.arguments:
        claim = claims_by_id.get(arg_id, {"claim_id": arg_id})
        p_args[arg_id] = p_arg_from_claim(claim)

    return ProbabilisticAF(
        framework=af,
        p_args=p_args,
        p_defeats=p_defeats,
        p_attacks=relation_map(relations.attack_relations),
        supports=relations.supports,
        p_supports=relation_map(relations.support_relations),
        base_defeats=relations.direct_defeats,
        attack_relations=relations.attack_relations,
        support_relations=relations.support_relations,
        direct_defeat_relations=relations.direct_defeat_relations,
    )


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
