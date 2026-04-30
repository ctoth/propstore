from __future__ import annotations

from click.testing import CliRunner

from propstore.cli import cli


def test_proposal_rules_and_predicates_help_loads() -> None:
    runner = CliRunner()

    rules = runner.invoke(cli, ["proposal", "propose-rules", "--help"])
    assert rules.exit_code == 0, rules.output
    assert "--paper" in rules.output
    assert "--model" in rules.output
    assert "--prompt-version" in rules.output
    assert "--dry-run" in rules.output
    assert "--mock-llm-fixture" in rules.output

    predicates = runner.invoke(cli, ["proposal", "predicates", "declare", "--help"])
    assert predicates.exit_code == 0, predicates.output
    assert "--paper" in predicates.output
    assert "--model" in predicates.output
    assert "--dry-run" in predicates.output

    promote = runner.invoke(cli, ["proposal", "predicates", "promote", "--help"])
    assert promote.exit_code == 0, promote.output
    assert "--paper" in promote.output
