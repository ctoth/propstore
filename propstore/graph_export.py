"""Graph export — render the world store as a Graphviz/JSON knowledge graph.

A :class:`KnowledgeGraph` is a presentation projection of the corpus: concept and
claim nodes plus ``parameterization`` / ``relationship`` / ``stance`` / ``claim_of``
edges, rendered to DOT (via the core ``graphviz`` dependency) or to a plain JSON
dict. It reads the ONE canonical charters the
:class:`~propstore.core.environment.WorldStore` exposes — ``Concept`` / ``Claim``
charters plus the graph-carrier
:class:`~propstore.core.graph_types.RelationEdge` /
:class:`~propstore.core.graph_types.ParameterizationEdge` — so there is no second
``*Row`` spelling and no ``coerce`` round-trip (CLAUDE.md substrate boundary).

The export is render-layer: an optional :class:`~propstore.world.BoundWorld`
filters claims to the active set under an environment and marks claims whose
concept resolves to a conflicted value, and an optional ``group_id`` scopes the
concepts to one parameterization group. The build never gates on status — every
authored node reaches the graph; the binding only decides which claims are active.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from propstore.core.environment import Environment
from propstore.core.id_types import ConceptId, to_concept_id
from propstore.families.claims import Claim

if TYPE_CHECKING:
    from collections.abc import Mapping

    from propstore.world import BoundWorld, WorldQuery


def _claim_concept_id(claim: Claim) -> ConceptId | None:
    """The concept a claim's value is about: output, else target, else first ref."""

    for candidate in (claim.output_concept, claim.target_concept, *claim.concepts):
        if candidate:
            return to_concept_id(candidate)
    return None


@dataclass
class GraphNode:
    id: str
    label: str
    node_type: str  # "concept" | "claim"
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])


@dataclass
class GraphEdge:
    source: str
    target: str
    edge_type: str  # "parameterization" | "relationship" | "stance" | "claim_of"
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])


_EDGE_COLORS = {
    "parameterization": "blue",
    "relationship": "green",
    "stance": "red",
    "claim_of": "gray",
}


def _dot_quote(value: str) -> str:
    """Quote a string as a DOT identifier/attribute value."""

    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _dot_attributes(attributes: list[tuple[str, str]]) -> str:
    if not attributes:
        return ""
    body = ", ".join(f"{key}={_dot_quote(value)}" for key, value in attributes)
    return f" [{body}]"


@dataclass
class KnowledgeGraph:
    nodes: list[GraphNode] = field(default_factory=list[GraphNode])
    edges: list[GraphEdge] = field(default_factory=list[GraphEdge])

    def to_dot(self) -> str:
        """Render the graph as a Graphviz DOT (``digraph``) string.

        The emitted string is valid DOT consumable by the ``graphviz`` core
        dependency (``graphviz.Source(graph.to_dot()).render(...)``); it is built
        from the stdlib here so the export carries no untyped third-party surface.
        """

        lines = ["digraph {"]
        for node in self.nodes:
            attributes: list[tuple[str, str]] = [
                ("label", node.label),
                ("shape", "box" if node.node_type == "concept" else "oval"),
            ]
            if node.metadata.get("status") == "conflicted":
                attributes.append(("color", "red"))
                attributes.append(("penwidth", "2"))
            lines.append(f"  {_dot_quote(node.id)}{_dot_attributes(attributes)}")

        for edge in self.edges:
            color = _EDGE_COLORS.get(edge.edge_type, "black")
            label = str(edge.metadata.get("type") or edge.edge_type)
            edge_attributes: list[tuple[str, str]] = [("color", color), ("label", label)]
            lines.append(
                f"  {_dot_quote(edge.source)} -> {_dot_quote(edge.target)}"
                f"{_dot_attributes(edge_attributes)}"
            )

        lines.append("}")
        return "\n".join(lines)

    def to_json(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""

        return {
            "nodes": [
                {
                    "id": node.id,
                    "label": node.label,
                    "node_type": node.node_type,
                    "metadata": node.metadata,
                }
                for node in self.nodes
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "edge_type": edge.edge_type,
                    "metadata": edge.metadata,
                }
                for edge in self.edges
            ],
        }


@dataclass(frozen=True)
class GraphExportRequest:
    bindings: Mapping[str, object] = field(default_factory=dict[str, object])
    group_id: int | None = None


@dataclass(frozen=True)
class GraphExportReport:
    graph: KnowledgeGraph


def export_knowledge_graph(
    world: WorldQuery,
    request: GraphExportRequest,
) -> GraphExportReport:
    """Owner-layer entry: build the graph under an optional binding/group scope."""

    bound = (
        world.bind(Environment(bindings=dict(request.bindings)))
        if request.bindings
        else None
    )
    return GraphExportReport(
        graph=build_knowledge_graph(world, bound=bound, group_id=request.group_id)
    )


