"""Regression tests for the new repository merge surface."""

from __future__ import annotations

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.families.identity.claims import compute_claim_version_id
from quire.git_store import GitStore
from tests.git_store_helpers import init_store
from propstore.repository import Repository
from propstore.merge.merge_classifier import build_merge_framework
from propstore.merge.merge_commit import create_merge_commit
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
    *,
    conditions: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": cid,
        "type": "parameter",
        "output_concept": concept,
        "value": value,
        "unit": "K",
        "provenance": {"paper": "test_paper", "page": 1},
    }
    if conditions:
        claim["conditions"] = conditions
    return claim


def _snapshot(kr: GitStore) -> RepositorySnapshot:
    if kr.root is None:
        raise ValueError("test snapshot requires a filesystem-backed git store")
    return RepositorySnapshot(Repository(kr.root))
