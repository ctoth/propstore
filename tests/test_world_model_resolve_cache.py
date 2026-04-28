"""Regression tests for resolve_claim / resolve_concept fallback memoization.

The WorldModel fallback branches used to issue a fresh full-table
``SELECT id, logical_ids_json FROM <table>`` on every miss, JSON-decoding
every row in Python. WorldModel is immutable per open sidecar, so the
logical-id → artifact-id mapping can be built once on first miss and
reused thereafter. These tests exercise that memoization by counting
SQL ``execute`` calls across repeated fallback lookups.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from propstore.sidecar.schema import build_minimal_world_model_schema
from propstore.world.model import WorldModel


# ── test fixture helpers ─────────────────────────────────────────────


def _insert_claim_row(
    conn: sqlite3.Connection, claim_id: str, seq: int
) -> None:
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


def _insert_concept(conn: sqlite3.Connection, concept_id: str) -> None:
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
        build_minimal_world_model_schema(conn)
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
        build_minimal_world_model_schema(conn)
        for idx in range(n_rows):
            _insert_concept(conn, f"concept_{idx}")
        conn.commit()
    finally:
        conn.close()
    return sidecar


class _CountingConnection:
    """Pass-through proxy around a ``sqlite3.Connection``.

    ``sqlite3.Connection.execute`` is a C-level attribute and cannot be
    reassigned on the instance. Instead the whole connection is wrapped
    and ``world._conn`` is repointed at the proxy — all
    ``self._conn.execute(...)`` calls inside ``WorldModel`` route through
    ``__getattr__`` → the wrapped ``execute`` method on this proxy.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.count = 0

    def execute(self, sql: str, *args: Any, **kwargs: Any) -> sqlite3.Cursor:
        self.count += 1
        return self._conn.execute(sql, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)


# ── resolve_claim ────────────────────────────────────────────────────


def test_resolve_claim_logical_id_lookup_does_not_scale_with_n(tmp_path):
    sidecar = _build_claim_sidecar(tmp_path, n_rows=200)

    world = WorldModel(sidecar_path=sidecar)
    try:
        counter = _CountingConnection(world._conn)
        world._conn = counter  # type: ignore[assignment]

        # First miss: must reach the fallback, which builds the cache.
        assert world.resolve_claim("test:claim_missing") is None
        n_first_miss = counter.count
        assert n_first_miss >= 1  # at least one SELECT landed

        # Second miss: cache is populated — must not rescan.
        assert world.resolve_claim("test:claim_still_missing") is None
        n_second_miss = counter.count - n_first_miss

        # Allow the two primary_id / primary_logical_id SELECTs (fast,
        # scoped), but the full-table logical-id scan must NOT repeat.
        assert n_second_miss < 3, (
            f"second miss issued {n_second_miss} execute calls; "
            "cache should have made the fallback a dict lookup"
        )

        # Existing logical id via the cache: also cheap, and returns the
        # right artifact id.
        before_hit = counter.count
        resolved = world.resolve_claim("test:claim_42")
        assert resolved == "claim_42"
        hit_delta = counter.count - before_hit
        assert hit_delta < 3
    finally:
        world.close()


def test_resolve_claim_cached_lookup_handles_bare_value_key(tmp_path):
    sidecar = _build_claim_sidecar(tmp_path, n_rows=50)

    world = WorldModel(sidecar_path=sidecar)
    try:
        # Prime the cache via a miss.
        assert world.resolve_claim("test:claim_missing") is None

        counter = _CountingConnection(world._conn)
        world._conn = counter  # type: ignore[assignment]

        # Bare ``value`` (not ``namespace:value``) must also be served
        # by the cache per the existing fallback contract.
        resolved = world.resolve_claim("claim_17")
        assert resolved == "claim_17"
        assert counter.count < 3
    finally:
        world.close()


# ── resolve_concept ──────────────────────────────────────────────────


def test_resolve_concept_logical_id_lookup_does_not_scale_with_n(tmp_path):
    sidecar = _build_concept_sidecar(tmp_path, n_rows=200)

    world = WorldModel(sidecar_path=sidecar)
    try:
        counter = _CountingConnection(world._conn)
        world._conn = counter  # type: ignore[assignment]

        # First miss: cache builds.
        assert world.resolve_concept("test:concept_missing") is None
        n_first_miss = counter.count
        assert n_first_miss >= 1

        # Second miss: must not rescan the full concept table. The
        # fallback is followed by a canonical-name SELECT on cache miss,
        # so the legitimate execute budget is alias + id + primary_id +
        # canonical_name = up to 4 statements.
        assert world.resolve_concept("test:concept_still_missing") is None
        n_second_miss = counter.count - n_first_miss
        assert n_second_miss < 5, (
            f"second concept miss issued {n_second_miss} execute calls; "
            "cache should have made the fallback a dict lookup"
        )

        # Existing logical id: dict hit, returns the right concept id.
        before_hit = counter.count
        resolved = world.resolve_concept("test:concept_42")
        assert resolved == "concept_42"
        hit_delta = counter.count - before_hit
        assert hit_delta < 5
    finally:
        world.close()


def test_resolve_concept_canonical_name_path_still_reachable(tmp_path):
    sidecar = _build_concept_sidecar(tmp_path, n_rows=20)

    world = WorldModel(sidecar_path=sidecar)
    try:
        # Force the cache to populate via a miss first.
        assert world.resolve_concept("test:concept_missing") is None

        # canonical_name lookup must still work after the cache is
        # populated — the fallback short-circuit must not swallow the
        # tail SELECT.
        resolved = world.resolve_concept("canonical_concept_7")
        assert resolved == "concept_7"
    finally:
        world.close()
