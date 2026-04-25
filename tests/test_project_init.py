from __future__ import annotations

from pathlib import Path

from propstore.app.project_init import initialize_project
from propstore.repository import Repository


def test_initialize_project_seeds_packaged_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"

    report = initialize_project(root)

    assert report.initialized is True
    assert not (root / "forms").exists()
    assert not (root / "concepts").exists()
    repo = Repository.find(root)
    entries = repo.git.flat_tree_entries()
    assert any(path.startswith("forms/") and path.endswith(".yaml") for path in entries)
    assert any(path.startswith("concepts/") and path.endswith(".yaml") for path in entries)


def test_initialize_project_reports_existing_project(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    initialize_project(root)

    report = initialize_project(root)

    assert report.initialized is False
    assert report.root == root
