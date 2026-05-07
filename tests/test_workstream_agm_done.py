from __future__ import annotations

from pathlib import Path


def test_agm_workstream_is_closed_with_required_sentinels() -> None:
    workstream = Path("reviews/2026-05-05-agm-proposal/workstreams/WS-AGM-propstore-belief-set-cutover.md")
    text = workstream.read_text(encoding="utf-8")

    assert "**Status**: CLOSED " in text
    assert Path("tests/architecture/test_no_local_agm_logic.py").exists()
    assert Path("tests/architecture/test_belief_set_boundary_contract.py").exists()
    assert Path("tests/architecture/test_argumentation_boundary_contract.py").exists()
    assert Path("tests/test_revision_adapter_projection.py").exists()
    assert Path("tests/test_revision_app_contract.py").exists()
    assert Path("tests/test_web_revision_readonly.py").exists()


def test_agm_proposal_records_implemented_cutover() -> None:
    proposal = Path("proposals/true-agm-revision-proposal.md").read_text(encoding="utf-8")

    assert "**Status:** Implemented for the Propstore cutover." in proposal
    assert "propstore.support_revision.belief_set_adapter" in proposal
