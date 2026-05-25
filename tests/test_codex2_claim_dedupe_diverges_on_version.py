from __future__ import annotations

from quire.documents import LoadedDocument, document_to_payload

from propstore.compiler.ir import (
    ClaimCompilationBundle,
    SemanticClaim,
    SemanticClaimFile,
)
from propstore.families.claims.declaration import compile_claim_models
from propstore.families.claims.declaration import ClaimDocument
from propstore.claims import loaded_claim_file_from_payload


def _claim_entry(
    artifact_id: str,
    *,
    version_id: str,
    concepts: tuple[str, ...] = ("ps:concept:velocity",),
    statement: str = "observation",
) -> LoadedDocument[ClaimDocument]:
    return loaded_claim_file_from_payload(
        filename=f"{artifact_id.removeprefix('ps:claim:')}.yaml",
        source_path=None,
        data={
            "artifact_id": artifact_id,
            "version_id": version_id,
            "type": "observation",
            "context": {"id": "ctx:test"},
            "source": {"paper": "demo"},
            "provenance": {"page": 0, "paper": "demo"},
            "concepts": list(concepts),
            "statement": statement,
        },
    )


def _semantic_claim(entry: LoadedDocument[ClaimDocument]) -> SemanticClaim:
    payload = dict(document_to_payload(entry.document))
    artifact_id = payload["artifact_id"]
    claim_type = payload["type"]
    if not isinstance(artifact_id, str) or not isinstance(claim_type, str):
        raise TypeError("test claim payload must carry typed identity fields")
    return SemanticClaim(
        filename=entry.filename,
        source_paper="demo",
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


def test_compile_claim_models_reports_same_logical_id_different_version() -> None:
    models = compile_claim_models(
        _bundle(
            _claim_entry("ps:claim:shared", version_id="sha256:first"),
            _claim_entry("ps:claim:shared", version_id="sha256:second"),
        ),
        concept_registry={},
    )

    assert [claim.version_id for claim in models.claims] == ["sha256:first"]
    assert [
        (diagnostic.artifact_id, diagnostic.diagnostic_kind)
        for diagnostic in models.quarantine_diagnostics
    ] == [("ps:claim:shared", "claim_version_conflict")]


def test_compile_claim_models_dedupes_duplicate_claim_concept_links() -> None:
    models = compile_claim_models(
        _bundle(
            _claim_entry("ps:claim:linked", version_id="sha256:same"),
            _claim_entry("ps:claim:linked", version_id="sha256:same"),
        ),
        concept_registry={},
    )

    assert [
        (link.claim_id, link.concept_id, link.role.value, link.ordinal)
        for link in models.concept_links
    ] == [("ps:claim:linked", "ps:concept:velocity", "about", 0)]
