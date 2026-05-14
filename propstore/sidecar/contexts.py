"""Context projection contracts for the sidecar."""

from __future__ import annotations

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
