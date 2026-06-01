"""Tests for branch-local structured projection into merge summaries."""

from __future__ import annotations

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from quire.git_store import GitStore
from propstore.families.identity.stances import stamp_stance_artifact_id
from tests.git_store_helpers import init_store
from propstore.repository import Repository
from propstore.storage.snapshot import RepositorySnapshot
from propstore.merge.structured_merge import (
    build_branch_structured_summary,
    build_structured_merge_candidates,
)
from tests.conftest import make_claim_identity, normalize_claims_payload


def _artifact_id(local_id: str, *, paper: str = "test_paper") -> str:
    return make_claim_identity(local_id, namespace=paper)["artifact_id"]


def _obs_claim(cid: str, statement: str) -> dict:
    return {
        "id": cid,
        "type": "observation",
        "statement": statement,
        "concepts": ["concept_x"],
        "confidence": 0.5,
        "sample_size": 10,
        "provenance": {"paper": "test_paper", "page": 1},
    }


def _snapshot(kr: GitStore) -> RepositorySnapshot:
    if kr.root is None:
        raise ValueError("test snapshot requires a filesystem-backed git store")
    return RepositorySnapshot(Repository(kr.root))
