"""World graph projection from family records into renderable graph records."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from quire.projections import (
    ArtifactIdentity,
    GraphEdgeProjection,
    graph_node_projection,
)

from propstore.core.environment import WorldStore
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.claims.declaration import CLAIM_CORE_CHARTER, Claim
from propstore.families.concepts.declaration import CONCEPT_CHARTER, Parameterization
from propstore.graph_export import GraphEdge, GraphNode, KnowledgeGraph
from propstore.world.types import BeliefSpace


def project_knowledge_graph(
    world: WorldStore,
    bound: BeliefSpace | None = None,
    group_id: int | None = None,
) -> KnowledgeGraph:
    graph = KnowledgeGraph()
    node_ids: set[str] = set()

    allowed_concept_ids: set[str] | None = None
    if group_id is not None:
        allowed_concept_ids = world.concept_ids_for_group(group_id)

    for concept in world.all_concepts():
        projection = graph_node_projection(CONCEPT_CHARTER, concept)
        concept_id = projection.identity.identity
        if allowed_concept_ids is not None and concept_id not in allowed_concept_ids:
            continue
        graph.nodes.append(
            GraphNode(
                id=concept_id,
                label=projection.label,
                node_type="concept",
                metadata=dict(projection.metadata),
            )
        )
        node_ids.add(concept_id)

    claims = list(
        bound.active_claims() if bound is not None else world.claims_for(None)
    )
    if allowed_concept_ids is not None:
        claims = [
            claim
            for claim in claims
            if str(claim_projection_concept_id(claim) or "") in allowed_concept_ids
        ]

    concept_statuses: dict[str, str] = {}
    if bound is not None:
        for concept_id in node_ids:
            concept_statuses[concept_id] = bound.value_of(concept_id).status

    claim_display_ids: dict[str, str] = {}
    for claim in claims:
        projection = graph_node_projection(CLAIM_CORE_CHARTER, claim)
        display_id = claim_projection_display_id(claim)
        claim_display_ids[projection.identity.identity] = display_id
        concept_id = claim_projection_concept_id(claim)
        metadata: dict[str, Any] = dict(projection.metadata)
        metadata["concept_id"] = concept_id
        metadata["artifact_id"] = projection.identity.identity
        if bound is not None and concept_id and concept_id in concept_statuses:
            metadata["status"] = concept_statuses[concept_id]
        graph.nodes.append(
            GraphNode(
                id=display_id,
                label=display_id,
                node_type="claim",
                metadata=metadata,
            )
        )
        node_ids.add(display_id)

    for edge in _parameterization_edges(world.all_parameterizations()):
        _append_edge(graph, edge, node_ids)

    for row in world.all_relationships():
        _append_edge(
            graph,
            GraphEdgeProjection(
                source=ArtifactIdentity("concept", str(row.source_id)),
                target_family="concept",
                target_identity=str(row.target_id),
                edge_type="relationship",
                field="target_id",
                foreign_key="relation_target",
                metadata={"type": row.relation_type},
            ),
            node_ids,
        )

    for row in world.all_claim_stances():
        source_id = claim_display_ids.get(str(row.claim_id), str(row.claim_id))
        target_id = claim_display_ids.get(
            str(row.target_claim_id), str(row.target_claim_id)
        )
        _append_edge(
            graph,
            GraphEdgeProjection(
                source=ArtifactIdentity("claim", source_id),
                target_family="claim",
                target_identity=target_id,
                edge_type="stance",
                field="target_claim_id",
                foreign_key="stance_target",
                metadata={"stance_type": row.stance_type},
            ),
            node_ids,
        )

    for claim in claims:
        claim_id = claim_projection_display_id(claim)
        concept_id = claim_projection_concept_id(claim)
        if concept_id:
            _append_edge(
                graph,
                GraphEdgeProjection(
                    source=ArtifactIdentity("claim", claim_id),
                    target_family="concept",
                    target_identity=str(concept_id),
                    edge_type="claim_of",
                    field="concept_id",
                    foreign_key="claim_concept",
                ),
                node_ids,
            )

    return graph


def claim_projection_concept_id(claim: Claim) -> Any:
    for role in (ClaimConceptLinkRole.OUTPUT, ClaimConceptLinkRole.TARGET):
        for link in claim.concept_links:
            if link.role is role:
                return link.concept_id
    return claim.target_concept


def claim_projection_display_id(claim: Claim) -> str:
    if claim.primary_logical_id:
        return claim.primary_logical_id.split(":", 1)[-1]
    return str(claim.id)


def _parameterization_edges(
    parameterizations: Iterable[Parameterization],
) -> Iterable[GraphEdgeProjection]:
    for row in parameterizations:
        output_id = str(row.output_concept_id)
        for input_id in row.input_concept_ids:
            yield GraphEdgeProjection(
                source=ArtifactIdentity("concept", input_id),
                target_family="concept",
                target_identity=output_id,
                edge_type="parameterization",
                field="input_concept_ids",
                foreign_key="parameterization_input",
                metadata={
                    "formula": row.formula,
                    "exactness": row.exactness,
                },
            )


def _append_edge(
    graph: KnowledgeGraph,
    edge: GraphEdgeProjection,
    node_ids: set[str],
) -> None:
    source_id = edge.source.identity
    target_id = edge.target_identity
    if source_id not in node_ids or target_id not in node_ids:
        return
    graph.edges.append(
        GraphEdge(
            source=source_id,
            target=target_id,
            edge_type=edge.edge_type,
            metadata=dict(edge.metadata),
        )
    )
