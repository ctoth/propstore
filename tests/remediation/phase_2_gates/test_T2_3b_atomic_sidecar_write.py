from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
import yaml

from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar


def _form_names(sidecar_path: Path) -> list[str]:
    conn = sqlite3.connect(sidecar_path)
    try:
        rows = conn.execute("SELECT name FROM form ORDER BY name").fetchall()
    finally:
        conn.close()
    return [str(row[0]) for row in rows]


def test_sidecar_rebuild_crash_before_replace_keeps_prior_sidecar_and_hash(
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
        "seed initial sidecar",
    )
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"
    hash_path = sidecar_path.with_suffix(".hash")

    assert build_sidecar(repo, sidecar_path, force=True) is True
    original_hash = hash_path.read_text().strip()
    assert _form_names(sidecar_path) == ["frequency"]

    repo.git.commit_files(
        {
            "forms/duration.yaml": yaml.dump(
                {"name": "duration", "dimensionless": False},
                sort_keys=False,
            ).encode(),
        },
        "add duration form",
    )
    original_replace = Path.replace

    def crash_before_sidecar_replace(self: Path, target: Path | str) -> Path:
        if Path(target) == sidecar_path:
            raise RuntimeError("rename crash")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", crash_before_sidecar_replace)

    with pytest.raises(RuntimeError, match="rename crash"):
        build_sidecar(repo, sidecar_path)

    assert hash_path.read_text().strip() == original_hash
    assert _form_names(sidecar_path) == ["frequency"]
