"""Context family projection and read-model declarations."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass

from quire.projections import (
    ARTIFACT_ID_FIELD,
    AUTOINCREMENT_ID_FIELD,
    CONDITIONS_CEL_FIELD,
    PROVENANCE_JSON_FIELD,
    SEQUENCE_FIELD,
    ProjectionForeignKey,
    ProjectionIndex,
    ProjectionRow,
    ProjectionTable,
    family_reference_field,
    text_field,
)

from propstore.context_lifting import (
    IstProposition,
    LiftedAssertion,
    LiftingDecision,
    LiftingMode,
    LiftingRule,
    LiftingSystem,
)
from propstore.core.assertions import ContextReference
from propstore.core.id_types import to_context_id
from propstore.cel_types import to_cel_exprs
from propstore.families.contexts.stages import (
    LoadedContext,
    coerce_loaded_contexts,
    loaded_contexts_to_lifting_system,
)


@dataclass(frozen=True)
class ContextSidecarRows:
    context_rows: tuple[ProjectionRow, ...]
    assumption_rows: tuple[ProjectionRow, ...]
    lifting_rule_rows: tuple[ProjectionRow, ...]
    lifting_materialization_rows: tuple[ProjectionRow, ...] = ()


CONTEXT_PROJECTION = ProjectionTable(
    name="context",
    columns=(
        ARTIFACT_ID_FIELD.column(primary_key=True),
        text_field("name", nullable=False).column(),
        text_field("description").column(),
        text_field("parameters_json").column(),
        text_field("perspective").column(),
    ),
    if_not_exists=True,
)


CONTEXT_ASSUMPTION_PROJECTION = ProjectionTable(
    name="context_assumption",
    columns=(
        family_reference_field("context", nullable=False).column(),
        text_field("assumption_cel", nullable=False).column(),
        SEQUENCE_FIELD.column(),
    ),
    foreign_keys=(ProjectionForeignKey(("context_id",), "context", ("id",)),),
    indexes=(ProjectionIndex("idx_ctx_assumption", ("context_id",)),),
    if_not_exists=True,
)


CONTEXT_LIFTING_RULE_PROJECTION = ProjectionTable(
    name="context_lifting_rule",
    columns=(
        ARTIFACT_ID_FIELD.column(primary_key=True),
        family_reference_field("context", role="source", nullable=False).column(),
        family_reference_field("context", role="target", nullable=False).column(),
        CONDITIONS_CEL_FIELD.column(),
        text_field("mode", nullable=False).column(),
        text_field("justification").column(),
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
        AUTOINCREMENT_ID_FIELD.column(),
        text_field("rule_id", nullable=False).column(),
        family_reference_field("context", role="source", nullable=False).column(),
        family_reference_field("context", role="target", nullable=False).column(),
        text_field("proposition_id", nullable=False).column(),
        text_field("status", nullable=False).column(),
        text_field("exception_id").column(),
        PROVENANCE_JSON_FIELD.column(nullable=False),
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

CONTEXT_PROJECTIONS: tuple[ProjectionTable, ...] = (
    CONTEXT_PROJECTION,
    CONTEXT_ASSUMPTION_PROJECTION,
    CONTEXT_LIFTING_RULE_PROJECTION,
    CONTEXT_LIFTING_MATERIALIZATION_PROJECTION,
)


def create_context_tables(conn: sqlite3.Connection) -> None:
    for projection in CONTEXT_PROJECTIONS:
        for statement in projection.ddl_statements():
            conn.execute(statement)


def populate_contexts(
    conn: sqlite3.Connection,
    *,
    context_rows: Sequence[object],
    assumption_rows: Sequence[object],
    lifting_rule_rows: Sequence[object],
    lifting_materialization_rows: Sequence[object],
) -> None:
    CONTEXT_PROJECTION.insert_rows(conn, context_rows)
    CONTEXT_ASSUMPTION_PROJECTION.insert_rows(conn, assumption_rows)
    CONTEXT_LIFTING_RULE_PROJECTION.insert_rows(conn, lifting_rule_rows)
    CONTEXT_LIFTING_MATERIALIZATION_PROJECTION.insert_rows(
        conn,
        lifting_materialization_rows,
    )


def filter_invalid_context_lifting_rows(
    rows: ContextSidecarRows,
) -> ContextSidecarRows:
    context_ids = {row.values["id"] for row in rows.context_rows}
    valid_lifting_rows = tuple(
        row
        for row in rows.lifting_rule_rows
        if row.values["source_context_id"] in context_ids
        and row.values["target_context_id"] in context_ids
    )
    return ContextSidecarRows(
        context_rows=rows.context_rows,
        assumption_rows=rows.assumption_rows,
        lifting_rule_rows=valid_lifting_rows,
        lifting_materialization_rows=rows.lifting_materialization_rows,
    )


def compile_context_sidecar_rows(
    contexts: Sequence[LoadedContext],
    *,
    authored_ist_assertions: Sequence[IstProposition] = (),
) -> ContextSidecarRows:
    context_rows: list[ProjectionRow] = []
    assumption_rows: list[ProjectionRow] = []
    lifting_rule_rows: list[ProjectionRow] = []

    for context in coerce_loaded_contexts(contexts):
        record = context.record
        if record.context_id is None:
            continue
        context_id = str(record.context_id)

        context_rows.append(
            CONTEXT_PROJECTION.row(
                id=context_id,
                name=record.name or "",
                description=record.description,
                parameters_json=json.dumps(dict(record.parameters), sort_keys=True)
                if record.parameters
                else None,
                perspective=record.perspective,
            )
        )

        for seq, assumption in enumerate(record.assumptions, 1):
            assumption_rows.append(
                CONTEXT_ASSUMPTION_PROJECTION.row(
                    context_id=context_id,
                    assumption_cel=assumption,
                    seq=seq,
                )
            )

        for rule in record.lifting_rules:
            lifting_rule_rows.append(
                CONTEXT_LIFTING_RULE_PROJECTION.row(
                    id=rule.id,
                    source_context_id=str(rule.source.id),
                    target_context_id=str(rule.target.id),
                    conditions_cel=json.dumps(list(rule.conditions), sort_keys=True)
                    if rule.conditions
                    else None,
                    mode=rule.mode.value,
                    justification=rule.justification,
                )
            )

    materialization_rows = ()
    if authored_ist_assertions:
        lifting_system = loaded_contexts_to_lifting_system(contexts)
        decisions = tuple(
            decision
            for assertion in authored_ist_assertions
            for decision in lifting_system.lift_decisions_for(assertion)
        )
        materialization_rows = compile_context_lifting_materialization_rows(
            decisions
        )

    return ContextSidecarRows(
        context_rows=tuple(context_rows),
        assumption_rows=tuple(assumption_rows),
        lifting_rule_rows=tuple(lifting_rule_rows),
        lifting_materialization_rows=materialization_rows,
    )


def compile_context_lifting_materialization_rows(
    materializations: Sequence[LiftedAssertion | LiftingDecision],
) -> tuple[ProjectionRow, ...]:
    rows: list[ProjectionRow] = []
    for materialization in materializations:
        if isinstance(materialization, LiftingDecision):
            provenance = materialization.provenance.to_payload()
            exception_id = materialization.provenance.exception_id
            rows.append(
                CONTEXT_LIFTING_MATERIALIZATION_PROJECTION.row(
                    rule_id=materialization.rule_id,
                    source_context_id=str(materialization.source_context.id),
                    target_context_id=str(materialization.target_context.id),
                    proposition_id=materialization.proposition_id,
                    status=materialization.status.value,
                    exception_id=exception_id,
                    provenance_json=json.dumps(provenance, sort_keys=True),
                )
            )
            continue
        rows.append(
            CONTEXT_LIFTING_MATERIALIZATION_PROJECTION.row(
                rule_id=materialization.rule_id,
                source_context_id=str(materialization.source_context.id),
                target_context_id=str(materialization.target_context.id),
                proposition_id=materialization.proposition_id,
                status=materialization.status.value,
                exception_id=materialization.exception_id,
                provenance_json=json.dumps(materialization.provenance, sort_keys=True),
            )
        )
    return tuple(rows)


def load_lifting_system(conn: sqlite3.Connection) -> LiftingSystem | None:
    rows = conn.execute("SELECT id FROM context ORDER BY id").fetchall()
    if not rows:
        return None

    context_ids = [str(row["id"]) for row in rows]
    context_refs = tuple(
        ContextReference(id=to_context_id(context_id))
        for context_id in context_ids
    )

    assumption_rows = conn.execute(
        "SELECT context_id, assumption_cel FROM context_assumption "
        "ORDER BY context_id, seq"
    ).fetchall()
    assumptions_by_id: dict[str, list[str]] = {
        context_id: [] for context_id in context_ids
    }
    for row in assumption_rows:
        context_id = row["context_id"]
        if context_id not in assumptions_by_id:
            continue
        assumptions_by_id[context_id].append(row["assumption_cel"])

    lifting_rows = conn.execute(
        """
        SELECT id, source_context_id, target_context_id,
               conditions_cel, mode, justification
        FROM context_lifting_rule
        ORDER BY id
        """
    ).fetchall()
    lifting_rules: list[LiftingRule] = []
    for row in lifting_rows:
        raw_conditions = row["conditions_cel"]
        if raw_conditions:
            conditions = tuple(str(item) for item in json.loads(raw_conditions))
        else:
            conditions = ()
        lifting_rules.append(
            LiftingRule(
                id=row["id"],
                source=ContextReference(id=to_context_id(row["source_context_id"])),
                target=ContextReference(id=to_context_id(row["target_context_id"])),
                conditions=to_cel_exprs(conditions),
                mode=LiftingMode(row["mode"]),
                justification=row["justification"],
            )
        )

    return LiftingSystem(
        contexts=context_refs,
        lifting_rules=tuple(lifting_rules),
        context_assumptions={
            to_context_id(context_id): to_cel_exprs(assumptions)
            for context_id, assumptions in assumptions_by_id.items()
        },
    )
