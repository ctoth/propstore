from __future__ import annotations

from click.testing import CliRunner

from propstore.cli import cli
from propstore.repository import Repository
from propstore.support_revision.workflows import (
    RevisionWorldRequest,
    contract_revision,
    epistemic_state,
    expand_revision,
    explain_revision_operation,
    iterated_revise_world,
    revise_world,
    revision_base,
    revision_entrenchment,
)
from propstore.world import WorldModel
from tests.test_revision_phase1_cli import revision_cli_workspace


def _revision_request() -> RevisionWorldRequest:
    return RevisionWorldRequest(
        bindings={"speaker_sex": "male"},
        context_id="ctx_test",
    )


def test_revision_workflow_reports_base_and_entrenchment(revision_cli_workspace) -> None:
    repo = Repository.find(revision_cli_workspace)
    with WorldModel(repo) as wm:
        base = revision_base(wm, _revision_request())
        entrenchment = revision_entrenchment(wm, _revision_request())

    assert "claim:freq_claim1" in {atom.atom_id for atom in base.atoms}
    assert "claim:freq_claim1" in entrenchment.ranked_atom_ids


def test_revision_workflow_runs_expand_contract_and_revise(revision_cli_workspace) -> None:
    repo = Repository.find(revision_cli_workspace)
    atom = {"kind": "claim", "id": "synthetic_freq", "value": 123.0}
    with WorldModel(repo) as wm:
        expanded = expand_revision(wm, _revision_request(), atom)
        contracted = contract_revision(wm, _revision_request(), ("freq_claim1",))
        revised = revise_world(wm, _revision_request(), atom, ("freq_claim1",))

    assert "claim:synthetic_freq" in expanded.accepted_atom_ids
    assert "claim:freq_claim1" in contracted.rejected_atom_ids
    assert "claim:synthetic_freq" in revised.accepted_atom_ids
    assert "claim:freq_claim1" in revised.rejected_atom_ids


def test_revision_workflow_explains_and_iterates(revision_cli_workspace) -> None:
    repo = Repository.find(revision_cli_workspace)
    atom = {"kind": "claim", "id": "synthetic_freq", "value": 123.0}
    with WorldModel(repo) as wm:
        explanation = explain_revision_operation(
            wm,
            _revision_request(),
            operation="contract",
            targets=("freq_claim1",),
        )
        state = epistemic_state(wm, _revision_request())
        iterated = iterated_revise_world(
            wm,
            _revision_request(),
            atom=atom,
            conflicts=("freq_claim1",),
            operator="lexicographic",
        )

    assert explanation.atoms["claim:freq_claim1"].status == "rejected"
    assert state.history == ()
    assert iterated.operator == "lexicographic"
    assert "claim:synthetic_freq" in iterated.next_state.accepted_atom_ids


def test_world_expand_shows_added_revision_atom(revision_cli_workspace) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "world",
            "expand",
            "--context",
            "ctx_test",
            "speaker_sex=male",
            "--atom",
            '{"kind":"claim","id":"synthetic_freq","value":123.0}',
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Accepted" in result.output
    assert "claim:synthetic_freq" in result.output


def test_world_contract_shows_rejected_atoms_and_incision_set(revision_cli_workspace) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "world",
            "contract",
            "--context",
            "ctx_test",
            "speaker_sex=male",
            "--target",
            "freq_claim1",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Rejected" in result.output
    assert "claim:freq_claim1" in result.output
    assert "Incision set" in result.output


def test_world_revise_shows_new_atom_and_rejected_conflict(revision_cli_workspace) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "world",
            "revise",
            "--context",
            "ctx_test",
            "speaker_sex=male",
            "--atom",
            '{"kind":"claim","id":"synthetic_freq","value":123.0}',
            "--conflict",
            "freq_claim1",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "claim:synthetic_freq" in result.output
    assert "claim:freq_claim1" in result.output


def test_world_revision_explain_shows_atom_status_and_reason(revision_cli_workspace) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "world",
            "revision-explain",
            "--context",
            "ctx_test",
            "speaker_sex=male",
            "--operation",
            "contract",
            "--target",
            "freq_claim1",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "claim:freq_claim1" in result.output
    assert "status=rejected" in result.output
    assert "reason=support_lost" in result.output


def test_world_iterated_state_shows_ranked_atoms_and_empty_history(revision_cli_workspace) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "world",
            "iterated-state",
            "--context",
            "ctx_test",
            "speaker_sex=male",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Iterated state" in result.output
    assert "History length: 0" in result.output
    assert "claim:freq_claim1" in result.output


def test_world_iterated_revise_shows_operator_and_next_state_summary(revision_cli_workspace) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "world",
            "iterated-revise",
            "--context",
            "ctx_test",
            "speaker_sex=male",
            "--atom",
            '{"kind":"claim","id":"synthetic_freq","value":123.0}',
            "--conflict",
            "freq_claim1",
            "--operator",
            "lexicographic",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Operator: lexicographic" in result.output
    assert "Next state" in result.output
    assert "claim:synthetic_freq" in result.output
    assert "Ranking delta:" in result.output
    assert "History:" in result.output
