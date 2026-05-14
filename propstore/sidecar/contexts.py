"""Context projection contracts for the sidecar."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from quire.projections import ProjectionColumn, ProjectionForeignKey, ProjectionIndex, ProjectionTable


CONTEXT_PROJECTION = ProjectionTable(
    name="context",
    columns=(
        ProjectionColumn("id", "TEXT", primary_key=True),
        ProjectionColumn("name", "TEXT", nullable=False),
        ProjectionColumn("description", "TEXT"),
        ProjectionColumn("parameters_json", "TEXT"),
        ProjectionColumn("perspective", "TEXT"),
    ),
    if_not_exists=True,
)


CONTEXT_ASSUMPTION_PROJECTION = ProjectionTable(
    name="context_assumption",
    columns=(
        ProjectionColumn("context_id", "TEXT", nullable=False),
        ProjectionColumn("assumption_cel", "TEXT", nullable=False),
        ProjectionColumn("seq", "INTEGER", nullable=False),
    ),
    foreign_keys=(ProjectionForeignKey(("context_id",), "context", ("id",)),),
    indexes=(ProjectionIndex("idx_ctx_assumption", ("context_id",)),),
    if_not_exists=True,
)


CONTEXT_LIFTING_RULE_PROJECTION = ProjectionTable(
    name="context_lifting_rule",
    columns=(
        ProjectionColumn("id", "TEXT", primary_key=True),
        ProjectionColumn("source_context_id", "TEXT", nullable=False),
        ProjectionColumn("target_context_id", "TEXT", nullable=False),
        ProjectionColumn("conditions_cel", "TEXT"),
        ProjectionColumn("mode", "TEXT", nullable=False),
        ProjectionColumn("justification", "TEXT"),
    ),
    foreign_keys=(
        ProjectionForeignKey(("source_context_id",), "context", ("id",)),
        ProjectionForeignKey(("target_context_id",), "context", ("id",)),
    ),
    indexes=(
        ProjectionIndex("idx_ctx_lift_source", ("source_context_id",)),
        ProjectionIndex("idx_ctx_lift_target", ("target_context_id",)),
    ),
    if_not_exists=True,
)


CONTEXT_LIFTING_MATERIALIZATION_PROJECTION = ProjectionTable(
    name="context_lifting_materialization",
    columns=(
        ProjectionColumn("id", "INTEGER PRIMARY KEY AUTOINCREMENT", insertable=False),
        ProjectionColumn("rule_id", "TEXT", nullable=False),
        ProjectionColumn("source_context_id", "TEXT", nullable=False),
        ProjectionColumn("target_context_id", "TEXT", nullable=False),
        ProjectionColumn("proposition_id", "TEXT", nullable=False),
        ProjectionColumn("status", "TEXT", nullable=False),
        ProjectionColumn("exception_id", "TEXT"),
        ProjectionColumn("provenance_json", "TEXT", nullable=False),
    ),
    foreign_keys=(
        ProjectionForeignKey(("rule_id",), "context_lifting_rule", ("id",)),
        ProjectionForeignKey(("source_context_id",), "context", ("id",)),
        ProjectionForeignKey(("target_context_id",), "context", ("id",)),
    ),
    indexes=(
        ProjectionIndex(
            "idx_ctx_lift_mat_target",
            ("target_context_id", "proposition_id"),
        ),
    ),
    if_not_exists=True,
)


@dataclass(frozen=True)
class ContextProjectionRow:
    id: str
    name: str
    description: str | None
    parameters_json: str | None
    perspective: str | None

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parameters_json": self.parameters_json,
            "perspective": self.perspective,
        }


@dataclass(frozen=True)
class ContextAssumptionProjectionRow:
    context_id: str
    assumption_cel: str
    seq: int

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "context_id": self.context_id,
            "assumption_cel": self.assumption_cel,
            "seq": self.seq,
        }


@dataclass(frozen=True)
class ContextLiftingRuleProjectionRow:
    id: str
    source_context_id: str
    target_context_id: str
    conditions_cel: str | None
    mode: str
    justification: str | None

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "id": self.id,
            "source_context_id": self.source_context_id,
            "target_context_id": self.target_context_id,
            "conditions_cel": self.conditions_cel,
            "mode": self.mode,
            "justification": self.justification,
        }


@dataclass(frozen=True)
class ContextLiftingMaterializationProjectionRow:
    rule_id: str
    source_context_id: str
    target_context_id: str
    proposition_id: str
    status: str
    exception_id: str | None
    provenance_json: str

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "rule_id": self.rule_id,
            "source_context_id": self.source_context_id,
            "target_context_id": self.target_context_id,
            "proposition_id": self.proposition_id,
            "status": self.status,
            "exception_id": self.exception_id,
            "provenance_json": self.provenance_json,
        }
