from __future__ import annotations

from pathlib import Path

import yaml
from quire.git_store import GitStore

from propstore.claims import claim_file_claims, loaded_claim_file_from_payload
from propstore.core.claim_types import ClaimType
from propstore.families.claims.documents import ClaimDocument
from propstore.families.contexts.documents import ContextReferenceDocument
from propstore.families.identity.claims import compute_claim_version_id
from propstore.merge.merge_claims import MergeClaim
from propstore.repository import Repository
from propstore.storage.snapshot import RepositorySnapshot
from tests.conftest import normalize_claims_payload


def claim_yaml(claims: list[dict], paper: str = "test_paper") -> bytes:
    doc = normalize_claims_payload(
        {
            "source": {
                "paper": paper,
                "extraction_model": "test",
                "extraction_date": "2026-01-01",
            },
            "claims": claims,
        }
    )
    return yaml.dump(doc, sort_keys=False).encode()


def claim_yaml_with_explicit_identities(
    claims: list[dict],
    paper: str = "test_paper",
) -> bytes:
    normalized = normalize_claims_payload(
        {
            "source": {
                "paper": paper,
                "extraction_model": "test",
                "extraction_date": "2026-01-01",
            },
            "claims": claims,
        }
    )
    rewritten_claims: list[dict] = []
    for original, normalized_claim in zip(claims, normalized["claims"], strict=True):
        merged = dict(normalized_claim)
        if "artifact_id" in original:
            merged["artifact_id"] = original["artifact_id"]
        if "logical_ids" in original:
            merged["logical_ids"] = original["logical_ids"]
        merged["version_id"] = compute_claim_version_id(merged)
        rewritten_claims.append(merged)
    normalized["claims"] = rewritten_claims
    return yaml.dump(normalized, sort_keys=False).encode()


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


def merge_claim_from_payload(claim: dict, *, paper: str = "test_paper") -> MergeClaim:
    payload = normalize_claims_payload(
        {
            "source": {"paper": paper, "extraction_model": "test"},
            "claims": [claim],
        }
    )
    loaded = loaded_claim_file_from_payload(
        filename="claims/test.yaml",
        source_path=None,
        data=payload,
    )
    document = claim_file_claims(loaded)[0]
    merge_claim = MergeClaim.from_document(document)
    if merge_claim is None:
        raise AssertionError("claim did not normalize to a merge claim")
    return merge_claim


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
