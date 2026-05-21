from __future__ import annotations

from typing import get_type_hints

import yaml

from propstore.families.claims.documents import ClaimDocument
from tests.family_helpers import load_claim_files
from propstore.core.algorithm_stage import AlgorithmStage, to_algorithm_stage
from propstore.families.claims.declaration import ClaimAlgorithmPayload
from propstore.families.documents.sources import SourceClaimDocument
from tests.claim_model_helpers import claim_model


def test_algorithm_stage_annotations_cover_runtime_path() -> None:
    assert get_type_hints(ClaimDocument)["stage"] == AlgorithmStage | None
    assert get_type_hints(SourceClaimDocument)["stage"] == AlgorithmStage | None
    assert get_type_hints(ClaimAlgorithmPayload)["algorithm_stage"] == AlgorithmStage | None


def test_typed_claim_carries_algorithm_stage() -> None:
    stage = to_algorithm_stage("excitation")
    claim = claim_model(
        claim_id="ps:claim:test",
        algorithm_stage=stage,
    )

    assert claim.algorithm_payload is not None
    assert claim.algorithm_payload.algorithm_stage == stage


def test_claim_file_stage_split_is_preserved(tmp_path) -> None:
    (tmp_path / "claims.yaml").write_text(
        yaml.dump(
            {
                "source": {"paper": "test_paper"},
                "stage": "draft",
                "claims": [
                    {
                        "id": "claim1",
                        "artifact_id": "ps:claim:test_paper:claim1",
                        "version_id": "v1",
                        "type": "algorithm",
                        "body": "def compute(x):\n    return x\n",
                        "stage": "inference",
                        "variables": [{"name": "x", "concept": "concept1"}],
                        "context": {"id": "ctx_test"},
                        "provenance": {"paper": "test_paper", "page": 1},
                    }
                ],
            },
            default_flow_style=False,
        )
    )

    claim_file = load_claim_files(tmp_path)[0]

    assert getattr(claim_file, "stage") == "draft"
    assert claim_file.document.stage == to_algorithm_stage("inference")
