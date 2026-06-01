"""Tests for direct repo emission of the formal merge object."""

from __future__ import annotations

import yaml

import propstore.storage as repo_module
from propstore.families.identity.claims import compute_claim_version_id
from quire.git_store import GitStore
from tests.git_store_helpers import init_store
from propstore.repository import Repository
from propstore.merge.merge_classifier import build_merge_framework
from propstore.storage.snapshot import RepositorySnapshot
from tests.conftest import make_claim_identity, normalize_claims_payload


def _obs_claim(
    cid: str,
    statement: str,
    concepts: list[str],
    *,
    conditions: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": cid,
        "type": "observation",
        "statement": statement,
        "concepts": concepts,
        "provenance": {"paper": "test_paper", "page": 1},
    }
    if conditions:
        claim["conditions"] = conditions
    return claim


def _param_claim(
    cid: str,
    concept: str,
    value: float,
    unit: str = "K",
    *,
    conditions: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": cid,
        "type": "parameter",
        "concept": concept,
        "value": value,
        "unit": unit,
        "concepts": [concept],
        "provenance": {"paper": "test_paper", "page": 1},
    }
    if conditions:
        claim["conditions"] = conditions
    return claim


def _snapshot(kr: GitStore) -> RepositorySnapshot:
    if kr.root is None:
        raise ValueError("test snapshot requires a filesystem-backed git store")
    return RepositorySnapshot(Repository(kr.root))


def test_repo_public_merge_surface_excludes_bridge_helpers() -> None:
    assert not hasattr(repo_module, "make_branch_assumption")
    assert not hasattr(repo_module, "branch_nogoods_from_merge")
    assert not hasattr(repo_module, "inject_branch_stances")
