from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import yaml

from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar


@pytest.mark.parametrize(
    ("exc", "message"),
    [
        (ImportError("missing vec extension"), "missing vec extension"),
        (RuntimeError("restore boom"), "restore boom"),
    ],
)
def test_embedding_restore_failures_write_diagnostics(
    tmp_path: Path,
    exc: Exception,
    message: str,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files(
        {
            "forms/frequency.yaml": yaml.dump(
                {"name": "frequency", "dimensionless": False},
                sort_keys=False,
            ).encode(),
        },
        "seed embedding restore diagnostic test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"

    assert build_sidecar(repo, sidecar_path, force=True) is True
    snapshot = SimpleNamespace(
        models=(),
        claim_vectors={},
        concept_vectors={},
    )

    with (
        patch("propstore.embed._load_vec_extension", MagicMock()),
        patch("propstore.embed.extract_embeddings", MagicMock(return_value=snapshot)),
        patch("propstore.embed.restore_embeddings", MagicMock(side_effect=exc)),
    ):
        assert build_sidecar(repo, sidecar_path, force=True) is True

    conn = sqlite3.connect(sidecar_path)
    try:
        rows = conn.execute(
            """
            SELECT diagnostic_kind, severity, blocking, source_kind, source_ref, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'embedding_restore'
            """
        ).fetchall()
    finally:
        conn.close()

    assert rows == [
        (
            "embedding_restore",
            "warning",
            0,
            "embedding",
            "restore",
            f"embedding restore failed: {message}",
        )
    ]
