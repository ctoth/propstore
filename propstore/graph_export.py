"""Graph export — build a KnowledgeGraph from the sidecar's relational structure.

Exports concept and claim nodes plus parameterization, relationship, stance,
and claim_of edges.  Supports DOT (via graphviz) and JSON output formats.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Mapping

from propstore.core.environment import Environment
from propstore.core.row_types import (
    coerce_claim_row,
    coerce_concept_row,
    coerce_parameterization_row,
    coerce_relationship_row,
    coerce_stance_row,
)
from propstore.world import ArtifactStore, BeliefSpace

if TYPE_CHECKING:
    from propstore.world import WorldModel


def _coerce_claim_like(claim_input):
    row_input = getattr(claim_input, "row", claim_input)
    return coerce_claim_row(row_input)


def _claim_concept_id(claim_input) -> Any:
    claim = _coerce_claim_like(claim_input)
    return claim.concept_id or claim.target_concept


def _display_claim_id(claim_input) -> str:
    claim = _coerce_claim_like(claim_input)
    logical_value = claim.primary_logical_value
    if isinstance(logical_value, str) and logical_value:
        return logical_value
    return str(claim.claim_id)


def _display_claim_id_from_store(world: ArtifactStore, claim_id: str) -> str:
    getter = getattr(world, "get_claim", None)
    if callable(getter):
        claim = getter(claim_id)
        if claim is not None:
            return _display_claim_id(claim)
    return claim_id


@dataclass
class GraphNode:
    id: str
    label: str
    node_type: str  # "concept" | "claim"
    metadata: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    edge_type: str  # "parameterization" | "relationship" | "stance" | "claim_of"
    metadata: dict = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)

    def to_dot(self) -> str:
        """Render the graph as a Graphviz DOT string."""
        import graphviz

        dot = graphviz.Digraph(format="png")

        _EDGE_COLORS = {
            "parameterization": "blue",
            "relationship": "green",
            "stance": "red",
            "claim_of": "gray",
        }

        for node in self.nodes:
            attrs: dict[str, str] = {}
            if node.node_type == "concept":
                attrs["shape"] = "box"
            else:
                attrs["shape"] = "oval"

            if node.metadata.get("status") == "conflicted":
                attrs["color"] = "red"
                attrs["penwidth"] = "2"

            dot.node(node.id, label=node.label, **attrs)

        for edge in self.edges:
            color = _EDGE_COLORS.get(edge.edge_type, "black")
            label = edge.edge_type
            if edge.metadata.get("type"):
                label = edge.metadata["type"]
            dot.edge(edge.source, edge.target, color=color, label=label)

        return dot.source

    def to_json(self) -> dict:
        """Return a JSON-serializable dict representation."""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "node_type": n.node_type,
                    "metadata": n.metadata,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "edge_type": e.edge_type,
                    "metadata": e.metadata,
                }
                for e in self.edges
            ],
        }


@dataclass(frozen=True)
class GraphExportRequest:
    bindings: Mapping[str, str]
    group_id: int | None = None


@dataclass(frozen=True)
class GraphExportReport:
    graph: KnowledgeGraph


def export_knowledge_graph(
    world: WorldModel,
    request: GraphExportRequest,
) -> GraphExportReport:
    bound = (
        world.bind(Environment(bindings=dict(request.bindings)))
        if request.bindings
        else None
    )
    return GraphExportReport(
        graph=build_knowledge_graph(world, bound=bound, group_id=request.group_id)
    )


def build_knowledge_graph(
    world: ArtifactStore,
    bound: BeliefSpace | None = None,
    group_id: int | None = None,
) -> KnowledgeGraph:
    """Build a KnowledgeGraph from the sidecar database.

    Parameters
    ----------
    world : ArtifactStore
        The artifact store backed by the sidecar database.
    bound : BeliefSpace | None
        If provided, only active claims in this belief space are included.
    group_id : int | None
        If provided, only concepts in this parameterization group are included.
    """
    graph = KnowledgeGraph()
    node_ids: set[str] = set()

    # ---- Determine which concept IDs to include ----
    allowed_concept_ids: set[str] | None = None
    if group_id is not None:
        allowed_concept_ids = world.concept_ids_for_group(group_id)

    # ---- 1. Concept nodes ----
    concept_rows = world.all_concepts()
    for row_input in concept_rows:
        row = coerce_concept_row(row_input)
        cid = str(row.concept_id)
        if allowed_concept_ids is not None and cid not in allowed_concept_ids:
            continue
        graph.nodes.append(GraphNode(
            id=cid,
            label=row.canonical_name,
            node_type="concept",
            metadata={
                "form": row.form,
                "status": row.status,
                "domain": row.domain,
            },
        ))
        node_ids.add(cid)

    # ---- 2. Claim nodes ----
    if bound is not None:
        claims = bound.active_claims()
    else:
        claims = world.claims_for(None)

    claim_rows = [_coerce_claim_like(claim) for claim in claims]

    # Filter claims to allowed concepts if group scoping is active
    if allowed_concept_ids is not None:
        claim_rows = [c for c in claim_rows if str(_claim_concept_id(c) or "") in allowed_concept_ids]

    # Determine value_of status per concept for metadata
    concept_statuses: dict[str, str] = {}
    if bound is not None:
        for cid in node_ids:
            vr = bound.value_of(cid)
            concept_statuses[cid] = vr.status

    for claim in claim_rows:
        claim_id = _display_claim_id(claim)
        concept_id = _claim_concept_id(claim)
        meta: dict[str, Any] = {
            "type": claim.claim_type,
            "value": claim.value,
            "concept_id": concept_id,
            "artifact_id": claim.artifact_id,
            "target_concept": claim.target_concept,
        }
        if bound is not None and concept_id and concept_id in concept_statuses:
            meta["status"] = concept_statuses[concept_id]

        label = claim_id
        if claim.value is not None:
            label = f"{claim_id}={claim.value}"

        graph.nodes.append(GraphNode(
            id=claim_id,
            label=label,
            node_type="claim",
            metadata=meta,
        ))
        node_ids.add(claim_id)

    # ---- 3. Parameterization edges ----
    for row_input in world.all_parameterizations():
        row = coerce_parameterization_row(row_input)
        output_id = str(row.output_concept_id)
        if output_id not in node_ids:
            continue
        input_ids = json.loads(row.concept_ids)
        for iid in input_ids:
            if iid not in node_ids:
                continue
            graph.edges.append(GraphEdge(
                source=iid,
                target=output_id,
                edge_type="parameterization",
                metadata={
                    "formula": row.formula,
                    "exactness": row.exactness,
                },
            ))

    # ---- 4. Relationship edges ----
    for row_input in world.all_relationships():
        row = coerce_relationship_row(row_input)
        src = row.source_id
        tgt = row.target_id
        if src not in node_ids or tgt not in node_ids:
            continue
        graph.edges.append(GraphEdge(
            source=src,
            target=tgt,
            edge_type="relationship",
            metadata={"type": row.relation_type},
        ))

    # ---- 5. Stance edges ----
    for row_input in world.all_claim_stances():
        row = coerce_stance_row(row_input)
        cid = _display_claim_id_from_store(world, row.claim_id)
        tid = _display_claim_id_from_store(world, row.target_claim_id)
        if cid not in node_ids or tid not in node_ids:
            continue
        graph.edges.append(GraphEdge(
            source=cid,
            target=tid,
            edge_type="stance",
            metadata={"stance_type": row.stance_type},
        ))

    # ---- 6. Claim-of edges ----
    for claim in claim_rows:
        claim_id = _display_claim_id(claim)
        concept_id = _claim_concept_id(claim)
        if concept_id and claim_id in node_ids and concept_id in node_ids:
            graph.edges.append(GraphEdge(
                source=claim_id,
                target=concept_id,
                edge_type="claim_of",
                metadata={},
            ))

    return graph
