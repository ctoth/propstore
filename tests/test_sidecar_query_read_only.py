from __future__ import annotations

import sqlite3

from propstore.sidecar.query import query_sidecar
from tests.web_demo_fixture import seed_web_demo_repository


def _journal_mode(path) -> str:
    with sqlite3.connect(path) as conn:
        return str(conn.execute("PRAGMA journal_mode").fetchone()[0])


def test_query_sidecar_does_not_switch_database_to_wal(tmp_path) -> None:
    fixture = seed_web_demo_repository(tmp_path)
    before_mode = _journal_mode(fixture.repo.sidecar_path)
    before_bytes = fixture.repo.sidecar_path.read_bytes()

    result = query_sidecar(fixture.repo, "SELECT 1 AS one")

    assert result.columns == ("one",)
    assert result.rows == (("1",),)
    assert _journal_mode(fixture.repo.sidecar_path) == before_mode
    assert fixture.repo.sidecar_path.read_bytes() == before_bytes
    assert not fixture.repo.sidecar_path.with_name("propstore.sqlite-wal").exists()
    assert not fixture.repo.sidecar_path.with_name("propstore.sqlite-shm").exists()
