from __future__ import annotations

from pathlib import Path

import yaml
from quire.git_store import GitStore

from propstore.families.claims.types import ClaimType
from propstore.families.claims.declaration import ClaimDocument
from propstore.families.contexts.declaration import ContextReferenceDocument
from propstore.families.identity.claims import compute_claim_version_id
from propstore.merge.merge_claims import MergeClaim
from propstore.repository import Repository
from propstore.storage.snapshot import RepositorySnapshot
from tests.conftest import normalize_claims_payload


def obs_claim(
    cid: str,
    statement: str,
    concepts: list[str],
    *,
    paper: str = "test_paper",
    page: int = 1,
    conditions: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": cid,
        "type": "observation",
        "statement": statement,
        "concepts": concepts,
        "provenance": {"paper": paper, "page": page},
    }
    if conditions:
        claim["conditions"] = conditions
    return claim


def param_claim(
    cid: str,
    concept: str,
    value: float,
    *,
    paper: str = "test_paper",
    page: int = 1,
    conditions: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": cid,
        "type": "parameter",
        "output_concept": concept,
        "value": value,
        "unit": "K",
        "provenance": {"paper": paper, "page": page},
    }
    if conditions:
        claim["conditions"] = conditions
    return claim


def merge_claim_without_paper(
    *,
    artifact_id: str,
    statement: str = "Missing provenance",
    concept: str = "concept_x",
) -> MergeClaim:
    merge_claim = MergeClaim.from_document(
        ClaimDocument(
            context=ContextReferenceDocument(id="default"),
            artifact_id=artifact_id,
            type=ClaimType.OBSERVATION,
            statement=statement,
            concepts=(concept,),
        )
    )
    if merge_claim is None:
        raise AssertionError("claim did not normalize to a merge claim")
    return merge_claim


def snapshot(kr: GitStore) -> RepositorySnapshot:
    if kr.root is None:
        raise ValueError("test snapshot requires a filesystem-backed git store")
    return RepositorySnapshot(Repository(Path(kr.root)))
