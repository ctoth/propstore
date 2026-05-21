from propstore.preference import metadata_strength_vector
from propstore.provenance import ProvenanceStatus
from tests.typed_family_fixtures import claim_from_payload


def test_metadata_strength_vector_vacuous_on_missing() -> None:
    v = metadata_strength_vector(claim_from_payload({"id": "claim:missing-metadata"}))
    assert v.uncertainty > 0.99
    assert v.provenance is not None
    assert v.provenance.status is ProvenanceStatus.VACUOUS
