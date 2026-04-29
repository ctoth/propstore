from propstore.heuristic.classify import classify_stance_from_llm_output
from propstore.stances import StanceType


def test_classify_error_routes_to_abstain() -> None:
    result = classify_stance_from_llm_output({"type": "error"})

    assert result.stance_type is StanceType.ABSTAIN
    assert result.opinion.uncertainty > 0.99
