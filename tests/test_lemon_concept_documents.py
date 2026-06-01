from __future__ import annotations

import pytest

from quire.documents import DocumentSchemaError, convert_document

from propstore.families.concepts.declaration import ConceptDocument
from propstore.families.forms.models import FORM_CHARTER
from propstore.families.registry import ConceptFileRef, FormRef

from propstore.families.concepts.stages import parse_concept_record_document
from propstore.repository import Repository

FormDocument = FORM_CHARTER.generated_document()


def test_concept_document_rejects_flat_pre_lemon_shape(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    with pytest.raises(DocumentSchemaError):
        convert_document(
            {
                "canonical_name": "temperature",
                "status": "accepted",
                "definition": "A thermal state quantity.",
                "form": "temperature",
            },
            ConceptDocument,
            source="concepts/temperature.yaml",
        )
