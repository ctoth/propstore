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


def test_concept_family_save_applies_identity_normalization_on_write(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.forms.save(
        FormRef("structural"),
        FormDocument(name="structural", dimensionless=True),
        message="Seed structural form",
    )
    ref = ConceptFileRef("demo")
    document = convert_document(
        normalize_canonical_concept_payload(
            {
                "canonical_name": "demo",
                "status": "accepted",
                "definition": "Demo concept.",
                "form": "structural",
            }
        ),
        ConceptDocument,
        source="concepts/demo.yaml",
    )

    repo.families.concepts.save(
        ref,
        document,
        message="Write demo concept",
    )
    loaded = repo.families.concepts.require(ref)

    assert loaded.artifact_id == derive_concept_artifact_id("propstore", "demo")
    assert loaded.logical_ids[0].namespace == "propstore"
    assert loaded.logical_ids[0].value == "demo"
    assert loaded.lexical_entry.canonical_form.written_rep == "demo"
    assert loaded.lexical_entry.physical_dimension_form == "structural"
    assert isinstance(loaded.version_id, str) and loaded.version_id.startswith(
        "sha256:"
    )
