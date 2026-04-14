from __future__ import annotations

from pathlib import Path

from propstore.artifacts import SOURCE_DOCUMENT_FAMILY, SourceRef
from propstore.cli.repository import Repository
from propstore.source.common import initial_source_document, source_branch_name
from propstore.source_documents import SourceDocument


def test_snapshot_can_read_typed_document_from_branch(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    source_name = "paper_source"
    branch = source_branch_name(source_name)
    repo.snapshot.ensure_branch(branch)

    source_doc = initial_source_document(
        repo,
        source_name,
        kind="academic_paper",
        origin_type="manual",
        origin_value=source_name,
    )
    repo.artifacts.save(
        SOURCE_DOCUMENT_FAMILY,
        SourceRef(source_name),
        source_doc,
        message=f"Init source {source_name}",
    )

    loaded = repo.snapshot.read_document("source.yaml", SourceDocument, branch=branch)
    assert loaded is not None
    assert loaded.to_payload() == source_doc.to_payload()


def test_snapshot_lists_directory_entries_with_relpaths(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    source_name = "paper_source"
    branch = source_branch_name(source_name)
    repo.snapshot.ensure_branch(branch)

    source_doc = initial_source_document(
        repo,
        source_name,
        kind="academic_paper",
        origin_type="manual",
        origin_value=source_name,
    )
    repo.artifacts.save(
        SOURCE_DOCUMENT_FAMILY,
        SourceRef(source_name),
        source_doc,
        message=f"Init source {source_name}",
    )

    tip = repo.snapshot.branch_head(branch)
    assert tip is not None

    relpaths = {entry.relpath for entry in repo.snapshot.list_dir_entries("", commit=tip)}
    assert ".gitignore" in relpaths
    assert "source.yaml" in relpaths
