"""Graph export — build a KnowledgeGraph from the sidecar's relational structure.

Exports concept and claim nodes plus parameterization, relationship, stance,
and claim_of edges.  Supports DOT (via graphviz) and JSON output formats.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from compiler.world_model import BoundWorld, WorldModel


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


def build_knowledge_graph(
    world: WorldModel,
    bound: BoundWorld | None = None,
    group_id: int | None = None,
) -> KnowledgeGraph:
    """Build a KnowledgeGraph from the sidecar database.

    Parameters
    ----------
    world : WorldModel
        The world model backed by the sidecar database.
    bound : BoundWorld | None
        If provided, only active claims under these bindings are included.
    group_id : int | None
        If provided, only concepts in this parameterization group are included.
    """
    graph = KnowledgeGraph()
    node_ids: set[str] = set()

    # ---- Determine which concept IDs to include ----
    allowed_concept_ids: set[str] | None = None
    if group_id is not None and world._has_table("parameterization_group"):
        rows = world._conn.execute(
            "SELECT concept_id FROM parameterization_group WHERE group_id = ?",
            (group_id,),
        ).fetchall()
        allowed_concept_ids = {r["concept_id"] for r in rows}

    # ---- 1. Concept nodes ----
    concept_rows = world._conn.execute("SELECT * FROM concept").fetchall()
    for row in concept_rows:
        cid = row["id"]
        if allowed_concept_ids is not None and cid not in allowed_concept_ids:
            continue
        graph.nodes.append(GraphNode(
            id=cid,
            label=row["canonical_name"],
            node_type="concept",
            metadata={
                "form": row["form"],
                "status": row["status"],
                "domain": row["domain"],
            },
        ))
        node_ids.add(cid)

    # ---- 2. Claim nodes ----
    if bound is not None:
        claims = bound.active_claims()
    else:
        claims = world.claims_for(None)

    # Filter claims to allowed concepts if group scoping is active
    if allowed_concept_ids is not None:
        claims = [c for c in claims if c.get("concept_id") in allowed_concept_ids]

    # Determine value_of status per concept for metadata
    concept_statuses: dict[str, str] = {}
    if bound is not None:
        for cid in node_ids:
            vr = bound.value_of(cid)
            concept_statuses[cid] = vr.status

    for claim in claims:
        claim_id = claim["id"]
        concept_id = claim.get("concept_id")
        meta: dict[str, Any] = {
            "type": claim.get("type"),
            "value": claim.get("value"),
            "concept_id": concept_id,
        }
        if bound is not None and concept_id and concept_id in concept_statuses:
            meta["status"] = concept_statuses[concept_id]

        label = claim_id
        if claim.get("value") is not None:
            label = f"{claim_id}={claim['value']}"

        graph.nodes.append(GraphNode(
            id=claim_id,
            label=label,
            node_type="claim",
            metadata=meta,
        ))
        node_ids.add(claim_id)

    # ---- 3. Parameterization edges ----
    if world._has_table("parameterization"):
        param_rows = world._conn.execute("SELECT * FROM parameterization").fetchall()
        for row in param_rows:
            row_d = dict(row)
            output_id = row_d["output_concept_id"]
            if output_id not in node_ids:
                continue
            input_ids = json.loads(row_d["concept_ids"])
            for iid in input_ids:
                if iid not in node_ids:
                    continue
                graph.edges.append(GraphEdge(
                    source=iid,
                    target=output_id,
                    edge_type="parameterization",
                    metadata={
                        "formula": row_d.get("formula"),
                        "exactness": row_d.get("exactness"),
                    },
                ))

    # ---- 4. Relationship edges ----
    if world._has_table("relationship"):
        rel_rows = world._conn.execute("SELECT * FROM relationship").fetchall()
        for row in rel_rows:
            src = row["source_id"]
            tgt = row["target_id"]
            if src not in node_ids or tgt not in node_ids:
                continue
            graph.edges.append(GraphEdge(
                source=src,
                target=tgt,
                edge_type="relationship",
                metadata={"type": row["type"]},
            ))

    # ---- 5. Stance edges ----
    if world._has_table("claim_stance"):
        stance_rows = world._conn.execute("SELECT * FROM claim_stance").fetchall()
        for row in stance_rows:
            cid = row["claim_id"]
            tid = row["target_claim_id"]
            if cid not in node_ids or tid not in node_ids:
                continue
            graph.edges.append(GraphEdge(
                source=cid,
                target=tid,
                edge_type="stance",
                metadata={"stance_type": row["stance_type"]},
            ))

    # ---- 6. Claim-of edges ----
    for claim in claims:
        claim_id = claim["id"]
        concept_id = claim.get("concept_id")
        if concept_id and claim_id in node_ids and concept_id in node_ids:
            graph.edges.append(GraphEdge(
                source=claim_id,
                target=concept_id,
                edge_type="claim_of",
                metadata={},
            ))

    return graph
