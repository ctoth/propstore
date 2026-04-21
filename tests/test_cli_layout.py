from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from propstore.cli import cli


def test_world_commands_live_outside_compiler_cmds() -> None:
    compiler_cmds = Path("propstore/cli/compiler_cmds.py").read_text(encoding="utf-8")
    world_cmds = Path("propstore/cli/world/__init__.py").read_text(encoding="utf-8")

    assert "@world.command" not in compiler_cmds
    assert "def world(" not in compiler_cmds
    assert "@world.command" not in world_cmds
    assert "def world(" in world_cmds
    assert "from propstore.cli.world import query" in world_cmds


def test_world_command_families_live_outside_group_module() -> None:
    query_cmds = Path("propstore/cli/world/query.py").read_text(
        encoding="utf-8"
    )
    reasoning_cmds = Path("propstore/cli/world/reasoning.py").read_text(
        encoding="utf-8"
    )
    analysis_cmds = Path("propstore/cli/world/analysis.py").read_text(
        encoding="utf-8"
    )

    assert '@world.command("status")' in query_cmds
    assert '@world.command("resolve")' in reasoning_cmds
    assert '@world.command("fragility")' in analysis_cmds


def test_world_atms_commands_live_outside_world_group_module() -> None:
    world_cmds = Path("propstore/cli/world/__init__.py").read_text(encoding="utf-8")
    atms_cmds = Path("propstore/cli/world/atms.py").read_text(encoding="utf-8")

    assert '@world.command("atms-' not in world_cmds
    assert '@world.group("atms"' in atms_cmds
    assert '@atms.command("status")' in atms_cmds
    assert '@atms.command("next-query")' in atms_cmds
    assert "from propstore.cli.world import atms" in world_cmds


def test_world_revision_commands_live_outside_world_group_module() -> None:
    world_cmds = Path("propstore/cli/world/__init__.py").read_text(encoding="utf-8")
    revision_cmds = Path("propstore/cli/world/revision.py").read_text(
        encoding="utf-8"
    )

    assert '@world.command("revision-' not in world_cmds
    assert '@world.command("expand")' not in world_cmds
    assert '@world.group("revision"' in revision_cmds
    assert '@revision.command("base")' in revision_cmds
    assert '@revision.command("revise")' in revision_cmds
    assert "from propstore.cli.world import revision" in world_cmds


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


def test_forms_alias_does_not_trigger_startup_traceback() -> None:
    result = CliRunner().invoke(cli, ["forms"])

    assert result.exit_code == 2
    assert "Manage form definitions." in result.output
    assert "Commands:" in result.output
    assert "Traceback" not in result.output


def test_dead_prefixed_error_helper_is_removed() -> None:
    assert not Path("propstore/cli/output/errors.py").exists()


def test_cli_only_world_arg_parsers_live_in_cli_layer() -> None:
    app_world = Path("propstore/app/world.py").read_text(encoding="utf-8")
    app_world_atms = Path("propstore/app/world_atms.py").read_text(encoding="utf-8")
    app_worldlines = Path("propstore/app/worldlines.py").read_text(encoding="utf-8")
    cli_world = Path("propstore/cli/world/__init__.py").read_text(encoding="utf-8")
    cli_worldline = Path("propstore/cli/worldline/__init__.py").read_text(
        encoding="utf-8"
    )

    assert "def parse_world_binding_args(" not in app_world
    assert "WorldBindingParseError" not in app_world
    assert "parse_world_binding_args" not in app_world_atms
    assert "args: tuple[str, ...]" not in app_world_atms
    assert "def coerce_worldline_cli_value(" not in app_worldlines
    assert "def parse_world_binding_args(" in cli_world
    assert "def coerce_worldline_cli_value(" in cli_worldline


def test_worldline_commands_live_outside_group_module() -> None:
    group_module = Path("propstore/cli/worldline/__init__.py").read_text(encoding="utf-8")
    materialize = Path("propstore/cli/worldline/materialize.py").read_text(
        encoding="utf-8"
    )
    display = Path("propstore/cli/worldline/display.py").read_text(
        encoding="utf-8"
    )
    mutation = Path("propstore/cli/worldline/mutation.py").read_text(
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


def test_concept_commands_live_outside_group_module() -> None:
    group_module = Path("propstore/cli/concept/__init__.py").read_text(encoding="utf-8")
    mutation = Path("propstore/cli/concept/mutation.py").read_text(
        encoding="utf-8"
    )
    display = Path("propstore/cli/concept/display.py").read_text(
        encoding="utf-8"
    )
    alignment = Path("propstore/cli/concept/alignment.py").read_text(
        encoding="utf-8"
    )
    embedding = Path("propstore/cli/concept/embedding.py").read_text(
        encoding="utf-8"
    )

    assert "@concept.command" not in group_module
    assert "def concept(" in group_module
    assert "from propstore.cli.concept import mutation" in group_module
    assert '@concept.command("add-value")' in mutation
    assert '@concept.command("list")' in display
    assert '@concept.command("align")' in alignment
    assert "def similar(" in embedding


def test_concept_add_uses_owner_form_listing() -> None:
    mutation = Path("propstore/cli/concept/mutation.py").read_text(encoding="utf-8")

    assert "repo.families.forms" not in mutation
    assert "list_form_items" in mutation


def test_micropub_lift_uses_named_error_exit_code() -> None:
    micropub = Path("propstore/cli/micropub.py").read_text(encoding="utf-8")

    assert "exit_with_code(1)" not in micropub
    assert "EXIT_ERROR" in micropub


def test_world_atms_uses_named_validation_exit_code() -> None:
    atms = Path("propstore/cli/world/atms.py").read_text(encoding="utf-8")

    assert "exit_with_code(2)" not in atms
    assert "EXIT_VALIDATION" in atms


def test_source_commands_live_in_source_package() -> None:
    group_module = Path("propstore/cli/source/__init__.py").read_text(encoding="utf-8")
    authoring = Path("propstore/cli/source/authoring.py").read_text(encoding="utf-8")
    batch = Path("propstore/cli/source/batch.py").read_text(encoding="utf-8")
    lifecycle = Path("propstore/cli/source/lifecycle.py").read_text(encoding="utf-8")
    proposal = Path("propstore/cli/source/proposal.py").read_text(encoding="utf-8")

    assert "@source.command" not in group_module
    assert "def source(" in group_module
    assert "from propstore.cli.source import authoring" in group_module
    assert '@source.command("write-notes")' in authoring
    assert '@source.command("write-metadata")' in authoring
    assert '@source.command("add-concepts")' in batch
    assert '@source.command("init")' in lifecycle
    assert '@source.command("finalize")' in lifecycle
    assert '@source.command("propose-concept")' in proposal
