from __future__ import annotations

from propstore.families.claims.declaration import SOURCE_CLAIM_BATCH_SPEC
from propstore.families.micropublications.declaration import MicropublicationDocument
from propstore.families.identity.micropubs import micropub_artifact_id
from propstore.source import finalize
from quire.documents import (
    convert_document_value,
    decode_document_batch_bytes,
    encode_yaml_value,
)


def _micropub(payload: dict[str, object]) -> MicropublicationDocument:
    return convert_document_value(
        payload,
        MicropublicationDocument,
        source="tests:micropub.yaml",
    )


def test_old_source_claim_handle_identity_surface_is_deleted() -> None:
    assert not hasattr(finalize, "_stable_micropub_artifact_id")
    assert not hasattr(finalize, "_stamp_micropub_identity")
