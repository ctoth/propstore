"""Relation-edge projection contract for the sidecar."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from propstore.sidecar.projection import ProjectionColumn, ProjectionIndex, ProjectionTable


RELATION_EDGE_PROJECTION = ProjectionTable(
    name="relation_edge",
    columns=(
        ProjectionColumn("id", "INTEGER PRIMARY KEY AUTOINCREMENT", insertable=False),
        ProjectionColumn("source_kind", "TEXT", nullable=False),
        ProjectionColumn("source_id", "TEXT", nullable=False),
        ProjectionColumn("relation_type", "TEXT", nullable=False),
        ProjectionColumn("target_kind", "TEXT", nullable=False),
        ProjectionColumn("target_id", "TEXT", nullable=False),
        ProjectionColumn("perspective_source_claim_id", "TEXT"),
        ProjectionColumn("target_justification_id", "TEXT"),
        ProjectionColumn("conditions_cel", "TEXT"),
        ProjectionColumn("strength", "TEXT"),
        ProjectionColumn("conditions_differ", "TEXT"),
        ProjectionColumn("note", "TEXT"),
        ProjectionColumn("resolution_method", "TEXT"),
        ProjectionColumn("resolution_model", "TEXT"),
        ProjectionColumn("embedding_model", "TEXT"),
        ProjectionColumn("embedding_distance", "REAL"),
        ProjectionColumn("pass_number", "INTEGER"),
        ProjectionColumn("confidence", "REAL"),
        ProjectionColumn("opinion_belief", "REAL", check_sql="opinion_belief >= 0 AND opinion_belief <= 1"),
        ProjectionColumn("opinion_disbelief", "REAL", check_sql="opinion_disbelief >= 0 AND opinion_disbelief <= 1"),
        ProjectionColumn("opinion_uncertainty", "REAL", check_sql="opinion_uncertainty >= 0 AND opinion_uncertainty <= 1"),
        ProjectionColumn("opinion_base_rate", "REAL", check_sql="opinion_base_rate > 0 AND opinion_base_rate < 1"),
    ),
    checks=(
        "opinion_belief IS NULL OR ABS(opinion_belief + opinion_disbelief + opinion_uncertainty - 1.0) <= 1e-6",
    ),
    indexes=(
        ProjectionIndex("idx_relation_edge_source", ("source_kind", "source_id")),
        ProjectionIndex("idx_relation_edge_target", ("target_kind", "target_id")),
        ProjectionIndex("idx_relation_edge_type", ("relation_type",)),
    ),
)


@dataclass(frozen=True)
class RelationEdgeProjectionRow:
    source_kind: str
    source_id: str
    relation_type: str
    target_kind: str
    target_id: str
    conditions_cel: str | None
    note: str | None

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "source_kind": self.source_kind,
            "source_id": self.source_id,
            "relation_type": self.relation_type,
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "perspective_source_claim_id": None,
            "target_justification_id": None,
            "conditions_cel": self.conditions_cel,
            "strength": None,
            "conditions_differ": None,
            "note": self.note,
            "resolution_method": None,
            "resolution_model": None,
            "embedding_model": None,
            "embedding_distance": None,
            "pass_number": None,
            "confidence": None,
            "opinion_belief": None,
            "opinion_disbelief": None,
            "opinion_uncertainty": None,
            "opinion_base_rate": None,
        }
