from __future__ import annotations

from propstore.app.world_revision import (
    AppRevisionContractRequest,
    AppRevisionWorldRequest,
    world_revision_contract,
)
from propstore.repository import Repository
from tests.test_revision_cli import _projected_assertion_id
from tests.test_revision_phase1_cli import revision_cli_workspace


def test_world_revision_app_returns_typed_split_report(revision_cli_workspace) -> None:
    repo = Repository.find(revision_cli_workspace)
    assertion_id = _projected_assertion_id(repo)

    result = world_revision_contract(
        repo,
        AppRevisionContractRequest(
            world=AppRevisionWorldRequest(
                bindings={"speaker_sex": "male"},
                context="ctx_test",
            ),
            targets=(assertion_id,),
        ),
    )

    assert result.decision is not None
    assert result.realization is not None
    assert result.decision.operation == "contract"
    assert result.realization.rejected_atom_ids == result.rejected_atom_ids
