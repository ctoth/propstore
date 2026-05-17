"""Context family projection and read-model declarations."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any

from quire.projection_mapping import ProjectionCodec, ProjectionModel, ReferencePath, ScalarPath
from quire.projections import (
    ProjectionColumn,
    ProjectionRow,
    ProjectionSchema,
    ProjectionTable,
    create_projection_schema,
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


def _nullable_text(value: object) -> str | None:
    return None if value is None else str(value)


def _json_or_none(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Mapping) and not value:
        return None
    if isinstance(value, Sequence) and not isinstance(value, str) and not value:
        return None
    return json.dumps(value, sort_keys=True)


def _json_mapping(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, str):
        raise TypeError(f"expected JSON text, got {type(value).__name__}")
    decoded = json.loads(value)
    if not isinstance(decoded, Mapping):
        raise TypeError("expected JSON object")
    return {str(key): str(item) for key, item in decoded.items()}


def _json_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, str):
        raise TypeError(f"expected JSON text, got {type(value).__name__}")
    decoded = json.loads(value)
    if not isinstance(decoded, Sequence) or isinstance(decoded, str):
        raise TypeError("expected JSON array")
    return tuple(str(item) for item in decoded)


TEXT_CODEC = ProjectionCodec("text", "TEXT", encoder=_nullable_text, decoder=_nullable_text)
PARAMETERS_CODEC = ProjectionCodec(
    "context_parameters",
    "TEXT",
    encoder=_json_or_none,
    decoder=_json_mapping,
)
CONDITIONS_CODEC = ProjectionCodec(
    "context_conditions",
    "TEXT",
    encoder=_json_or_none,
    decoder=_json_string_tuple,
)
PROVENANCE_CODEC = ProjectionCodec(
    "context_lifting_provenance",
    "TEXT",
    encoder=_json_or_none,
    decoder=lambda value: {} if value is None else json.loads(str(value)),
)
AUTOINCREMENT_CODEC = ProjectionCodec("autoincrement", "INTEGER PRIMARY KEY AUTOINCREMENT")


CONTEXT_MODEL: ProjectionModel[dict[str, object]] = ProjectionModel(
    name="context",
    table="context",
    result_type=dict,
    fields=(
        ScalarPath(("id",), "id", codec=TEXT_CODEC, nullable=False, primary_key=True, missing="raise"),
        ScalarPath(("name",), "name", codec=TEXT_CODEC, nullable=False, missing="raise"),
        ScalarPath(("description",), "description", codec=TEXT_CODEC),
        ScalarPath(("parameters",), "parameters_json", codec=PARAMETERS_CODEC),
        ScalarPath(("perspective",), "perspective", codec=TEXT_CODEC),
    ),
    if_not_exists=True,
)


CONTEXT_ASSUMPTION_MODEL: ProjectionModel[dict[str, object]] = ProjectionModel(
    name="context_assumption",
    table="context_assumption",
    result_type=dict,
    fields=(
        ReferencePath(("context_id",), "context_id", family="context", nullable=False, indexed=True, missing="raise"),
        ScalarPath(("assumption_cel",), "assumption_cel", codec=TEXT_CODEC, nullable=False, missing="raise"),
        ScalarPath(("seq",), "seq", codec=ProjectionCodec("integer", "INTEGER"), nullable=False, missing="raise"),
    ),
    if_not_exists=True,
)


CONTEXT_LIFTING_RULE_MODEL: ProjectionModel[dict[str, object]] = ProjectionModel(
    name="context_lifting_rule",
    table="context_lifting_rule",
    result_type=dict,
    fields=(
        ScalarPath(("id",), "id", codec=TEXT_CODEC, nullable=False, primary_key=True, missing="raise"),
        ReferencePath(("source_context_id",), "source_context_id", family="context", nullable=False, indexed=True, missing="raise"),
        ReferencePath(("target_context_id",), "target_context_id", family="context", nullable=False, indexed=True, missing="raise"),
        ScalarPath(("conditions",), "conditions_cel", codec=CONDITIONS_CODEC),
        ScalarPath(("mode",), "mode", codec=TEXT_CODEC, nullable=False, missing="raise"),
        ScalarPath(("justification",), "justification", codec=TEXT_CODEC),
    ),
    if_not_exists=True,
)


CONTEXT_LIFTING_MATERIALIZATION_MODEL: ProjectionModel[dict[str, object]] = ProjectionModel(
    name="context_lifting_materialization",
    table="context_lifting_materialization",
    result_type=dict,
    fields=(
        ScalarPath(("id",), "id", codec=AUTOINCREMENT_CODEC, insertable=False),
        ReferencePath(("rule_id",), "rule_id", family="context_lifting_rule", nullable=False, missing="raise"),
        ReferencePath(("source_context_id",), "source_context_id", family="context", nullable=False, indexed=True, missing="raise"),
        ReferencePath(("target_context_id",), "target_context_id", family="context", nullable=False, indexed=True, missing="raise"),
        ScalarPath(("proposition_id",), "proposition_id", codec=TEXT_CODEC, nullable=False, missing="raise"),
        ScalarPath(("status",), "status", codec=TEXT_CODEC, nullable=False, missing="raise"),
        ScalarPath(("exception_id",), "exception_id", codec=TEXT_CODEC),
        ScalarPath(("provenance",), "provenance_json", codec=PROVENANCE_CODEC, nullable=False, missing="raise"),
    ),
    if_not_exists=True,
)

CONTEXT_TABLE = CONTEXT_MODEL.projection_tables()[0]
CONTEXT_ASSUMPTION_TABLE = CONTEXT_ASSUMPTION_MODEL.projection_tables()[0]
CONTEXT_LIFTING_RULE_TABLE = CONTEXT_LIFTING_RULE_MODEL.projection_tables()[0]
CONTEXT_LIFTING_MATERIALIZATION_TABLE = CONTEXT_LIFTING_MATERIALIZATION_MODEL.projection_tables()[0]

CONTEXT_TABLES = (
    CONTEXT_TABLE,
    CONTEXT_ASSUMPTION_TABLE,
    CONTEXT_LIFTING_RULE_TABLE,
    CONTEXT_LIFTING_MATERIALIZATION_TABLE,
)

CONTEXT_SCHEMA: ProjectionSchema = create_projection_schema(
    *CONTEXT_TABLES,
)


def create_context_tables(conn: sqlite3.Connection) -> None:
    CONTEXT_SCHEMA.create_all(conn)


def populate_contexts(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    rows_by_table: dict[str, list[Mapping[str, Any]]] = {
        table.name: [] for table in CONTEXT_TABLES
    }
    for row in rows:
        rows_by_table[row.table].append(row.values)
    for table in CONTEXT_TABLES:
        conn.executemany(table.insert_sql(), tuple(rows_by_table[table.name]))


def filter_invalid_context_lifting_rows(
    rows: Sequence[ProjectionRow],
) -> tuple[ProjectionRow, ...]:
    context_ids = {
        row.values["id"]
        for row in rows
        if row.table == CONTEXT_TABLE.name
    }
    return tuple(
        row
        for row in rows
        if row.table != CONTEXT_LIFTING_RULE_TABLE.name
        or (
            row.values["source_context_id"] in context_ids
            and row.values["target_context_id"] in context_ids
        )
    )


def compile_context_sidecar_rows(
    contexts: Sequence[LoadedContext],
    *,
    authored_ist_assertions: Sequence[IstProposition] = (),
) -> tuple[ProjectionRow, ...]:
    context_rows: list[ProjectionRow] = []
    assumption_rows: list[ProjectionRow] = []
    lifting_rule_rows: list[ProjectionRow] = []

    for context in coerce_loaded_contexts(contexts):
        record = context.record
        if record.context_id is None:
            continue
        context_id = str(record.context_id)

        context_rows.append(
            _projection_row(
                CONTEXT_TABLE,
                CONTEXT_MODEL.to_row(
                    {
                        "id": context_id,
                        "name": record.name or "",
                        "description": record.description,
                        "parameters": dict(record.parameters),
                        "perspective": record.perspective,
                    }
                ),
            )
        )

        for seq, assumption in enumerate(record.assumptions, 1):
            assumption_rows.append(
                _projection_row(
                    CONTEXT_ASSUMPTION_TABLE,
                    CONTEXT_ASSUMPTION_MODEL.to_row(
                        {
                            "context_id": context_id,
                            "assumption_cel": assumption,
                            "seq": seq,
                        }
                    ),
                )
            )

        for rule in record.lifting_rules:
            lifting_rule_rows.append(
                _projection_row(
                    CONTEXT_LIFTING_RULE_TABLE,
                    CONTEXT_LIFTING_RULE_MODEL.to_row(
                        {
                            "id": rule.id,
                            "source_context_id": str(rule.source.id),
                            "target_context_id": str(rule.target.id),
                            "conditions": tuple(rule.conditions),
                            "mode": rule.mode.value,
                            "justification": rule.justification,
                        }
                    ),
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

    return tuple(context_rows + assumption_rows + lifting_rule_rows + list(materialization_rows))


def compile_context_lifting_materialization_rows(
    materializations: Sequence[LiftedAssertion | LiftingDecision],
) -> tuple[ProjectionRow, ...]:
    rows: list[ProjectionRow] = []
    for materialization in materializations:
        if isinstance(materialization, LiftingDecision):
            provenance = materialization.provenance.to_payload()
            exception_id = materialization.provenance.exception_id
            rows.append(
                _lifting_materialization_row(
                    rule_id=materialization.rule_id,
                    source_context_id=str(materialization.source_context.id),
                    target_context_id=str(materialization.target_context.id),
                    proposition_id=materialization.proposition_id,
                    status=materialization.status.value,
                    exception_id=exception_id,
                    provenance=provenance,
                )
            )
            continue
        rows.append(
            _lifting_materialization_row(
                rule_id=materialization.rule_id,
                source_context_id=str(materialization.source_context.id),
                target_context_id=str(materialization.target_context.id),
                proposition_id=materialization.proposition_id,
                status=materialization.status.value,
                exception_id=materialization.exception_id,
                provenance=materialization.provenance,
            )
        )
    return tuple(rows)


def load_lifting_system(conn: sqlite3.Connection) -> LiftingSystem | None:
    context_rows = sorted(
        CONTEXT_TABLE.select_all(conn),
        key=lambda row: str(row["id"]),
    )
    if not context_rows:
        return None

    context_ids = [str(row["id"]) for row in context_rows]
    context_refs = tuple(
        ContextReference(id=to_context_id(context_id))
        for context_id in context_ids
    )

    assumption_rows = sorted(
        CONTEXT_ASSUMPTION_TABLE.select_all(conn),
        key=lambda row: (str(row["context_id"]), int(row["seq"])),
    )
    assumptions_by_id: dict[str, list[str]] = {
        context_id: [] for context_id in context_ids
    }
    for row in assumption_rows:
        context_id = row["context_id"]
        if context_id not in assumptions_by_id:
            continue
        assumptions_by_id[context_id].append(row["assumption_cel"])

    lifting_rows = sorted(
        CONTEXT_LIFTING_RULE_TABLE.select_all(conn),
        key=lambda row: str(row["id"]),
    )
    lifting_rules: list[LiftingRule] = []
    for row in lifting_rows:
        conditions = tuple(str(item) for item in row.get("conditions", ()))
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


def _projection_row(table: ProjectionTable, values: Mapping[str, Any]) -> ProjectionRow:
    return ProjectionRow(table=table.name, values=values)


def _lifting_materialization_row(
    *,
    rule_id: str,
    source_context_id: str,
    target_context_id: str,
    proposition_id: str,
    status: str,
    exception_id: str | None,
    provenance: Mapping[str, object],
) -> ProjectionRow:
    return _projection_row(
        CONTEXT_LIFTING_MATERIALIZATION_TABLE,
        CONTEXT_LIFTING_MATERIALIZATION_MODEL.to_row(
            {
                "rule_id": rule_id,
                "source_context_id": source_context_id,
                "target_context_id": target_context_id,
                "proposition_id": proposition_id,
                "status": status,
                "exception_id": exception_id,
                "provenance": dict(provenance),
            }
        ),
    )
