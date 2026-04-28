from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from propstore.families.documents.micropubs import MicropublicationDocument
from propstore.families.identity.micropubs import (
    canonical_micropub_payload,
    micropub_artifact_id,
)
from propstore.uri import verify_ni_uri
from quire.documents import convert_document_value


def _micropub(*, claim_id: str, context_id: str, page: int) -> MicropublicationDocument:
    return convert_document_value(
        {
            "artifact_id": "ps:micropub:old",
            "version_id": "old-version",
            "context": {"id": context_id},
            "claims": [claim_id],
            "source": "tag:local@propstore,2026:source/demo",
            "evidence": [{"kind": "paper_page", "reference": f"demo:{page}"}],
            "provenance": {"paper": "demo", "page": page},
        },
        MicropublicationDocument,
        source="tests:micropub.yaml",
    )


def test_micropub_trusty_uri_verifies_exact_canonical_bytes() -> None:
    document = _micropub(
        claim_id="ps:claim:alpha",
        context_id="ctx_alpha",
        page=1,
    )
    uri = micropub_artifact_id(document)
    canonical_payload = canonical_micropub_payload(document)

    assert verify_ni_uri(uri, canonical_payload)
    assert not verify_ni_uri(uri, canonical_payload + b"\n")


@given(
    claim_id=st.from_regex(r"ps:claim:[a-z0-9_]{1,12}", fullmatch=True),
    context_id=st.from_regex(r"ctx_[a-z0-9_]{1,12}", fullmatch=True),
    page=st.integers(min_value=1, max_value=999),
)
@pytest.mark.property
def test_generated_micropub_trusty_uri_verification_round_trips(
    claim_id: str,
    context_id: str,
    page: int,
) -> None:
    document = _micropub(claim_id=claim_id, context_id=context_id, page=page)
    uri = micropub_artifact_id(document)
    canonical_payload = canonical_micropub_payload(document)
    changed = _micropub(claim_id=claim_id, context_id=context_id, page=page + 1)

    assert verify_ni_uri(uri, canonical_payload)
    assert not verify_ni_uri(uri, canonical_micropub_payload(changed))
