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
