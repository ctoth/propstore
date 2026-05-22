from __future__ import annotations

from typing import get_type_hints

import yaml

from propstore.families.claims.documents import ClaimDocument
from tests.family_helpers import load_claim_files
from propstore.core.algorithm_stage import AlgorithmStage
from propstore.families.documents.sources import SourceClaimDocument
from propstore.families.world_charters import world_charter_catalog
from tests.claim_model_helpers import claim_model


def _schema_object(name: str):
    for schema_object in world_charter_catalog().objects:
        if schema_object.name == name:
            return schema_object
    raise AssertionError(f"missing schema object {name}")


def test_algorithm_stage_annotations_cover_runtime_path() -> None:
    assert get_type_hints(ClaimDocument)["stage"] == AlgorithmStage | None
    assert get_type_hints(SourceClaimDocument)["stage"] == AlgorithmStage | None
    field = _schema_object("claim_algorithm_payload").field("algorithm_stage")
    assert field.python_type == "builtins.str"
    assert field.metadata["semantic_type"] == "propstore.core.algorithm_stage.AlgorithmStage"


def test_typed_claim_carries_algorithm_stage() -> None:
    stage = AlgorithmStage("excitation")
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

    assert claim_file.stage == "draft"
    assert claim_file.document.stage == AlgorithmStage("inference")
