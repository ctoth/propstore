"""Tests for repo-facing merge query/report helpers."""

from __future__ import annotations

import yaml

from propstore.families.identity.claims import compute_claim_version_id
from propstore.families.identity.concepts import derive_concept_artifact_id
from quire.git_store import GitStore
from tests.git_store_helpers import init_store
from propstore.repository import Repository
from propstore.merge.merge_classifier import build_merge_framework
from propstore.merge.merge_report import summarize_merge_framework
from propstore.storage.snapshot import RepositorySnapshot
from tests.conftest import make_claim_identity, normalize_claims_payload


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
        "concept": concept,
        "value": value,
        "unit": "K",
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
