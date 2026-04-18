from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from propstore.cli import cli


def test_world_commands_live_outside_compiler_cmds() -> None:
    compiler_cmds = Path("propstore/cli/compiler_cmds.py").read_text(encoding="utf-8")
    world_cmds = Path("propstore/cli/world_cmds.py").read_text(encoding="utf-8")

    assert "@world.command" not in compiler_cmds
    assert "def world(" not in compiler_cmds
    assert "@world.command" not in world_cmds
    assert "def world(" in world_cmds
    assert "from propstore.cli import world_query_cmds" in world_cmds


def test_world_command_families_live_outside_group_module() -> None:
    query_cmds = Path("propstore/cli/world_query_cmds.py").read_text(
        encoding="utf-8"
    )
    reasoning_cmds = Path("propstore/cli/world_reasoning_cmds.py").read_text(
        encoding="utf-8"
    )
    analysis_cmds = Path("propstore/cli/world_analysis_cmds.py").read_text(
        encoding="utf-8"
    )

    assert '@world.command("status")' in query_cmds
    assert '@world.command("resolve")' in reasoning_cmds
    assert '@world.command("fragility")' in analysis_cmds


def test_world_atms_commands_live_outside_world_group_module() -> None:
    world_cmds = Path("propstore/cli/world_cmds.py").read_text(encoding="utf-8")
    atms_cmds = Path("propstore/cli/world_atms_cmds.py").read_text(encoding="utf-8")

    assert '@world.command("atms-' not in world_cmds
    assert '@world.group("atms"' in atms_cmds
    assert '@atms.command("status")' in atms_cmds
    assert '@atms.command("next-query")' in atms_cmds
    assert "from propstore.cli import world_atms_cmds" in world_cmds


def test_world_revision_commands_live_outside_world_group_module() -> None:
    world_cmds = Path("propstore/cli/world_cmds.py").read_text(encoding="utf-8")
    revision_cmds = Path("propstore/cli/world_revision_cmds.py").read_text(
        encoding="utf-8"
    )

    assert '@world.command("revision-' not in world_cmds
    assert '@world.command("expand")' not in world_cmds
    assert '@world.group("revision"' in revision_cmds
    assert '@revision.command("base")' in revision_cmds
    assert '@revision.command("revise")' in revision_cmds
    assert "from propstore.cli import world_revision_cmds" in world_cmds


def test_root_cli_only_registers_top_level_commands() -> None:
    root_cli = Path("propstore/cli/__init__.py").read_text(encoding="utf-8")

    assert "class _LazyCLIGroup" in root_cli
    assert "import_module(module_name)" in root_cli
    assert "cli.add_command" not in root_cli
    assert "from propstore.cli.concept import" not in root_cli
    assert "from propstore.cli.form import" not in root_cli
    assert '@cli.command("log")' not in root_cli
    assert '@cli.command("diff")' not in root_cli
    assert '@cli.command("show")' not in root_cli
    assert '@cli.command("checkout")' not in root_cli
    assert "@cli.command()" not in root_cli


def test_forms_alias_does_not_trigger_startup_traceback() -> None:
    result = CliRunner().invoke(cli, ["forms"])

    assert result.exit_code == 2
    assert "Manage form definitions." in result.output
    assert "Commands:" in result.output
    assert "Traceback" not in result.output


def test_worldline_commands_live_outside_group_module() -> None:
    group_module = Path("propstore/cli/worldline_cmds.py").read_text(encoding="utf-8")
    materialize = Path("propstore/cli/worldline_materialize_cmds.py").read_text(
        encoding="utf-8"
    )
    display = Path("propstore/cli/worldline_display_cmds.py").read_text(
        encoding="utf-8"
    )
    mutation = Path("propstore/cli/worldline_mutation_cmds.py").read_text(
        encoding="utf-8"
    )

    assert "@worldline.command" not in group_module
    assert "def worldline_create(" in materialize
    assert "def worldline_run(" in materialize
    assert "def worldline_refresh(" in materialize
    assert "def worldline_show(" in display
    assert "def worldline_list(" in display
    assert "def worldline_diff(" in display
    assert "def worldline_delete(" in mutation
