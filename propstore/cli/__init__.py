"""pks - the propstore CLI.

The root entry point stays lazy (CLAUDE.md "CLI adapter discipline"): the command
families are registered through the ``_COMMANDS`` table and imported only when the
command they name is actually invoked, so asking for one command never imports an
unrelated family. Command families with sibling modules are packages; this module
owns only the root group, the lazy registry, and the aliases.
"""
from __future__ import annotations

import os
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from propstore.repository import Repository

_COMMANDS: dict[str, tuple[str, str, str]] = {
    "build": ("propstore.cli.compiler_cmds", "build", "Validate, build sidecar, and run conflict detection."),
    "checkout": ("propstore.cli.history_cmds", "checkout_cmd", "Checkout a repository commit."),
    "claim": ("propstore.cli.claim", "claim", "Manage claims."),
    "concept": ("propstore.cli.concept", "concept", "Manage concepts in the registry."),
    "contract-manifest": ("propstore.cli.contracts", "contract_manifest", "Render or write contract manifest."),
    "context": ("propstore.cli.context", "context", "Manage contexts."),
    "diff": ("propstore.cli.history_cmds", "diff_cmd", "Show repository changes."),
    "event": ("propstore.cli.event", "event", "Query render-time description-claim coreference."),
    "export-aliases": ("propstore.cli.compiler_cmds", "export_aliases", "Export concept aliases."),
    "form": ("propstore.cli.form", "form", "Manage form definitions."),
    "grounding": ("propstore.cli.grounding_cmds", "grounding", "Inspect grounding artifacts."),
    "import-repository": (
        "propstore.cli.repository_import_cmd",
        "import_repository_cmd",
        "Import a repository snapshot.",
    ),
    "init": ("propstore.cli.init", "init", "Initialize a propstore knowledge repository."),
    "log": ("propstore.cli.history_cmds", "log_cmd", "Show knowledge repository history."),
    "materialize": ("propstore.cli.materialize", "materialize_cmd", "Project committed artifacts to loose files."),
    "merge": ("propstore.cli.merge_cmds", "merge", "Merge repository branches."),
    "micropub": ("propstore.cli.micropub", "micropub", "Manage micropublications."),
    "observatory": ("propstore.cli.observatory", "observatory", "Run epistemic observatory fixtures."),
    "predicate": ("propstore.cli.predicate", "predicate", "Declare DeLP/Datalog predicates."),
    "proposal": ("propstore.cli.proposal", "proposal", "Manage proposal artifacts."),
    "rule": ("propstore.cli.rule", "rule", "Author DeLP rules."),
    "show": ("propstore.cli.history_cmds", "show_cmd", "Show a repository commit."),
    "source": ("propstore.cli.source", "source", "Manage source-local authoring state."),
    "validate": ("propstore.cli.compiler_cmds", "validate", "Validate concepts and claims."),
    "verify": ("propstore.cli.verify", "verify", "Verify repository evidence."),
    "web": ("propstore.cli.web", "web", "Serve the propstore web UI."),
    "world": ("propstore.cli.world", "world", "Query the world model."),
    "worldline": ("propstore.cli.worldline", "worldline", "Manage materialized query artifacts."),
}

_QUICKSTART_COMMANDS = (
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
)

_ADVANCED_COMMANDS = (
    "event",
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
)

_COMMAND_ALIASES = {
    "forms": "form",
}


class _LazyRepository:
    """Defers ``Repository.find`` until an attribute is actually accessed.

    Keeping resolution lazy means ``pks <cmd> --help`` and commands that never
    touch the repository do not require an initialized repository to exist.
    """

    def __init__(self, start: Path | None) -> None:
        self._start = start
        self._repo: Repository | None = None

    def _resolve(self) -> Repository:
        if self._repo is None:
            from propstore.repository import Repository

            self._repo = Repository.find(self._start)
        return self._repo

    def __getattr__(self, name: str) -> object:
        return getattr(self._resolve(), name)


