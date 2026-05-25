"""Regression test for duplicate claim identities during claim compilation."""

from __future__ import annotations

from quire.documents import LoadedDocument, document_to_payload

from propstore.claims import loaded_claim_file_from_payload
from propstore.compiler.ir import (
    ClaimCompilationBundle,
    SemanticClaim,
    SemanticClaimFile,
)
from propstore.families.claims.declaration import compile_claim_models
from propstore.families.claims.declaration import ClaimDocument


def _make_claim_entry(
    artifact_id: str,
    source_paper: str,
    *,
    version_id: str = "sha256:deadbeef",
) -> LoadedDocument[ClaimDocument]:
    return loaded_claim_file_from_payload(
        filename=f"{source_paper}.yaml",
        source_path=None,
        data={
            "artifact_id": artifact_id,
            "version_id": version_id,
            "type": "observation",
            "context": {"id": "ctx:test"},
            "source": {"paper": source_paper},
            "provenance": {"page": 0, "paper": source_paper},
            "concepts": ["ps:concept:shared"],
            "statement": "observation",
        },
    )


def _semantic_claim(entry: LoadedDocument[ClaimDocument]) -> SemanticClaim:
    payload = dict(document_to_payload(entry.document))
    artifact_id = payload["artifact_id"]
    claim_type = payload["type"]
    source = payload["source"]
    if (
        not isinstance(artifact_id, str)
        or not isinstance(claim_type, str)
        or not isinstance(source, dict)
        or not isinstance(source.get("paper"), str)
    ):
        raise TypeError("test claim payload must carry typed claim fields")
    return SemanticClaim(
        filename=entry.filename,
        source_paper=source["paper"],
        artifact_id=artifact_id,
        claim_type=claim_type,
        authored_claim=payload,
        resolved_claim=entry.document,
    )


def _bundle(*entries: LoadedDocument[ClaimDocument]) -> ClaimCompilationBundle:
    return ClaimCompilationBundle(
        context=None,
        normalized_claim_files=tuple(entries),
        semantic_files=tuple(
            SemanticClaimFile(
                loaded_entry=entry,
                normalized_entry=entry,
                claims=(_semantic_claim(entry),),
            )
            for entry in entries
        ),
    )


def test_compile_claim_models_tolerates_duplicate_artifact_ids() -> None:
    models = compile_claim_models(
        _bundle(
            _make_claim_entry("ps:claim:shared0001", "paper-alpha"),
            _make_claim_entry("ps:claim:shared0001", "paper-alpha-variant"),
        ),
        concept_registry={},
    )

    assert [claim.id for claim in models.claims] == ["ps:claim:shared0001"]
    assert [payload.claim_id for payload in models.numeric_payloads] == [
        "ps:claim:shared0001"
    ]
    assert [payload.claim_id for payload in models.text_payloads] == [
        "ps:claim:shared0001"
    ]
    assert [payload.claim_id for payload in models.algorithm_payloads] == [
        "ps:claim:shared0001"
    ]
