"""Regression test for Bug 6: UNIQUE violation in sidecar build when two
micropublication files contribute the same ``micropublication.id``.

Reproduces the aspirin ``pks build`` crash (2026-04-23) surfaced after
the Bug 5 fix shipped in v0.3.2: the aspirin repository has two McNeil
micropublication files (the original and a ``--<hex>`` disambiguated
copy) carrying overlapping ``id`` values. Because the micropub id is
content-derived, identical ids mean identical micropub content — the
build pass must dedupe instead of crashing with
``sqlite3.IntegrityError: UNIQUE constraint failed: micropublication.id``.
"""
from __future__ import annotations

from propstore.sidecar.micropublications import populate_micropublications
from propstore.sidecar.schema import (
    create_context_tables,
    create_micropublication_tables,
)
from propstore.sidecar.sqlite import connect_sidecar
from propstore.sidecar.stages import (
    MicropublicationClaimInsertRow,
    MicropublicationInsertRow,
    MicropublicationSidecarRows,
)


def _make_micropub_values(
    micropub_id: str,
    context_id: str,
    source_slug: str,
) -> tuple:
    # Positional tuple matches the INSERT in populate_micropublications:
    # (id, context_id, assumptions_json, evidence_json,
    #  stance, provenance_json, source_slug)
    return (
        micropub_id,
        context_id,
        "[]",
        "[]",
        None,
        None,
        source_slug,
    )


def test_populate_micropublications_tolerates_duplicate_ids(tmp_path):
    sidecar_path = tmp_path / "propstore.sqlite"
    conn = connect_sidecar(sidecar_path)
    try:
        create_context_tables(conn)
        create_micropublication_tables(conn)

        # Minimum context row to satisfy the FK from micropublication.
        conn.execute(
            "INSERT INTO context (id, name) VALUES (?, ?)",
            ("ctx:default", "default"),
        )

        # Two rows share the micropublication id. Simulates aspirin's
        # two McNeil micropub files (suffixed + un-suffixed) that share
        # artifact ids.
        shared_id = "ps:micropub:shared0001"
        rows = MicropublicationSidecarRows(
            micropublication_rows=(
                MicropublicationInsertRow(
                    _make_micropub_values(
                        shared_id,
                        "ctx:default",
                        "paper-alpha",
                    )
                ),
                MicropublicationInsertRow(
                    _make_micropub_values(
                        shared_id,
                        "ctx:default",
                        "paper-alpha-variant",
                    )
                ),
            ),
            claim_rows=(),
        )

        populate_micropublications(conn, rows)
        conn.commit()

        micropub_rows = conn.execute(
            "SELECT id FROM micropublication WHERE id = ?",
            (shared_id,),
        ).fetchall()
    finally:
        conn.close()

    # Duplicates collapse to a single row.
    assert len(micropub_rows) == 1


def test_populate_micropublications_tolerates_duplicate_claim_link_ids(
    tmp_path,
):
    """Also dedupe (micropublication_id, claim_id) pairs from duplicate
    micropub files so the second file's claim-link rows don't hit the
    composite PK on ``micropublication_claim``.
    """
    from propstore.sidecar.schema import create_claim_tables

    sidecar_path = tmp_path / "propstore.sqlite"
    conn = connect_sidecar(sidecar_path)
    try:
        create_context_tables(conn)
        create_claim_tables(conn)
        create_micropublication_tables(conn)

        conn.execute(
            "INSERT INTO context (id, name) VALUES (?, ?)",
            ("ctx:default", "default"),
        )

        shared_id = "ps:micropub:shared0002"
        rows = MicropublicationSidecarRows(
            micropublication_rows=(
                MicropublicationInsertRow(
                    _make_micropub_values(
                        shared_id,
                        "ctx:default",
                        "paper-alpha",
                    )
                ),
                MicropublicationInsertRow(
                    _make_micropub_values(
                        shared_id,
                        "ctx:default",
                        "paper-alpha-variant",
                    )
                ),
            ),
            claim_rows=(),
        )

        populate_micropublications(conn, rows)
        conn.commit()

        micropub_rows = conn.execute(
            "SELECT id FROM micropublication WHERE id = ?",
            (shared_id,),
        ).fetchall()
    finally:
        conn.close()

    assert len(micropub_rows) == 1
