from __future__ import annotations

from propstore.families.contexts.documents import ContextReferenceDocument
from propstore.families.documents.micropubs import MicropublicationDocument
from propstore.families.identity.micropubs import micropub_artifact_id
from propstore.families.identity.micropubs import canonical_micropub_payload


def test_micropub_identity_is_trusty_uri_and_verifiable() -> None:
    from propstore.provenance.trusty import verify_ni_uri

    document = MicropublicationDocument(
        artifact_id="placeholder",
        context=ContextReferenceDocument(id="context:one"),
        claims=("claim:one",),
    )

    artifact_id = micropub_artifact_id(document)

    assert artifact_id.startswith("ni:///sha-256;")
    assert not artifact_id.startswith("ps:micropub:")
    assert verify_ni_uri(artifact_id, canonical_micropub_payload(document)) is True
