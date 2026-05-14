from __future__ import annotations

import json
import sqlite3

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.documents.sources import (
    SourceDocument,
    SourceOriginDocument,
    SourceTrustDocument,
    SourceTrustQualityDocument,
)
from propstore.opinion import Opinion
from propstore.provenance import ProvenanceStatus
from propstore.sidecar.passes import compile_source_sidecar_rows
from propstore.sidecar.sources import SOURCE_PROJECTION, SourceProjectionRow, populate_sources


def test_source_rows_are_projection_rows_and_round_trip_artifact_code() -> None:
    source = SourceDocument(
        id="source-alpha",
        kind=SourceKind.ACADEMIC_PAPER,
        origin=SourceOriginDocument(
            type=SourceOriginType.DOI,
            value="10.1000/example",
            retrieved="2026-05-14",
            content_ref="sha256:abc",
        ),
        trust=SourceTrustDocument(
            status=ProvenanceStatus.STATED,
            prior_base_rate=Opinion(b=0.2, d=0.1, u=0.7, a=0.5),
            quality=SourceTrustQualityDocument(
                status=ProvenanceStatus.STATED,
                b=0.8,
                d=0.05,
                u=0.15,
                a=0.5,
            ),
            derived_from=("seed-a", "seed-b"),
        ),
        artifact_code="sha256:source-alpha",
    )

    rows = compile_source_sidecar_rows((("alpha", source),))

    assert rows == (
        SourceProjectionRow(
            slug="alpha",
            source_id="source-alpha",
            kind="academic_paper",
            origin_type="doi",
            origin_value="10.1000/example",
            origin_retrieved="2026-05-14",
            origin_content_ref="sha256:abc",
            prior_base_rate='{"a": 0.5, "b": 0.2, "d": 0.1, "u": 0.7}',
            quality_json='{"status": "stated", "b": 0.8, "d": 0.05, "u": 0.15, "a": 0.5}',
            derived_from_json='["seed-a", "seed-b"]',
            artifact_code="sha256:source-alpha",
        ),
    )

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for statement in SOURCE_PROJECTION.ddl_statements():
        conn.execute(statement)

    populate_sources(conn, rows)

    stored = conn.execute('SELECT * FROM "source" WHERE slug = ?', ("alpha",)).fetchone()
    assert stored["artifact_code"] == "sha256:source-alpha"
    assert json.loads(stored["prior_base_rate"]) == {"a": 0.5, "b": 0.2, "d": 0.1, "u": 0.7}
    assert json.loads(stored["quality_json"]) == {
        "status": "stated",
        "b": 0.8,
        "d": 0.05,
        "u": 0.15,
        "a": 0.5,
    }
    assert json.loads(stored["derived_from_json"]) == ["seed-a", "seed-b"]
