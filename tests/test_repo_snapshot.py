from __future__ import annotations

from pathlib import Path

from propstore.families.registry import SourceRef
from propstore.repository import Repository
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.source.common import initial_source_document
from propstore.families.sources.declaration import (
    SourceDocument,
    source_document_payload,
)
from propstore.storage.snapshot import MaterializeConflictError


def test_snapshot_lists_directory_entries_with_relpaths(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    source_name = "paper_source"
    branch = repo.families.source_documents.address(SourceRef(source_name)).branch
    repo.git.create_branch(branch)

    source_doc = initial_source_document(
        repo,
        source_name,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value=source_name,
    )
    repo.families.source_documents.save(
        SourceRef(source_name),
        source_doc,
        message=f"Init source {source_name}",
    )

    tip = repo.git.branch_sha(branch)
    assert tip is not None

    relpaths = {entry.relpath for entry in repo.git.iter_tree_files(commit=tip)}
    assert ".gitignore" in relpaths
    assert "source.yaml" in relpaths


def test_snapshot_materialize_writes_commit_files_and_refuses_conflicts(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    git = repo.git
    git.commit_files({"concepts/example.yaml": b"name: example\n"}, "seed concept")

    report = repo.snapshot.materialize()

    assert report.source_commit == git.head_sha()
    assert (repo.root / ".gitignore").is_file()
    assert (repo.root / "concepts" / "example.yaml").read_bytes() == b"name: example\n"
    assert "concepts/example.yaml" in report.written_paths

    (repo.root / "concepts" / "example.yaml").write_bytes(b"local edit\n")
    try:
        repo.snapshot.materialize()
    except MaterializeConflictError as exc:
        assert "concepts/example.yaml" in str(exc)
    else:
        raise AssertionError("materialize should reject local content conflicts")

    forced = repo.snapshot.materialize(force=True)
    assert forced.force is True
    assert (repo.root / "concepts" / "example.yaml").read_bytes() == b"name: example\n"


def test_snapshot_materialize_clean_preserves_ignored_runtime_outputs(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files({"concepts/example.yaml": b"name: example\n"}, "seed concept")
    repo.snapshot.materialize()

    stale = repo.root / "concepts" / "stale.yaml"
    provenance = repo.root / "concepts" / "local.provenance"
    sidecar = repo.root / "sidecar" / "propstore.sqlite"
    stale.write_bytes(b"stale\n")
    provenance.write_bytes(b"runtime\n")
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_bytes(b"runtime db\n")

    report = repo.snapshot.materialize(clean=True)

    assert "concepts/stale.yaml" in report.deleted_stale_paths
    assert "concepts/local.provenance" in report.skipped_ignored_paths
    assert not stale.exists()
    assert provenance.read_bytes() == b"runtime\n"
    assert sidecar.read_bytes() == b"runtime db\n"