def _render_expected_cli_error(exc: BaseException) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    return (
        f"{message}\n"
        "Hint: rerun with --traceback or PKS_TRACEBACK=1 for a full traceback."
    )


def _load_command(module_name: str, attribute_name: str) -> click.Command:
    module = import_module(module_name)
    command: object = getattr(module, attribute_name)
    if not isinstance(command, click.Command):
        raise TypeError(f"{module_name}.{attribute_name} is not a click command")
    return command


class _LazyCLIGroup(click.Group):
    def _traceback_enabled(self, ctx: click.Context) -> bool:
        if os.environ.get("PKS_TRACEBACK") == "1":
            return True
        return bool(ctx.params.get("traceback_enabled"))

    def invoke(self, ctx: click.Context) -> object:
        # Map expected owner-layer failures to a one-line ClickException (exit 1)
        # unless the caller asked for a full traceback via --traceback / PKS_TRACEBACK.
        if self._traceback_enabled(ctx):
            return super().invoke(ctx)
        try:
            return super().invoke(ctx)
        except (click.exceptions.Exit, click.exceptions.Abort):
            # click control-flow exceptions (incl. --help) subclass RuntimeError;
            # let click handle them rather than rendering them as errors.
            raise
        except (ValueError, RuntimeError) as exc:
            raise click.ClickException(_render_expected_cli_error(exc)) from exc

    def list_commands(self, ctx: click.Context) -> list[str]:
        return list(_QUICKSTART_COMMANDS)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if cmd_name == "advanced":
            return _advanced
        command_name = _COMMAND_ALIASES.get(cmd_name, cmd_name)
        if command_name == "status":
            command_name = "world-status"
        if command_name == "world-status":
            return _load_command("propstore.cli.world.query", "world_status")
        spec = _COMMANDS.get(command_name)
        if spec is None:
            return None
        module_name, attribute_name, _help = spec
        return _load_command(module_name, attribute_name)

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        rows = [
            (
                name,
                "Show knowledge base stats and authored reasoning inventory."
                if name == "status"
                else _COMMANDS[name][2],
            )
            for name in _QUICKSTART_COMMANDS
        ]
        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)

    def format_epilog(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        formatter.write_paragraph()
        formatter.write_text(
            "Quickstart: pks init / pks build / pks world status / "
            "pks world query <concept>"
        )
        formatter.write_text("Advanced commands: pks advanced --help")


class _AdvancedCLIGroup(click.Group):
    def list_commands(self, ctx: click.Context) -> list[str]:
        return list(_ADVANCED_COMMANDS)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        command_name = _COMMAND_ALIASES.get(cmd_name, cmd_name)
        spec = _COMMANDS.get(command_name)
        if spec is None or command_name not in _ADVANCED_COMMANDS:
            return None
        module_name, attribute_name, _help = spec
        return _load_command(module_name, attribute_name)

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        rows = [(name, _COMMANDS[name][2]) for name in _ADVANCED_COMMANDS]
        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


_advanced = _AdvancedCLIGroup(
    "advanced",
    help="Show advanced and specialized command families.",
)


@click.group(cls=_LazyCLIGroup)
@click.version_option(package_name="propstore")
@click.option(
    "-C",
    "--directory",
    default=None,
    type=click.Path(file_okay=False),
    help="Run as if pks was started in this directory.",
)
@click.option(
    "--traceback",
    "traceback_enabled",
    is_flag=True,
    help="Show full Python tracebacks for unexpected command failures.",
)
@click.pass_context
def cli(ctx: click.Context, directory: str | None, traceback_enabled: bool) -> None:
    """Propositional Knowledge Store CLI."""
    ctx.ensure_object(dict)
    ctx.obj["traceback"] = traceback_enabled
    start = Path(directory) if directory else None
    if ctx.resilient_parsing:
        return
    if ctx.invoked_subcommand == "init":
        # init bypasses the repository lookup; store the start dir for it to use.
        ctx.obj["start"] = start
        return
    ctx.obj["repo"] = _LazyRepository(start)
