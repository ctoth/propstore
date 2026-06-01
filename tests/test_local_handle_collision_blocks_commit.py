from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from propstore.repository import Repository
from propstore.importing.repository_import import (
    commit_repository_import,
    plan_repository_import,
)
from tests.conftest import TEST_CONTEXT_ID


def test_local_handle_collision_blocks_repository_import_commit(tmp_path: Path) -> None:
    destination = Repository.init(tmp_path / "destination" / "knowledge")
    source = Repository.init(tmp_path / "source" / "knowledge")
    source.git.commit_files(
        {
            "claims/first.yaml": _claim_file(
                "shared_local",
                "ps:claim:first",
                "First claim.",
            ),
            "claims/second.yaml": _claim_file(
                "shared_local",
                "ps:claim:second",
                "Second claim.",
            ),
        },
        "Seed ambiguous local handles",
    )
    plan = plan_repository_import(destination, source.root.parent)
    assert plan.warnings

    with pytest.raises(ValueError, match="ambiguous imported claim handle"):
        commit_repository_import(destination, plan)
