"""pks — the propstore CLI."""
from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys
from typing import Any

import click

_COMMANDS: dict[str, tuple[str, str, str]] = {
    "build": ("propstore.cli.compiler_cmds", "build", "Validate, build sidecar, and run conflict detection."),
    "checkout": ("propstore.cli.history_cmds", "checkout_cmd", "Checkout a repository commit."),
    "claim": ("propstore.cli.claim", "claim", "Manage claims."),
    "concept": ("propstore.cli.concept", "concept", "Manage concepts in the registry."),
    "context": ("propstore.cli.context", "context", "Manage contexts."),
    "diff": ("propstore.cli.history_cmds", "diff_cmd", "Show repository changes."),
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
    "merge": ("propstore.cli.merge_cmds", "merge", "Merge repository branches."),
    "micropub": ("propstore.cli.micropub", "micropub", "Manage micropublications."),
    "promote": ("propstore.cli.proposal_cmds", "promote_cmd", "Promote proposed artifacts."),
    "query": ("propstore.cli.compiler_cmds", "query", "Run SQL against the sidecar."),
    "show": ("propstore.cli.history_cmds", "show_cmd", "Show a repository commit."),
    "source": ("propstore.cli.source", "source", "Manage source-local authoring state."),
    "validate": ("propstore.cli.compiler_cmds", "validate", "Validate concepts and claims."),
    "verify": ("propstore.cli.verify", "verify", "Verify repository evidence."),
    "world": ("propstore.cli.world_cmds", "world", "Query the world model."),
    "worldline": ("propstore.cli.worldline_cmds", "worldline", "Manage materialized query artifacts."),
}

_COMMAND_ALIASES = {
    "forms": "form",
}


class _LazyRepository:
    def __init__(self, start: Path | None) -> None:
        self._start = start
        self._repo: Any | None = None

    def _resolve(self) -> Any:
        if self._repo is None:
            from propstore.repository import Repository

            self._repo = Repository.find(self._start)
        return self._repo

    def __getattr__(self, name: str):
        return getattr(self._resolve(), name)


class _LazyCLIGroup(click.Group):
    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(_COMMANDS)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        command_name = _COMMAND_ALIASES.get(cmd_name, cmd_name)
        spec = _COMMANDS.get(command_name)
        if spec is None:
            return None
        module_name, attribute_name, _help = spec
        module = import_module(module_name)
        command = getattr(module, attribute_name)
        if not isinstance(command, click.Command):
            raise TypeError(f"{module_name}.{attribute_name} is not a click command")
        return command

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        rows = [(name, spec[2]) for name, spec in sorted(_COMMANDS.items())]
        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


@click.group(cls=_LazyCLIGroup)
@click.option("-C", "--directory", default=None, type=click.Path(exists=True),
              help="Run as if pks was started in this directory.")
@click.pass_context
def cli(ctx: click.Context, directory: str | None) -> None:
    """Propositional Knowledge Store CLI."""
    ctx.ensure_object(dict)
    start = Path(directory) if directory else None
    if ctx.resilient_parsing or any(arg in {"--help", "-h"} for arg in sys.argv[1:]):
        return
    if ctx.invoked_subcommand == "init":
        # init bypasses Repository lookup — store the start dir for init to use
        ctx.obj["start"] = start
        return
    ctx.obj["repo"] = _LazyRepository(start)
