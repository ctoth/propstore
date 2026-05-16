"""Source derived-store declaration helpers."""

from __future__ import annotations

import sqlite3
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from quire.projections import ProjectionColumn, ProjectionIndex, ProjectionTable

from propstore.families.documents.sources import SourceDocument


SOURCE_PROJECTION = ProjectionTable(
    name="source",
    columns=(
        ProjectionColumn("slug", "TEXT", primary_key=True),
        ProjectionColumn("source_id", "TEXT", nullable=False),
        ProjectionColumn("kind", "TEXT", nullable=False),
        ProjectionColumn("origin_type", "TEXT"),
        ProjectionColumn("origin_value", "TEXT"),
        ProjectionColumn("origin_retrieved", "TEXT"),
        ProjectionColumn("origin_content_ref", "TEXT"),
        ProjectionColumn("prior_base_rate", "TEXT"),
        ProjectionColumn("quality_json", "TEXT"),
        ProjectionColumn("derived_from_json", "TEXT"),
        ProjectionColumn("artifact_code", "TEXT"),
    ),
    indexes=(ProjectionIndex("idx_source_source_id", ("source_id",)),),
)


@dataclass(frozen=True)
class SourceProjectionRow:
    slug: str
    source_id: str
    kind: str
    origin_type: str | None
    origin_value: str | None
    origin_retrieved: str | None
    origin_content_ref: str | None
    prior_base_rate: str | None
    quality_json: str | None
    derived_from_json: str | None
    artifact_code: str | None


def _opinion_json(opinion) -> str | None:
    if opinion is None:
        return None
    return json.dumps(
        {
            "b": opinion.b,
            "d": opinion.d,
            "u": opinion.u,
            "a": opinion.a,
        },
        sort_keys=True,
    )


def compile_source_sidecar_rows(
    sources: Iterable[tuple[str, SourceDocument]],
) -> tuple[SourceProjectionRow, ...]:
    rows: list[SourceProjectionRow] = []
    for slug, source_doc in sources:
        origin = source_doc.origin
        trust = source_doc.trust
        rows.append(
            SourceProjectionRow(
                slug=slug,
                source_id=str(source_doc.id or slug),
                kind=source_doc.kind.value,
                origin_type=origin.type.value,
                origin_value=origin.value,
                origin_retrieved=origin.retrieved,
                origin_content_ref=origin.content_ref,
                prior_base_rate=_opinion_json(trust.prior_base_rate),
                quality_json=None
                if trust.quality is None
                else json.dumps(trust.quality.to_payload()),
                derived_from_json=None
                if not trust.derived_from
                else json.dumps(list(trust.derived_from)),
                artifact_code=source_doc.artifact_code,
            )
        )
    return tuple(rows)


def populate_sources(conn: sqlite3.Connection, rows: Sequence[SourceProjectionRow]) -> None:
    SOURCE_PROJECTION.insert_rows(conn, rows)
