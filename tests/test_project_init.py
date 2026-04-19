from __future__ import annotations

from pathlib import Path

from propstore.app.project_init import initialize_project


def test_initialize_project_seeds_packaged_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"

    report = initialize_project(root)

    assert report.initialized is True
    assert root / "concepts" in report.paths
    assert root / "forms" in report.paths
    assert (root / "forms").is_dir()
    assert any((root / "forms").glob("*.yaml"))
    assert any((root / "concepts").glob("*.yaml"))


def test_initialize_project_reports_existing_project(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    initialize_project(root)

    report = initialize_project(root)

    assert report.initialized is False
    assert report.root == root
