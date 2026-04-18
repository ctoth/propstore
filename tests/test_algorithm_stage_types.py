from __future__ import annotations

from typing import get_type_hints

import yaml

from propstore.families.documents.claims import ClaimDocument, ClaimsFileDocument
from tests.family_helpers import load_claim_files
from propstore.core.algorithm_stage import AlgorithmStage, to_algorithm_stage
from propstore.core.row_types import ClaimRow
from propstore.families.documents.sources import SourceClaimDocument


def test_algorithm_stage_annotations_cover_runtime_path() -> None:
    assert get_type_hints(ClaimDocument)["stage"] == AlgorithmStage | None
    assert get_type_hints(SourceClaimDocument)["stage"] == AlgorithmStage | None
    assert get_type_hints(ClaimRow)["algorithm_stage"] == AlgorithmStage | None
    assert get_type_hints(ClaimsFileDocument)["stage"] == str | None


def test_claim_row_coerces_algorithm_stage() -> None:
    row = ClaimRow.from_mapping(
        {
            "id": "ps:claim:test",
            "artifact_id": "ps:claim:test",
            "algorithm_stage": "excitation",
        }
    )

    assert row.algorithm_stage == to_algorithm_stage("excitation")


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

    assert claim_file.document.stage == "draft"
    assert claim_file.document.claims[0].stage == to_algorithm_stage("inference")
