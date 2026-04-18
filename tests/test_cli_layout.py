from __future__ import annotations

from pathlib import Path


def test_world_commands_live_outside_compiler_cmds() -> None:
    compiler_cmds = Path("propstore/cli/compiler_cmds.py").read_text(encoding="utf-8")
    world_cmds = Path("propstore/cli/world_cmds.py").read_text(encoding="utf-8")

    assert "@world.command" not in compiler_cmds
    assert "def world(" not in compiler_cmds
    assert "@world.command" in world_cmds
    assert "def world(" in world_cmds
