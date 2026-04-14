from __future__ import annotations

from typing import get_type_hints

from propstore.claim_documents import ClaimDocument, StanceDocument
from propstore.core.claim_types import ClaimType
from propstore.document_schema import convert_document_value
from propstore.source_documents import SourceClaimDocument, SourceStanceEntryDocument
from propstore.stance_documents import StanceEntryDocument
from propstore.stances import StanceType


def test_claim_and_stance_document_annotations_use_enums() -> None:
    assert get_type_hints(ClaimDocument)["type"] == ClaimType | None
    assert get_type_hints(SourceClaimDocument)["type"] == ClaimType | None
    assert get_type_hints(StanceDocument)["type"] == StanceType
    assert get_type_hints(StanceEntryDocument)["type"] == StanceType | None
    assert get_type_hints(SourceStanceEntryDocument)["type"] == StanceType | None


def test_claim_document_decodes_claim_and_inline_stance_enums() -> None:
    claim = convert_document_value(
        {
            "artifact_id": "ps:claim:test",
            "version_id": "v1",
            "type": "algorithm",
            "body": "def compute(x):\n    return x\n",
            "variables": [{"name": "x", "concept": "concept1"}],
            "stances": [{"type": "supports", "target": "ps:claim:other"}],
            "provenance": {"paper": "test_paper", "page": 1},
        },
        ClaimDocument,
        source="test-claim",
    )

    assert claim.type is ClaimType.ALGORITHM
    assert claim.stances[0].type is StanceType.SUPPORTS


def test_source_documents_decode_claim_and_stance_enums() -> None:
    source_claim = convert_document_value(
        {
            "id": "claim1",
            "type": "observation",
            "statement": "Observed something.",
            "provenance": {"paper": "paper", "page": 1},
        },
        SourceClaimDocument,
        source="source-claim",
    )
    source_stance = convert_document_value(
        {"source_claim": "claim1", "target": "claim2", "type": "rebuts"},
        SourceStanceEntryDocument,
        source="source-stance",
    )
    stance_file_entry = convert_document_value(
        {"source_claim": "claim1", "target": "claim2", "type": "undercuts"},
        StanceEntryDocument,
        source="stance-entry",
    )

    assert source_claim.type is ClaimType.OBSERVATION
    assert source_stance.type is StanceType.REBUTS
    assert stance_file_entry.type is StanceType.UNDERCUTS
