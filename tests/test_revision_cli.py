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
from propstore.world import WorldQuery
from tests.test_revision_phase1_cli import revision_cli_workspace


def _revision_request() -> RevisionWorldRequest:
    return RevisionWorldRequest(
        bindings={"speaker_sex": "male"},
        context_id="ctx_test",
    )


def _projected_assertion_id(repo: Repository) -> str:
    with WorldQuery(repo) as wm:
        base = revision_base(wm, _revision_request())
    assertion_ids = [
        atom.atom_id
        for atom in base.atoms
        if getattr(atom, "source_claims", ())
    ]
    assert len(assertion_ids) == 1
    return assertion_ids[0]


def test_revision_workflow_reports_base_and_entrenchment(revision_cli_workspace) -> None:
    repo = Repository.find(revision_cli_workspace)
    with WorldQuery(repo) as wm:
        base = revision_base(wm, _revision_request())
        entrenchment = revision_entrenchment(wm, _revision_request())
    assertion_id = _projected_assertion_id(repo)

    assert assertion_id in {atom.atom_id for atom in base.atoms}
    assert assertion_id in entrenchment.ranked_atom_ids


def test_revision_workflow_runs_expand_contract_and_revise(revision_cli_workspace) -> None:
    repo = Repository.find(revision_cli_workspace)
    assertion_id = _projected_assertion_id(repo)
    atom = {"kind": "assertion", "id": assertion_id}
    with WorldQuery(repo) as wm:
        expanded = expand_revision(wm, _revision_request(), atom)
        contracted = contract_revision(wm, _revision_request(), (assertion_id,))
        revised = revise_world(wm, _revision_request(), atom, (assertion_id,))

    assert assertion_id in expanded.accepted_atom_ids
    assert assertion_id in contracted.rejected_atom_ids
    assert assertion_id in revised.accepted_atom_ids
    assert assertion_id in revised.rejected_atom_ids


def test_revision_workflow_explains_and_iterates(revision_cli_workspace) -> None:
    repo = Repository.find(revision_cli_workspace)
    assertion_id = _projected_assertion_id(repo)
    atom = {"kind": "assertion", "id": assertion_id}
    with WorldQuery(repo) as wm:
        explanation = explain_revision_operation(
            wm,
            _revision_request(),
            operation="contract",
            targets=(assertion_id,),
        )
        state = epistemic_state(wm, _revision_request())
        iterated = iterated_revise_world(
            wm,
            _revision_request(),
            atom=atom,
            conflicts=(assertion_id,),
            operator="lexicographic",
        )

    assert explanation.atoms[assertion_id].status == "rejected"
    assert state.history == ()
    assert iterated.operator == "lexicographic"
    assert assertion_id in iterated.next_state.accepted_atom_ids


def test_world_expand_shows_added_revision_atom(revision_cli_workspace) -> None:
    runner = CliRunner()
    assertion_id = _projected_assertion_id(Repository.find(revision_cli_workspace))

    result = runner.invoke(
        cli,
        [
            "world",
            "revision",
            "expand",
            "--context",
            "ctx_test",
            "speaker_sex=male",
            "--atom",
            f'{{"kind":"assertion","id":"{assertion_id}"}}',
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Accepted" in result.output
    assert assertion_id in result.output


def test_world_contract_shows_rejected_atoms_and_incision_set(revision_cli_workspace) -> None:
    runner = CliRunner()
    assertion_id = _projected_assertion_id(Repository.find(revision_cli_workspace))

    result = runner.invoke(
        cli,
        [
            "world",
            "revision",
            "contract",
            "--context",
            "ctx_test",
            "speaker_sex=male",
            "--target",
            assertion_id,
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Rejected" in result.output
    assert assertion_id in result.output
    assert "Incision set" in result.output


def test_world_revise_shows_new_atom_and_rejected_conflict(revision_cli_workspace) -> None:
    runner = CliRunner()
    assertion_id = _projected_assertion_id(Repository.find(revision_cli_workspace))

    result = runner.invoke(
        cli,
        [
            "world",
            "revision",
            "revise",
            "--context",
            "ctx_test",
            "speaker_sex=male",
            "--atom",
            f'{{"kind":"assertion","id":"{assertion_id}"}}',
            "--conflict",
            assertion_id,
        ],
    )

    assert result.exit_code == 0, result.output
    assert assertion_id in result.output


def test_world_revision_explain_shows_atom_status_and_reason(revision_cli_workspace) -> None:
    runner = CliRunner()
    assertion_id = _projected_assertion_id(Repository.find(revision_cli_workspace))

    result = runner.invoke(
        cli,
        [
            "world",
            "revision",
            "explain",
            "--context",
            "ctx_test",
            "speaker_sex=male",
            "--operation",
            "contract",
            "--target",
            assertion_id,
        ],
    )

    assert result.exit_code == 0, result.output
    assert assertion_id in result.output
    assert "status=rejected" in result.output
    assert "reason=support_lost" in result.output


def test_world_iterated_state_shows_ranked_atoms_and_empty_history(revision_cli_workspace) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "world",
            "revision",
            "iterated-state",
            "--context",
            "ctx_test",
            "speaker_sex=male",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Iterated state" in result.output
    assert "History length: 0" in result.output
    assert "ps:assertion:" in result.output


def test_world_iterated_revise_shows_operator_and_next_state_summary(revision_cli_workspace) -> None:
    runner = CliRunner()
    assertion_id = _projected_assertion_id(Repository.find(revision_cli_workspace))

    result = runner.invoke(
        cli,
        [
            "world",
            "revision",
            "iterated-revise",
            "--context",
            "ctx_test",
            "speaker_sex=male",
            "--atom",
            f'{{"kind":"assertion","id":"{assertion_id}"}}',
            "--conflict",
            assertion_id,
            "--operator",
            "lexicographic",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Operator: lexicographic" in result.output
    assert "Next state" in result.output
    assert assertion_id in result.output
    assert "Ranking delta:" in result.output
    assert "History:" in result.output
