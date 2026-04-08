"""Store-based claim-graph and PrAF entrypoints.

This module is not the general argumentation core. It owns the store-based
entrypoints for the claim-graph backend and PrAF construction, while
delegating shared orchestration to `propstore.core.analyzers`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from propstore.core.analyzers import (
    analyze_claim_graph,
    build_praf_from_shared_input,
    shared_analyzer_input_from_store,
)
from propstore.core.relation_types import ATTACK_TYPES, NON_ATTACK_TYPES, SUPPORT_TYPES
from propstore.dung import ArgumentationFramework
from propstore.world.types import (
    ArgumentationSemantics,
    ArtifactStore,
    ReasoningBackend,
    validate_backend_semantics,
)

if TYPE_CHECKING:
    from propstore.praf import ProbabilisticAF

_ATTACK_TYPES = ATTACK_TYPES
_NON_ATTACK_TYPES = NON_ATTACK_TYPES
_SUPPORT_TYPES = SUPPORT_TYPES


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
    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.CLAIM_GRAPH,
        semantics,
    )
    resolver = getattr(store, "resolve_claim", None)
    canonical_active_ids = {
        (resolver(claim_id) or claim_id)
        if callable(resolver)
        else claim_id
        for claim_id in active_claim_ids
    }
    display_ids_by_canonical = {
        (
            (resolver(claim_id) or claim_id)
            if callable(resolver)
            else claim_id
        ): claim_id
        for claim_id in active_claim_ids
    }
    result = analyze_claim_graph(
        shared_analyzer_input_from_store(
            store,
            canonical_active_ids,
            comparison=comparison,
        ),
        semantics=normalized_semantics,
    )
    accepted = [
        frozenset(
            display_ids_by_canonical.get(claim_id, claim_id)
            for claim_id in extension.accepted_claim_ids
        )
        for extension in result.extensions
    ]
    if normalized_semantics in {
        ArgumentationSemantics.GROUNDED,
    }:
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
