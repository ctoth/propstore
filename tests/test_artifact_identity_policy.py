from __future__ import annotations

from quire.documents import convert_document

from propstore.families.concepts.declaration import ConceptDocument
from propstore.families.forms.models import FORM_CHARTER
from propstore.families.identity.concepts import (
    derive_concept_artifact_id,
    normalize_canonical_concept_payload,
)
from propstore.families.registry import ConceptFileRef, FormRef
from propstore.repository import Repository

FormDocument = FORM_CHARTER.generated_document()
