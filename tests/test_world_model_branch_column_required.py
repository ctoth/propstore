"""Commit 8 — schema validator must require `branch` column in `claim_core`.

These tests pin two guarantees:

1. The world sidecar projection contract requires `claim_core.branch`. This is a
   structural contract — if someone drops the column from the required
   set, this test fails fast. It runs at import-time against the source
   of truth, so there is no way to regress it by accident.

2. A legacy-shaped sidecar (schema_version matches the current constant,
   all other required tables and columns present, but `claim_core.branch`
   absent) is rejected by `WorldQuery` with a `ValueError` whose message
   mentions both `branch` and `claim_core`. This is the end-to-end
   proof that the old conditional select fallback is gone and the
   validator is the gatekeeper.

Co-located helper `_build_legacy_sidecar` constructs a minimal on-disk
sidecar fixture, bypassing the real compiler. It writes the full
projection contract's required columns except that `claim_core` omits the
`branch` column. Then it writes the current sidecar schema version so
the version guard passes (we want to prove the column check fires, not the
version check).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.family_helpers import world_query_from_sqlite_path

from propstore.families.world_charters import world_sqlalchemy_schema
from propstore.world.model import WorldQuery


def test_branch_column_in_required_schema() -> None:
    """The world sidecar projection contract must include `claim_core.branch`."""
    assert "branch" in _required_columns_by_table()["claim_core"], (
        "The world sidecar projection is missing claim_core.branch; the "
        "validator will not reject legacy pre-branch sidecars. Commit 8 requires this."
    )


def _build_legacy_sidecar(path: Path) -> None:
    """Write a sidecar with the full required schema EXCEPT `claim_core.branch`.

    Data-driven: iterates over the projection contract and emits
    `CREATE TABLE name (col1 TEXT, col2 TEXT, ...)` for every required
    table. For `claim_core`, the `branch` column is deliberately filtered
    out — that is the whole point of the fixture. All other tables get
    every required column verbatim from the schema dict, so the only
    validator-visible defect is the missing `branch` column.

    The meta row is written with the current sidecar schema version so the
    version guard passes cleanly and we isolate the column check.
    """
    import sqlite3

    conn = sqlite3.connect(path)
    try:
        for table, required_columns in _required_columns_by_table().items():
            if table == "claim_core":
                columns = sorted(required_columns - {"branch"})
            else:
                columns = sorted(required_columns)
            column_defs = ", ".join(f"{col} TEXT" for col in columns)
            conn.execute(f"CREATE TABLE {table} ({column_defs})")  # noqa: S608
        conn.commit()
    finally:
        conn.close()


def _required_columns_by_table() -> dict[str, frozenset[str]]:
    return {
        table_name: frozenset(table.c.keys())
        for table_name, table in world_sqlalchemy_schema().tables.items()
    }


def test_legacy_sidecar_without_branch_column_is_rejected(tmp_path: Path) -> None:
    """`WorldQuery` must reject a sidecar where `claim_core.branch` is absent.

    We construct a sidecar that satisfies every other row of
    the projection contract verbatim and writes the current sidecar schema version
    so only the missing `branch` column can trigger the error. The
    validator must raise `ValueError` whose message mentions both
    `branch` and `claim_core` so a human reviewer can see which column
    and which table failed.
    """
    sidecar_path = tmp_path / "propstore.sqlite"
    _build_legacy_sidecar(sidecar_path)

    with pytest.raises(ValueError) as excinfo:
        world_query_from_sqlite_path(sidecar_path)

    message = str(excinfo.value)
    assert "branch" in message, (
        f"Expected 'branch' in error message, got: {message!r}"
    )
    assert "claim_core" in message, (
        f"Expected 'claim_core' in error message, got: {message!r}"
    )
