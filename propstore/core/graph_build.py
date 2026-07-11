"""Build a compiled world graph without lowering canonical semantic objects."""

from __future__ import annotations

from propstore.core.environment import (
    ClaimCatalogStore,
    ClaimStanceInventoryStore,
    ConceptCatalogStore,
    ConflictStore,
    ParameterizationCatalogStore,
    RelationshipCatalogStore,
    StanceStore,
)
from propstore.core.graph_types import CompiledWorldGraph


def build_compiled_world_graph(store: object) -> CompiledWorldGraph:
    """Collect canonical charters, conflicts, and graph-native mechanics."""

    if not isinstance(store, ConceptCatalogStore):
        raise TypeError("build_compiled_world_graph requires all_concepts()")
    if not isinstance(store, ClaimCatalogStore):
        raise TypeError("build_compiled_world_graph requires claims_for()")
    if not isinstance(store, ParameterizationCatalogStore):
        raise TypeError("build_compiled_world_graph requires all_parameterizations()")
    if not isinstance(store, ConflictStore):
        raise TypeError("build_compiled_world_graph requires conflicts()")

    claims = tuple(store.claims_for(None))
    claim_ids = {claim.claim_id for claim in claims}
    if isinstance(store, ClaimStanceInventoryStore):
        stances = tuple(store.all_claim_stances())
    elif isinstance(store, StanceStore):
        stances = tuple(store.stances_between(claim_ids))
    else:
        raise TypeError(
            "build_compiled_world_graph requires all_claim_stances() or stances_between()"
        )

    return CompiledWorldGraph(
        concepts=tuple(store.all_concepts()),
        claims=claims,
        relations=(
            tuple(store.all_relationships())
            if isinstance(store, RelationshipCatalogStore)
            else ()
        ),
        parameterizations=tuple(store.all_parameterizations()),
        stances=stances,
        conflicts=tuple(store.conflicts()),
    )


__all__ = ["build_compiled_world_graph"]
