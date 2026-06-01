"""Duplicate micropublication files dedupe on the typed charter path."""

from __future__ import annotations

from sqlalchemy import text

from quire.documents import convert_document_value
from quire.sqlalchemy_store import create_sqlalchemy_store

from propstore.families.claims.references import (
    ImportedClaimReference,
    imported_claim_reference_index,
)
from propstore.families.micropublications.declaration import (
    MicropublicationDocument,
    compile_micropublication_models_with_diagnostics,
)
from propstore.families.registry import world_schema
from quire.sqlalchemy_store import readonly_session, writable_session


def _seed_claim_and_context(sidecar_path) -> None:
    schema = world_schema()
    with writable_session(sidecar_path, schema) as derived:
        derived.session.execute(
            text("INSERT INTO context (id, name) VALUES ('ctx:default', 'default')")
        )
        derived.session.execute(
            text(
                """
                INSERT INTO claim_core (
                    id, primary_logical_id, logical_ids_json, version_id,
                    seq, type, source_paper, provenance_page, provenance_json,
                    context_id, build_status, promotion_status
                ) VALUES (
                    'ps:claim:alpha', 'claim-alpha', '[]', 'claim-version',
                    1, 'observation', 'paper-alpha', 1, NULL,
                    'ctx:default', 'ingested', 'promoted'
                )
                """
            )
        )
        derived.commit()


def test_duplicate_micropublication_models_and_links_persist_once(tmp_path):
    sidecar_path = tmp_path / "propstore.sqlite"
    schema = world_schema()
    create_sqlalchemy_store(sidecar_path, schema)
    _seed_claim_and_context(sidecar_path)

    shared_id = "ps:micropub:shared0001"
    claim_index = imported_claim_reference_index(
        (ImportedClaimReference("claim-alpha", "ps:claim:alpha"),)
    )
    batches, diagnostics = compile_micropublication_models_with_diagnostics(
        (
            ("paper-alpha/micropubs/shared.yaml", _micropub(shared_id)),
            ("paper-alpha/micropubs/shared--copy.yaml", _micropub(shared_id)),
        ),
        claim_index,
    )

    micropublications, claim_links = batches
    assert diagnostics == ()
    assert len(micropublications) == 1
    assert len(claim_links) == 1

    with writable_session(sidecar_path, schema) as derived:
        derived.add_all(micropublications)
        derived.add_all(claim_links)
        derived.commit()

    with readonly_session(sidecar_path, schema) as derived:
        micropub_count = derived.session.execute(
            text(
                "SELECT COUNT(*) FROM micropublication WHERE id = 'ps:micropub:shared0001'"
            )
        ).scalar_one()
        link_count = derived.session.execute(
            text(
                """
                SELECT COUNT(*) FROM micropublication_claim
                WHERE micropublication_id = 'ps:micropub:shared0001'
                AND claim_id = 'ps:claim:alpha'
                """
            )
        ).scalar_one()

    assert micropub_count == 1
    assert link_count == 1