def build_knowledge_graph(
    world: WorldQuery,
    bound: BoundWorld | None = None,
    group_id: int | None = None,
) -> KnowledgeGraph:
    """Build a :class:`KnowledgeGraph` from the world store's charters.

    Parameters
    ----------
    world:
        The repo-backed world reader.
    bound:
        If given, only claims active in this belief space are included, and a
        claim whose concept resolves to a conflicted value is marked
        ``status="conflicted"``.
    group_id:
        If given, only concepts in this parameterization group are included.
    """

    graph = KnowledgeGraph()
    node_ids: set[str] = set()

    allowed_concept_ids = (
        world.concept_ids_for_group(group_id) if group_id is not None else None
    )

    # ---- 1. Concept nodes ----
    for concept in world.all_concepts():
        cid = str(concept.concept_id)
        if allowed_concept_ids is not None and cid not in allowed_concept_ids:
            continue
        graph.nodes.append(
            GraphNode(
                id=cid,
                label=concept.canonical_name,
                node_type="concept",
                metadata={
                    "status": concept.status.value,
                    "definition": concept.definition,
                },
            )
        )
        node_ids.add(cid)

    # ---- 2. Claim nodes (filtered to the active set when bound) ----
    claims = list(world.claims_for(None))
    if bound is not None:
        active_ids = {str(claim.claim_id) for claim in bound.active_claims()}
        claims = [claim for claim in claims if str(claim.claim_id) in active_ids]
    if allowed_concept_ids is not None:
        claims = [
            claim
            for claim in claims
            if str(_claim_concept_id(claim) or "") in allowed_concept_ids
        ]

    concept_statuses: dict[str, str] = {}
    if bound is not None:
        for cid in node_ids:
            concept_statuses[cid] = str(bound.value_of(cid).status)

    for claim in claims:
        claim_id = str(claim.claim_id)
        concept_id = _claim_concept_id(claim)
        metadata: dict[str, Any] = {
            "type": None if claim.claim_type is None else claim.claim_type.value,
            "value": claim.value,
            "concept_id": None if concept_id is None else str(concept_id),
        }
        if concept_id is not None and str(concept_id) in concept_statuses:
            metadata["status"] = concept_statuses[str(concept_id)]
        label = claim_id if claim.value is None else f"{claim_id}={claim.value}"
        graph.nodes.append(
            GraphNode(id=claim_id, label=label, node_type="claim", metadata=metadata)
        )
        node_ids.add(claim_id)

    # ---- 3. Parameterization edges ----
    for edge in world.all_parameterizations():
        output_id = str(edge.output_concept_id)
        if output_id not in node_ids:
            continue
        for input_id in edge.input_concept_ids:
            iid = str(input_id)
            if iid not in node_ids:
                continue
            graph.edges.append(
                GraphEdge(
                    source=iid,
                    target=output_id,
                    edge_type="parameterization",
                    metadata={
                        "formula": edge.formula,
                        "exactness": (
                            None if edge.exactness is None else edge.exactness.value
                        ),
                    },
                )
            )

    # ---- 4. Concept relationship edges ----
    for edge in world.all_relationships():
        if edge.source_id not in node_ids or edge.target_id not in node_ids:
            continue
        graph.edges.append(
            GraphEdge(
                source=edge.source_id,
                target=edge.target_id,
                edge_type="relationship",
                metadata={"type": edge.relation_type.value},
            )
        )

    # ---- 5. Stance edges ----
    for stance in world.all_claim_stances():
        if stance.source_claim_id is None or stance.target_claim_id is None:
            continue
        source = str(stance.source_claim_id)
        target = str(stance.target_claim_id)
        if source not in node_ids or target not in node_ids:
            continue
        graph.edges.append(
            GraphEdge(
                source=source,
                target=target,
                edge_type="stance",
                metadata={
                    "stance_type": (
                        None if stance.stance_type is None else stance.stance_type.value
                    )
                },
            )
        )

    # ---- 6. Claim-of edges ----
    for claim in claims:
        claim_id = str(claim.claim_id)
        concept_id = _claim_concept_id(claim)
        if concept_id is not None and str(concept_id) in node_ids and claim_id in node_ids:
            graph.edges.append(
                GraphEdge(
                    source=claim_id,
                    target=str(concept_id),
                    edge_type="claim_of",
                    metadata={},
                )
            )

    return graph


__all__ = [
    "GraphEdge",
    "GraphExportReport",
    "GraphExportRequest",
    "GraphNode",
    "KnowledgeGraph",
    "build_knowledge_graph",
    "export_knowledge_graph",
]
