"""Propstore contracts that rely on Quire's generic GitStore substrate."""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
import yaml
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.documents.sources import SourceDocument
from propstore.families.registry import SourceRef, semantic_import_roots
from propstore.repository import Repository
from propstore.source.common import initial_source_document, source_branch_name
from propstore.storage.repository_import import commit_repository_import, plan_repository_import


_SLUG = st.from_regex(r"[a-z][a-z0-9_]{0,12}", fullmatch=True)
_CLAIM_IDS = st.lists(
    st.from_regex(r"claim_[a-z]{1,4}", fullmatch=True),
    min_size=1,
    max_size=4,
    unique=True,
)
_PAYLOAD = st.binary(min_size=0, max_size=512)


def _init_project(root: Path) -> Repository:
    return Repository.init(root / "knowledge")


def _raw_claim_yaml(local_id: str) -> bytes:
    return yaml.safe_dump(
        {
            "claims": [
                {
                    "id": local_id,
                    "context": {"id": "ctx-default"},
                }
            ]
        },
        sort_keys=False,
    ).encode("utf-8")


def test_propstore_init_materializes_and_commits_gitignore(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    git = repo.git
    assert git is not None

    disk_gitignore = repo.root / ".gitignore"

    assert disk_gitignore.is_file()
    assert disk_gitignore.read_bytes() == git.read_file(".gitignore")
    assert b"sidecar/" in disk_gitignore.read_bytes()
    assert b"*.sqlite" in disk_gitignore.read_bytes()


@settings(
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(payload=_PAYLOAD)
def test_propstore_sync_preserves_ignored_runtime_outputs(tmp_path: Path, payload: bytes) -> None:
    repo = Repository.init(tmp_path / f"project_{uuid4().hex}" / "knowledge")
    git = repo.git
    assert git is not None
    git.commit_files({"claims/committed.yaml": _raw_claim_yaml("claim_a")}, "seed claim")
    git.sync_worktree()

    sidecar = repo.root / "sidecar" / "propstore.sqlite"
    hash_file = repo.root / "sidecar" / "propstore.hash"
    provenance_file = repo.root / "claims" / "local.provenance"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_bytes(payload)
    hash_file.write_bytes(payload)
    provenance_file.write_bytes(payload)

    git.sync_worktree()

    assert sidecar.read_bytes() == payload
    assert hash_file.read_bytes() == payload
    assert provenance_file.read_bytes() == payload


@settings(
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(claim_ids=_CLAIM_IDS, payload=_PAYLOAD)
def test_repository_import_uses_committed_semantic_snapshot_only(
    tmp_path: Path,
    claim_ids: list[str],
    payload: bytes,
) -> None:
    destination = _init_project(tmp_path / f"dest_{uuid4().hex}")
    source = _init_project(tmp_path / f"source_{uuid4().hex}")
    source_git = source.git
    assert source_git is not None
    source_git.commit_files(
        {
            **{
                f"claims/{claim_id}.yaml": _raw_claim_yaml(claim_id)
                for claim_id in claim_ids
            },
            "README.md": b"not a semantic import root\n",
            "sidecar/propstore.sqlite": payload,
        },
        "seed source",
    )
    source_git.sync_worktree()
    uncommitted_claim = source.root / "claims" / "uncommitted.yaml"
    uncommitted_claim.write_bytes(_raw_claim_yaml("claim_uncommitted"))

    plan = plan_repository_import(destination, source.root.parent)
    result = commit_repository_import(destination, plan)

    imported_paths = {
        snapshot_file.relpath
        for snapshot_file in destination.snapshot.files(
            commit=result.commit_sha,
            roots=semantic_import_roots(),
        )
    }

    assert imported_paths == {f"claims/{claim_id}.yaml" for claim_id in claim_ids}
    assert "README.md" not in plan.touched_paths
    assert "sidecar/propstore.sqlite" not in plan.touched_paths
    assert "claims/uncommitted.yaml" not in plan.touched_paths
    assert result.source_commit == source_git.head_sha()


@settings(
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(first=_SLUG, second=_SLUG)
def test_source_documents_with_same_path_are_isolated_by_source_branch(
    tmp_path: Path,
    first: str,
    second: str,
) -> None:
    assume(first != second)
    repo = Repository.init(tmp_path / f"project_{uuid4().hex}" / "knowledge")

    first_branch = source_branch_name(first)
    second_branch = source_branch_name(second)
    repo.snapshot.ensure_branch(first_branch)
    repo.snapshot.ensure_branch(second_branch)
    first_doc = initial_source_document(
        repo,
        first,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value=first,
    )
    second_doc = initial_source_document(
        repo,
        second,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value=second,
    )

    repo.families.source_documents.save(SourceRef(first), first_doc, message=f"Init {first}")
    repo.families.source_documents.save(SourceRef(second), second_doc, message=f"Init {second}")

    loaded_first = repo.snapshot.read_document("source.yaml", SourceDocument, branch=first_branch)
    loaded_second = repo.snapshot.read_document("source.yaml", SourceDocument, branch=second_branch)

    assert loaded_first is not None
    assert loaded_second is not None
    assert loaded_first.to_payload() == first_doc.to_payload()
    assert loaded_second.to_payload() == second_doc.to_payload()
    assert loaded_first.to_payload() != loaded_second.to_payload()
    assert repo.snapshot.read_document("source.yaml", SourceDocument, branch="master") is None
