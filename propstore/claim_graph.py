"""Store-based claim-graph entrypoints.

This module is not the general argumentation core. It owns the store-based
entrypoints for the claim-graph backend and delegates shared orchestration to
`propstore.core.analyzers`.
"""

from __future__ import annotations

from propstore.core.analyzers import (
    analyze_claim_graph,
    shared_analyzer_input_from_store,
)
from argumentation.dung import ArgumentationFramework
from propstore.world.types import (
    ArgumentationSemantics,
    WorldStore,
    ReasoningBackend,
    validate_backend_semantics,
)


def build_argumentation_framework(
    store: WorldStore,
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


def compute_claim_graph_justified_claims(
    store: WorldStore,
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
    canonical_active_ids = {
        store.resolve_claim(claim_id) or claim_id
        for claim_id in active_claim_ids
    }
    display_ids_by_canonical = {
        (store.resolve_claim(claim_id) or claim_id): claim_id
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
