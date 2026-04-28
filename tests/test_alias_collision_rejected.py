from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from propstore.repository import Repository
from propstore.source.registry import ConceptAliasCollisionError, load_primary_branch_concepts
from tests.conftest import normalize_concept_payloads


def test_primary_branch_alias_collision_is_rejected(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    first, second = normalize_concept_payloads(
        [
            {
                "id": "velocity",
                "canonical_name": "velocity",
                "status": "accepted",
                "definition": "Vector-valued displacement per unit time.",
                "domain": "source",
                "form": "structural",
                "aliases": [{"name": "rate"}],
            },
            {
                "id": "speed",
                "canonical_name": "speed",
                "status": "accepted",
                "definition": "Scalar magnitude of motion.",
                "domain": "source",
                "form": "structural",
                "aliases": [{"name": "rate"}],
            },
        ],
        default_domain="source",
    )
    repo.git.commit_batch(
        adds={
            "concepts/velocity.yaml": yaml.safe_dump(
                first,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8"),
            "concepts/speed.yaml": yaml.safe_dump(
                second,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8"),
        },
        deletes=[],
        message="Seed alias collision",
        branch="master",
    )

    with pytest.raises(ConceptAliasCollisionError) as exc_info:
        load_primary_branch_concepts(repo)

    message = str(exc_info.value)
    assert "rate" in message
    assert first["artifact_id"] in message
    assert second["artifact_id"] in message
