from __future__ import annotations

from propstore.families.registry import ConceptFileRef
from propstore.families.identity.concepts import (
    derive_concept_artifact_id,
    normalize_canonical_concept_payload,
)
from propstore.repository import Repository


def test_normalize_canonical_concept_payload_preserves_propstore_handle_and_updates_primary_identity() -> None:
    normalized = normalize_canonical_concept_payload(
        {
            "canonical_name": "vocal_task",
            "domain": "speech",
            "status": "accepted",
            "definition": "A task produced with the vocal tract.",
            "form": "structural",
            "logical_ids": [{"namespace": "propstore", "value": "task"}],
        },
        local_handle="task",
    )

    assert normalized["artifact_id"] == derive_concept_artifact_id("propstore", "task")
    assert normalized["logical_ids"][0] == {"namespace": "speech", "value": "vocal_task"}
    assert {"namespace": "propstore", "value": "task"} in normalized["logical_ids"]
    assert normalized["version_id"].startswith("sha256:")


def test_concept_family_save_applies_identity_normalization_on_write(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    ref = ConceptFileRef("demo")
    document = repo.families.concepts.coerce(
        normalize_canonical_concept_payload({
            "canonical_name": "demo",
            "status": "accepted",
            "definition": "Demo concept.",
            "form": "structural",
        }),
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
    assert isinstance(loaded.version_id, str) and loaded.version_id.startswith("sha256:")
