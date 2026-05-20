from __future__ import annotations

import inspect
from pathlib import Path

from quire.documents import convert_document_value

from propstore.families.documents.micropubs import MicropublicationDocument
from propstore.families.identity.micropubs import micropub_artifact_id
from propstore.families.micropublications.declaration import (
    MicropublicationProjectionRow,
    MicropublicationSidecarRows,
    create_micropublication_tables,
    populate_micropublications,
)
from propstore.families.world_charters import world_sqlalchemy_schema
from quire.sqlalchemy_store import create_sqlalchemy_store
from quire.derived_runtime import connect_sqlite_store


def _micropub(page: int) -> MicropublicationDocument:
    return convert_document_value(
        {
            "artifact_id": "ps:micropub:old",
            "version_id": "old-version",
            "context": {"id": "ctx_alpha"},
            "claims": ["ps:claim:alpha"],
            "source": "tag:local@propstore,2026:source/demo",
            "evidence": [{"kind": "paper_page", "reference": f"demo:{page}"}],
            "provenance": {"paper": "demo", "page": page},
        },
        MicropublicationDocument,
        source="tests:micropub.yaml",
    )


def _row(document: MicropublicationDocument) -> MicropublicationProjectionRow:
    return MicropublicationProjectionRow(
        id=micropub_artifact_id(document),
        context_id=document.context.id,
        assumptions_json="[]",
        evidence_json="[]",
        stance=None,
        provenance_json=None,
        source_slug="demo",
    )


def test_micropublication_dedupe_uses_wscm_payload_identity_language() -> None:
    docstring = inspect.getdoc(populate_micropublications) or ""

    assert "full canonical payload by WS-CM" in docstring
    assert "two micropub files that carry the same id carry definitionally identical content" not in docstring


def test_micropublication_sidecar_dedupe_keeps_distinct_payload_ids(
    tmp_path: Path,
) -> None:
    first = _micropub(page=1)
    changed = _micropub(page=2)
    assert micropub_artifact_id(first) != micropub_artifact_id(changed)

    sidecar_path = tmp_path / "propstore.sqlite"
    create_sqlalchemy_store(sidecar_path, world_sqlalchemy_schema())
    conn = connect_sqlite_store(sidecar_path)
    try:
        create_micropublication_tables(conn)
        conn.execute("INSERT INTO context (id, name) VALUES (?, ?)", ("ctx_alpha", "alpha"))

        populate_micropublications(
            conn,
            MicropublicationSidecarRows(
                micropublication_rows=(_row(first), _row(first), _row(changed)),
                claim_rows=(),
            ),
        )
        conn.commit()
        ids = {
            row[0]
            for row in conn.execute("SELECT id FROM micropublication").fetchall()
        }
    finally:
        conn.close()

    assert ids == {micropub_artifact_id(first), micropub_artifact_id(changed)}
