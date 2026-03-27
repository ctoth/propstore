"""Claim-graph argumentation backend.

This module does not build full structured ASPIC+ arguments. The "arguments"
here are active claim rows, preferences come from heuristic claim metadata,
and conditions only decide which claims are active before AF construction.
The result is a claim-graph backend inspired by Dung and ASPIC+ ideas.
"""

from __future__ import annotations

from pathlib import Path

from propstore.bipolar import BipolarArgumentationFramework, cayrol_derived_defeats as _cayrol_derived_defeats_impl
from propstore.core.analyzers import (
    analyze_claim_graph,
    build_praf_from_shared_input,
    shared_analyzer_input_from_store,
)
from propstore.dung import ArgumentationFramework
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
    for left_id, right_id in supports:
        if left_id == source and right_id not in visited:
            targets.add(right_id)
            targets |= _transitive_support_targets(right_id, supports, visited)
    return targets


def _cayrol_derived_defeats(
    defeats: set[tuple[str, str]],
    supports: set[tuple[str, str]],
) -> set[tuple[str, str]]:
    """Compatibility wrapper for Cayrol 2005 derived defeats."""
    return set(_cayrol_derived_defeats_impl(frozenset(defeats), frozenset(supports)))


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
    shared = shared_analyzer_input_from_store(
        store,
        active_claim_ids,
        comparison=comparison,
    )
    return shared.argumentation_framework


def build_bipolar_framework(
    store: ArtifactStore,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
) -> BipolarArgumentationFramework:
    """Build an explicit Cayrol-style bipolar framework over active claim rows."""
    shared = shared_analyzer_input_from_store(
        store,
        active_claim_ids,
        comparison=comparison,
    )
    return shared.bipolar_framework


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
    shared = shared_analyzer_input_from_store(
        store,
        active_claim_ids,
        comparison=comparison,
    )
    return build_praf_from_shared_input(shared)


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
    result = analyze_claim_graph(
        shared_analyzer_input_from_store(
            store,
            active_claim_ids,
            comparison=comparison,
        ),
        semantics=semantics,
    )
    accepted = [frozenset(extension.accepted_claim_ids) for extension in result.extensions]
    if semantics in {"grounded", "legacy_grounded", "hybrid_grounded", "hybrid-grounded", "bipolar-grounded"}:
        return accepted[0] if accepted else frozenset()
    return accepted



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
