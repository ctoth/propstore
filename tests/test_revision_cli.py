from __future__ import annotations

from click.testing import CliRunner

from propstore.cli import cli
from tests.test_revision_phase1_cli import revision_cli_workspace


def test_world_expand_shows_added_revision_atom(revision_cli_workspace) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "world",
            "expand",
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
