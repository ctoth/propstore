from __future__ import annotations

from quire.documents import convert_document_value

from propstore.families.claims.references import (
    ImportedClaimReference,
    imported_claim_reference_index,
)
from propstore.families.identity.micropubs import micropub_artifact_id
from propstore.families.micropublications.declaration import (
    MicropublicationDocument,
    compile_micropublication_models_with_diagnostics,
)


def _micropub(
    *,
    page: int,
    artifact_id: str = "ps:micropub:declared",
    version_id: str = "declared-version",
) -> MicropublicationDocument:
    return convert_document_value(
        {
            "artifact_id": artifact_id,
            "version_id": version_id,
            "context": {"id": "ctx_alpha"},
            "claims": ["claim-alpha"],
            "source": "tag:local@propstore,2026:source/demo",
            "evidence": [{"kind": "paper_page", "reference": f"demo:{page}"}],
            "provenance": {"paper": "demo", "page": page},
        },
        MicropublicationDocument,
        source="tests:micropub.yaml",
    )


def _micropub_with_content_id(page: int) -> MicropublicationDocument:
    document = _micropub(page=page)
    return _micropub(page=page, artifact_id=micropub_artifact_id(document))


def test_micropublication_identity_uses_canonical_payload_not_declared_ids() -> None:
    base = _micropub(page=1, artifact_id="declared-a", version_id="version-a")
    renamed = _micropub(page=1, artifact_id="declared-b", version_id="version-b")
    changed = _micropub(page=2, artifact_id="declared-a", version_id="version-a")

    assert micropub_artifact_id(base) == micropub_artifact_id(renamed)
    assert micropub_artifact_id(base) != micropub_artifact_id(changed)


def test_micropublication_compiler_dedupes_only_matching_payload_ids() -> None:
    first = _micropub_with_content_id(page=1)
    duplicate = _micropub_with_content_id(page=1)
    changed = _micropub_with_content_id(page=2)
    assert first.artifact_id == duplicate.artifact_id
    assert first.artifact_id != changed.artifact_id

    claim_index = imported_claim_reference_index(
        (ImportedClaimReference("claim-alpha", "ps:claim:alpha"),)
    )
    (micropublications, claim_links), diagnostics = (
        compile_micropublication_models_with_diagnostics(
            (
                ("demo/micropubs/first.yaml", first),
                ("demo/micropubs/first-copy.yaml", duplicate),
                ("demo/micropubs/changed.yaml", changed),
            ),
            claim_index,
        )
    )

    assert diagnostics == ()
    assert {micropublication.id for micropublication in micropublications} == {
        first.artifact_id,
        changed.artifact_id,
    }
    assert {
        (link.micropublication_id, link.claim_id) for link in claim_links
    } == {
        (first.artifact_id, "ps:claim:alpha"),
        (changed.artifact_id, "ps:claim:alpha"),
    }
