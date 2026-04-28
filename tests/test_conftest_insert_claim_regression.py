"""Regression test for ``tests/conftest.py::insert_claim`` seq=NULL bug.

Commit 7 (branch column on claim_core) discovered that ``insert_claim``
bound ``None`` into the ``seq`` column of ``claim_core``, which is
declared ``INTEGER NOT NULL`` in the canonical
``propstore/sidecar/schema.py`` schema. The bug was latent because the
only callers that exercised ``insert_claim`` against the tightened
schema worked around the defect with a private ``_insert_claim_row``
helper instead of using the conftest helper.

This regression test pins the contract on the legacy permissive
``create_argumentation_schema`` — where ``seq`` is nullable — so that
we can observe the fix directly (``seq`` defaults to a non-NULL int)
without coupling the test to the canonical schema's other constraints.
Before the fix the helper wrote ``seq = NULL``; after the fix it
writes ``seq = 0`` by default, and callers can override via kwarg.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from tests.conftest import create_argumentation_schema, insert_claim


def test_insert_claim_without_explicit_seq_defaults_to_non_null(
    tmp_path: Path,
) -> None:
    """``insert_claim`` must populate ``seq`` with a non-NULL default.

    Before the fix, the helper bound ``None`` into the ``seq`` column
    unconditionally. Against the canonical schema that raised
    ``IntegrityError``; against ``create_argumentation_schema`` (legacy,
    nullable) it silently wrote ``NULL``. This test exercises the
    legacy schema to keep the observation narrow: it asserts that the
    column now lands with a non-NULL integer, which proves the default
    was applied regardless of which schema the caller uses.
    """
    db_path = tmp_path / "sidecar.sqlite"
    conn = sqlite3.connect(db_path)
    try:
        create_argumentation_schema(conn)
        # No explicit seq kwarg — exercise the default path.
        insert_claim(
            conn,
            "claim_test",
            claim_type="measurement",
            concept_id="concept_test",
            value=1.0,
            source_paper="test_paper",
        )
        conn.commit()

        row = conn.execute(
            "SELECT seq FROM claim_core WHERE id = ?",
            ("claim_test",),
        ).fetchone()
        assert row is not None, "inserted claim_core row should be retrievable"
        assert row[0] is not None, (
            "seq column must be populated with a non-NULL default value"
        )
        assert isinstance(row[0], int), (
            f"seq must be an integer, got {type(row[0]).__name__}"
        )
    finally:
        conn.close()
