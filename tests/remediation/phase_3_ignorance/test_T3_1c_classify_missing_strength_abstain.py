from propstore.heuristic.classify import classify_stance_from_llm_output
from propstore.provenance import ProvenanceStatus
from propstore.stances import StanceType


def test_missing_strength_routes_to_abstain_not_moderate() -> None:
    result = classify_stance_from_llm_output(
        {"type": "supports", "confidence": 0.9},
    )

    assert result.stance_type is StanceType.ABSTAIN
    assert result.opinion.uncertainty > 0.99
    assert result.opinion.provenance is not None
    assert result.opinion.provenance.status is ProvenanceStatus.VACUOUS
