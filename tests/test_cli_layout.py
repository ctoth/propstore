from __future__ import annotations

from pathlib import Path


def test_world_commands_live_outside_compiler_cmds() -> None:
    compiler_cmds = Path("propstore/cli/compiler_cmds.py").read_text(encoding="utf-8")
    world_cmds = Path("propstore/cli/world_cmds.py").read_text(encoding="utf-8")

    assert "@world.command" not in compiler_cmds
    assert "def world(" not in compiler_cmds
    assert "@world.command" in world_cmds
    assert "def world(" in world_cmds


def test_root_cli_only_registers_top_level_commands() -> None:
    root_cli = Path("propstore/cli/__init__.py").read_text(encoding="utf-8")

    assert '@cli.command("log")' not in root_cli
    assert '@cli.command("diff")' not in root_cli
    assert '@cli.command("show")' not in root_cli
    assert '@cli.command("checkout")' not in root_cli
    assert "@cli.command()" not in root_cli
    assert "from propstore.cli.history_cmds import" in root_cli
    assert "from propstore.cli.proposal_cmds import" in root_cli


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
