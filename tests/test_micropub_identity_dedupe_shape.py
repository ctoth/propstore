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
