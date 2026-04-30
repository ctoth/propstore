from __future__ import annotations

from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY, PropstoreFamily
from propstore.families.sameas.documents import (
    SameAsAssertionDocument,
    SameAsRelation,
)


def test_sameas_family_schema_exposes_graded_identity_vocab() -> None:
    family = PROPSTORE_FAMILY_REGISTRY.by_name(PropstoreFamily.SAMEAS.value)

    assert family.artifact_family.name == "same_as_file"
    assert {relation.value for relation in SameAsRelation} == {
        "sim:sameIndividual",
        "sim:claimsIdentical",
        "sim:almostSameAs",
    }
    assertion = SameAsAssertionDocument(
        left_artifact_id="ps:claim:left",
        right_artifact_id="ps:claim:right",
        relation=SameAsRelation.CLAIMS_IDENTICAL,
        evidence_source="paper_a",
        provenance={"paper": "paper_a", "page": 12},
    )

    assert assertion.to_payload() == {
        "left_artifact_id": "ps:claim:left",
        "right_artifact_id": "ps:claim:right",
        "relation": "sim:claimsIdentical",
        "evidence_source": "paper_a",
        "provenance": {"paper": "paper_a", "page": 12},
    }
