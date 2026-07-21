"""Store-based claim-graph entrypoints.

This module is not the general argumentation core. It owns the store-based
entrypoints for the claim-graph backend and delegates the shared assembly/math to
:mod:`propstore.core.analyzers`. The store surface and reasoning enums come from
``core`` (the world layer re-exports them later); this module does not import the
world layer.
"""

from __future__ import annotations

from argumentation.core.dung import ArgumentationFramework

from propstore.core.analyzers import (
    analyze_claim_graph,
    shared_analyzer_input_from_store,
)
from propstore.core.environment import WorldStore
from propstore.core.reasoning import (
    ArgumentationSemantics,
    ReasoningBackend,
    validate_backend_semantics,
)


def build_argumentation_framework(
    store: WorldStore,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
) -> ArgumentationFramework:
    """Build the claim-graph argumentation framework over active claims.

    The framework carries pre-preference attacks and post-preference (plus
    Cayrol-derived) defeats; grounded evaluation must reason over both rather than
    pruning a defeat-only fixpoint (Modgil & Prakken 2018; Cayrol & Lagasquie 2005).
    """

    shared = shared_analyzer_input_from_store(
        store, active_claim_ids, comparison=comparison
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

    Grounded returns the single grounded extension; preferred/stable return the
    list of extensions. Claim ids are resolved through the store so the returned
    sets are in the caller's display-id space.
    """

    _, normalized_semantics = validate_backend_semantics(
        ReasoningBackend.CLAIM_GRAPH,
        semantics,
    )
    canonical_active_ids = {
        store.resolve_claim(claim_id) or claim_id for claim_id in active_claim_ids
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
        semantics=normalized_semantics.value,
    )
    accepted = [
        frozenset(
            display_ids_by_canonical.get(claim_id, claim_id)
            for claim_id in extension.accepted_claim_ids
        )
        for extension in result.extensions
    ]
    if normalized_semantics is ArgumentationSemantics.GROUNDED:
        return accepted[0] if accepted else frozenset()
    return accepted


__all__ = ["build_argumentation_framework", "compute_claim_graph_justified_claims"]
