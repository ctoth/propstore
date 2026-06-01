"""Regression tests for WorldQuery generic family reference lookup."""

from __future__ import annotations

import json
import sqlite3
from sqlite3 import Connection
from pathlib import Path


from tests.sidecar_schema_helpers import build_world_projection_schema
from tests.family_helpers import world_query_from_sqlite_path


# ── test fixture helpers ─────────────────────────────────────────────


def _insert_claim_row(conn: Connection, claim_id: str, seq: int) -> None:
    """Insert a claim_core row with a matching ``test:<id>`` logical id.

    Mirrors the claim_core shape the fallback scans: ``primary_logical_id``
    = ``test:<id>``, ``logical_ids_json`` = ``[{"namespace":"test","value":<id>}]``.
    A local helper is used instead of ``tests.conftest.insert_claim`` because
    the latter writes ``seq = NULL`` which violates the NOT NULL constraint
    on the canonical schema.
    """

    conn.execute(
        """
        INSERT INTO claim_core (
            id, primary_logical_id, logical_ids_json, version_id,
            seq, type, target_concept,
            source_slug, source_paper, provenance_page, provenance_json, context_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            f"test:{claim_id}",
            json.dumps([{"namespace": "test", "value": claim_id}]),
            f"sha256:{claim_id}",
            seq,
            "measurement",
            None,
            "test",
            "test",
            1,
            None,
            None,
        ),
    )


def _insert_concept(conn: Connection, concept_id: str) -> None:
    """Insert a concept row with a matching ``test:<id>`` logical id.

    Mirrors the shape ``insert_claim`` writes for claim_core: a
    ``primary_logical_id`` of ``test:<id>`` AND a ``logical_ids_json``
    list of ``{"namespace": "test", "value": <id>}`` — exactly the shape
    the fallback scans.
    """

    conn.execute(
        """
        INSERT INTO concept (
            id, content_hash, seq, canonical_name, kind_type, form, form_parameters,
            primary_logical_id, logical_ids_json, status, domain, definition
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            concept_id,
            f"sha256:{concept_id}",
            0,
            f"canonical_{concept_id}",
            "category",
            "category",
            None,
            f"test:{concept_id}",
            json.dumps([{"namespace": "test", "value": concept_id}]),
            "accepted",
            None,
            f"definition for {concept_id}",
        ),
    )


def _build_claim_sidecar(tmp_path: Path, n_rows: int) -> Path:
    sidecar = tmp_path / "propstore.sqlite"
    conn = sqlite3.connect(sidecar)
    try:
        build_world_projection_schema(conn)
        for idx in range(n_rows):
            _insert_claim_row(conn, f"claim_{idx}", seq=idx)
        conn.commit()
    finally:
        conn.close()
    return sidecar


def _build_concept_sidecar(tmp_path: Path, n_rows: int) -> Path:
    sidecar = tmp_path / "propstore.sqlite"
    conn = sqlite3.connect(sidecar)
    try:
        build_world_projection_schema(conn)
        for idx in range(n_rows):
            _insert_concept(conn, f"concept_{idx}")
        conn.commit()
    finally:
        conn.close()
    return sidecar


# ── claim reference lookup ────────────────────────────────────────────


def test_get_claim_resolves_namespaced_logical_id(tmp_path):
    sidecar = _build_claim_sidecar(tmp_path, n_rows=200)

    world = world_query_from_sqlite_path(sidecar)
    try:
        assert world.get_claim("test:claim_missing") is None
        resolved = world.get_claim("test:claim_42")
        assert resolved is not None
        assert resolved.id == "claim_42"
    finally:
        world.close()


def test_get_claim_resolves_bare_logical_id_value(tmp_path):
    sidecar = _build_claim_sidecar(tmp_path, n_rows=50)

    world = world_query_from_sqlite_path(sidecar)
    try:
        resolved = world.get_claim("claim_17")
        assert resolved is not None
        assert resolved.id == "claim_17"
    finally:
        world.close()


# ── concept reference lookup ──────────────────────────────────────────


def test_get_concept_resolves_namespaced_logical_id(tmp_path):
    sidecar = _build_concept_sidecar(tmp_path, n_rows=200)

    world = world_query_from_sqlite_path(sidecar)
    try:
        assert world.get_concept("test:concept_missing") is None
        resolved = world.get_concept("test:concept_42")
        assert resolved is not None
        assert resolved.id == "concept_42"
    finally:
        world.close()


def test_get_concept_canonical_name_path_still_reachable(tmp_path):
    sidecar = _build_concept_sidecar(tmp_path, n_rows=20)

    world = world_query_from_sqlite_path(sidecar)
    try:
        assert world.get_concept("test:concept_missing") is None
        resolved = world.get_concept("canonical_concept_7")
        assert resolved is not None
        assert resolved.id == "concept_7"
    finally:
        world.close()
