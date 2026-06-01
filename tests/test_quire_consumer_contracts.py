"""Propstore contracts that rely on Quire's generic GitStore substrate."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
import yaml
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.sources.declaration import (
    SourceDocument,
    source_document_payload,
)
from propstore.families.registry import SourceRef, semantic_import_roots
from propstore.repository import Repository
from propstore.source.common import initial_source_document
from propstore.importing.repository_import import (
    commit_repository_import,
    plan_repository_import,
)
from tests.conftest import make_claim_identity


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
            "id": local_id,
            "context": {"id": "ctx-default"},
        },
        sort_keys=False,
    ).encode("utf-8")


def _claim_artifact_path(local_id: str, *, namespace: str) -> str:
    artifact_id = make_claim_identity(local_id, namespace=namespace)["artifact_id"]
    return f"claims/{artifact_id.replace(':', '__')}.yaml"


def test_propstore_init_commits_gitignore_without_materializing_it(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    git = repo.git
    assert git is not None

    disk_gitignore = repo.root / ".gitignore"

    assert not disk_gitignore.exists()
    assert b"sidecar/" in git.read_file(".gitignore")
    assert b"*.sqlite" in git.read_file(".gitignore")
