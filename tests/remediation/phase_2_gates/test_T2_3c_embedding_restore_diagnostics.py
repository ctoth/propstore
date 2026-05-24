from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from quire.sqlalchemy_store import readonly_session
from sqlalchemy import text
import yaml

from propstore.repository import Repository
from propstore.compiler.workflows import write_repository_world_store as build_sidecar
from propstore.families.world_charters import world_sqlalchemy_schema


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
        patch(
            "propstore.compiler.workflows.extract_embedding_snapshot",
            MagicMock(return_value=snapshot),
        ),
        patch(
            "propstore.compiler.workflows.restore_embedding_snapshot_to_session",
            MagicMock(side_effect=exc),
        ),
    ):
        assert build_sidecar(repo, sidecar_path, force=True) is True

    with readonly_session(sidecar_path, world_sqlalchemy_schema()) as derived:
        rows = derived.session.execute(
            text(
                """
            SELECT diagnostic_kind, severity, blocking, source_kind, source_ref, message
            FROM build_diagnostics
            WHERE diagnostic_kind = 'embedding_restore'
            """
            )
        ).fetchall()

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
