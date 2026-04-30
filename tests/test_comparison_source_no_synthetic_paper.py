from __future__ import annotations

import pytest

from propstore.merge.merge_classifier import MergeComparisonProvenanceError, _classify_pair
from tests.ws_l_merge_helpers import merge_claim_without_paper


def test_classify_pair_rejects_missing_provenance_instead_of_synthesizing_paper() -> None:
    left = merge_claim_without_paper(artifact_id="ps:claim:nopaperleft0001")
    right = merge_claim_without_paper(artifact_id="ps:claim:nopaperright0001")

    with pytest.raises(MergeComparisonProvenanceError) as excinfo:
        _classify_pair(left, right)

    assert "merge_comparison" not in str(excinfo.value)
