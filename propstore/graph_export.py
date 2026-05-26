"""KnowledgeGraph rendering and export request shells."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Mapping

from propstore.core.environment import Environment

if TYPE_CHECKING:
    from propstore.world.model import WorldQuery


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
    world: WorldQuery,
    request: GraphExportRequest,
) -> GraphExportReport:
    from propstore.world.graph_projection import project_knowledge_graph

    bound = (
        world.bind(Environment(bindings=dict(request.bindings)))
        if request.bindings
        else None
    )
    return GraphExportReport(
        graph=project_knowledge_graph(world, bound=bound, group_id=request.group_id)
    )
