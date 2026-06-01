from __future__ import annotations

import sqlite3

import pytest
import yaml

from propstore.repository import Repository
from propstore.compiler.workflows import write_repository_world_store as build_sidecar
from tests.conftest import normalize_claims_payload, normalize_concept_payloads
from tests.family_helpers import claim_artifact_commit_payloads


def test_sidecar_not_deleted_on_build_exception(tmp_path, monkeypatch) -> None:
    import propstore.compiler.workflows as build_module

    repo = _seed_claim_repo(tmp_path / "knowledge")
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    def fail_fts_population(*args, **kwargs) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(
        build_module,
        "populate_fts_index",
        fail_fts_population,
    )

    with pytest.raises(RuntimeError, match="boom"):
        build_sidecar(repo, sidecar_path, force=True)

    assert sidecar_path.exists(), "sidecar deleted on partial-build failure"
    conn = sqlite3.connect(sidecar_path)
    try:
        rows = conn.execute(
            "SELECT diagnostic_kind, severity, blocking, message "
            "FROM build_diagnostics WHERE diagnostic_kind='build_exception'"
        ).fetchall()
    finally:
        conn.close()

    assert rows
    assert rows[0][1:] == ("error", 1, "boom")
