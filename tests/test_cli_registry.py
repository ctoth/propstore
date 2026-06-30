"""Keystone tests for the lazy ``pks`` command registry.

These exercise only the root group, the lazy registry, and the help surface;
they do not import any command-family module, proving registration of one
command does not pull in unrelated families (CLAUDE.md "CLI adapter discipline").
The full per-family layout assertions live in ``test_cli_layout`` once the
families land.
"""
from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from propstore.cli import cli


def test_root_help_shows_quickstart_commands_not_advanced_surface() -> None:
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0, result.output
    for command in (
        "init",
        "build",
        "status",
        "claim",
        "concept",
        "world",
        "log",
        "show",
        "diff",
        "validate",
        "verify",
        "merge",
        "web",
    ):
        assert command in result.output
    for command in (
        "grounding",
        "micropub",
        "proposal",
        "source",
        "import-repository",
        "materialize",
        "worldline",
        "observatory",
        "predicate",
        "rule",
        "form",
        "context",
        "contract-manifest",
        "export-aliases",
        "checkout",
        "sidecar",
    ):
        assert f"  {command} " not in result.output
    assert "Quickstart: pks init / pks build / pks world status" in result.output
    assert "pks advanced --help" in result.output


def test_advanced_help_shows_advanced_commands() -> None:
    result = CliRunner().invoke(cli, ["advanced", "--help"])

    assert result.exit_code == 0, result.output
    for command in (
        "grounding",
        "micropub",
        "proposal",
        "source",
        "import-repository",
        "materialize",
        "worldline",
        "observatory",
        "predicate",
        "rule",
        "form",
        "context",
        "contract-manifest",
        "export-aliases",
        "checkout",
    ):
        assert command in result.output


def test_root_cli_only_registers_top_level_commands() -> None:
    root_cli = Path("propstore/cli/__init__.py").read_text(encoding="utf-8")

    assert "class _LazyCLIGroup" in root_cli
    assert "import_module(module_name)" in root_cli
    assert "cli.add_command" not in root_cli
    assert "cli.commands.update" not in root_cli
    assert "from propstore.cli.concept import" not in root_cli
    assert "from propstore.cli.form import" not in root_cli
    assert '@cli.command("log")' not in root_cli
    assert '@cli.command("diff")' not in root_cli
    assert '@cli.command("show")' not in root_cli
    assert '@cli.command("checkout")' not in root_cli
    assert "@cli.command()" not in root_cli


def test_dead_prefixed_error_helper_is_removed() -> None:
    assert not Path("propstore/cli/output/errors.py").exists()
