from __future__ import annotations

from propstore.artifacts.documents.claims import ClaimDocument, StanceDocument
from propstore.core.claim_types import ClaimType
from propstore.artifacts.schema import DocumentSchemaError, convert_document_value
from propstore.artifacts.documents.sources import SourceClaimDocument, SourceStanceEntryDocument
from propstore.artifacts.documents.stances import StanceEntryDocument
from propstore.stances import StanceType

import pytest


def test_claim_document_rejects_invalid_claim_type() -> None:
    with pytest.raises(DocumentSchemaError):
        convert_document_value(
            {
                "artifact_id": "ps:claim:test",
                "version_id": "v1",
                "type": "not-a-claim-type",
                "context": {"id": "ctx_test"},
                "body": "def compute(x):\n    return x\n",
                "provenance": {"paper": "test_paper", "page": 1},
            },
            ClaimDocument,
            source="test-claim",
        )


def test_stance_document_rejects_invalid_stance_type() -> None:
    with pytest.raises(DocumentSchemaError):
        convert_document_value(
            {"type": "not-a-stance-type", "target": "ps:claim:other"},
            StanceDocument,
            source="test-stance",
        )


def test_claim_document_decodes_claim_and_inline_stance_enums() -> None:
    claim = convert_document_value(
        {
            "artifact_id": "ps:claim:test",
            "version_id": "v1",
            "type": "algorithm",
            "context": {"id": "ctx_test"},
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
