"""Owner-layer loose-file materialize projection (Phase 10-0b).

``materialize_repository`` projects a committed store's semantic tree onto disk as
loose YAML source files (distinct from the content-addressed sidecar build). It is
the owner core the ``pks materialize`` adapter calls. A conflict (local edits
would be overwritten without ``force``) propagates as
:class:`MaterializeConflictError`; a malformed request lowers to
:class:`MaterializeError`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.app.materialize import (
    MaterializeError,
    MaterializeRequest,
    materialize_repository,
)
from propstore.families.concepts import Concept
from propstore.repository import Repository
from propstore.storage.snapshot import MaterializeConflictError


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    return repo


def test_materialize_repository_writes_loose_files(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = materialize_repository(repo, MaterializeRequest())

    assert report.source_commit
    assert any("concept/" in path for path in report.written_paths)
    # The loose source file is now on disk.
    assert any(path.suffix == ".yaml" for path in (repo.root / "concept").glob("*"))


def test_materialize_repository_conflict_propagates(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    materialize_repository(repo, MaterializeRequest())
    concept_files = list((repo.root / "concept").glob("*.yaml"))
    assert concept_files
    # Locally edit a materialized file; a re-materialize without force must refuse.
    concept_files[0].write_text("locally edited\n", encoding="utf-8")
    with pytest.raises(MaterializeConflictError):
        materialize_repository(repo, MaterializeRequest())


def test_materialize_repository_force_overwrites_local_edits(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    materialize_repository(repo, MaterializeRequest())
    concept_files = list((repo.root / "concept").glob("*.yaml"))
    concept_files[0].write_text("locally edited\n", encoding="utf-8")
    report = materialize_repository(repo, MaterializeRequest(force=True))
    assert report.force is True
    assert "locally edited" not in concept_files[0].read_text(encoding="utf-8")


def test_materialize_repository_rejects_commit_and_branch(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    head = repo.require_git().head_sha()
    with pytest.raises(MaterializeError):
        materialize_repository(
            repo, MaterializeRequest(commit=head, branch="master")
        )
