from __future__ import annotations

from propstore.families.documents.micropubs import MicropublicationDocument
from propstore.families.documents.sources import SourceClaimsDocument
from propstore.families.identity.micropubs import micropub_artifact_id
from propstore.source import finalize
from quire.documents import convert_document_value


def _micropub(payload: dict[str, object]) -> MicropublicationDocument:
    return convert_document_value(
        payload,
        MicropublicationDocument,
        source="tests:micropub.yaml",
    )


def test_same_source_and_claim_handle_different_payload_gets_different_id() -> None:
    first = _micropub({
        "artifact_id": "ps:micropub:old",
        "context": {"id": "ctx_alpha"},
        "claims": ["ps:claim:alpha"],
        "source": "tag:local@propstore,2026:source/demo",
        "evidence": [{"kind": "paper_page", "reference": "demo:1"}],
        "provenance": {"paper": "demo", "page": 1},
    })
    second = _micropub({
        "artifact_id": "ps:micropub:old",
        "context": {"id": "ctx_alpha"},
        "claims": ["ps:claim:alpha"],
        "source": "tag:local@propstore,2026:source/demo",
        "evidence": [{"kind": "paper_page", "reference": "demo:2"}],
        "provenance": {"paper": "demo", "page": 2},
    })

    assert micropub_artifact_id(first) != micropub_artifact_id(second)


def test_source_finalize_assigns_micropub_id_from_authored_payload() -> None:
    claims_doc = convert_document_value(
        {
            "claims": [
                {
                    "artifact_id": "ps:claim:alpha",
                    "context": "ctx_alpha",
                    "conditions": ["domain == 'argumentation'"],
                    "provenance": {"paper": "demo", "page": 1},
                }
            ],
        },
        SourceClaimsDocument,
        source="tests:claims.yaml",
    )

    micropubs_doc = finalize._compose_source_micropubs(
        source_id="tag:local@propstore,2026:source/demo",
        source_slug="demo",
        claims_doc=claims_doc,
    )

    assert micropubs_doc is not None
    micropub = micropubs_doc.micropubs[0]
    assert micropub.artifact_id == micropub_artifact_id(micropub)
    assert micropub.artifact_id.startswith("ni:///sha-256;")


def test_old_source_claim_handle_identity_surface_is_deleted() -> None:
    assert not hasattr(finalize, "_stable_micropub_artifact_id")
