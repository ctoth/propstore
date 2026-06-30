from __future__ import annotations

from click.testing import CliRunner

from propstore.cli import cli


def test_cli_propose_rules_help_lists_options() -> None:
    result = CliRunner().invoke(cli, ["proposal", "propose-rules", "--help"])
    assert result.exit_code == 0, result.output
    assert "--paper" in result.output
    assert "--dry-run" in result.output
    assert "--mock-llm-fixture" in result.output
