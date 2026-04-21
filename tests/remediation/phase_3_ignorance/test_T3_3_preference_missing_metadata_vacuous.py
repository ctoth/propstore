from propstore.preference import metadata_strength_vector
from propstore.provenance import ProvenanceStatus


def test_metadata_strength_vector_vacuous_on_missing() -> None:
    v = metadata_strength_vector({})
    assert v.uncertainty > 0.99
    assert v.provenance is not None
    assert v.provenance.status is ProvenanceStatus.VACUOUS
