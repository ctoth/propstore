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


def _micropub_with_content_id(page: int) -> MicropublicationDocument:
    document = _micropub(page=page)
    return _micropub(page=page, artifact_id=micropub_artifact_id(document))
