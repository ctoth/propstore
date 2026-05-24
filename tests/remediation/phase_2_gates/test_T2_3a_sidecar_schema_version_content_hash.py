from __future__ import annotations

from pathlib import Path

import yaml

from propstore.repository import Repository
import propstore.compiler.workflows as sidecar_build


def test_world_store_content_hash_changes_on_schema_version_bump(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files(
        {
            "forms/frequency.yaml": yaml.dump(
                {"name": "frequency", "dimensionless": False},
                sort_keys=False,
            ).encode(),
        },
        "seed schema-version hash test",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"
    hash_path = sidecar_path.with_suffix(".hash")

    assert sidecar_build.write_repository_world_store(repo, sidecar_path, force=True) is True
    first_hash = hash_path.read_text().strip()

    monkeypatch.setattr(
        sidecar_build,
        "PROPSTORE_WORLD_SCHEMA_VERSION",
        sidecar_build.PROPSTORE_WORLD_SCHEMA_VERSION + 1,
    )

    assert sidecar_build.write_repository_world_store(repo, sidecar_path) is True
    second_hash = hash_path.read_text().strip()

    assert second_hash != first_hash
