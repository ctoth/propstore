"""``pks world`` — presentation adapters over the world reasoning-report tier.

Thin Click adapters (CLAUDE.md "CLI adapter discipline"): each command parses
its flags into a typed request, opens a :class:`~propstore.world.WorldQuery` via
:func:`~propstore.app.world.open_app_world_model`, calls the owner-layer report
builder, and renders the typed report. No world / ATMS / revision / argumentation
query semantics live here; the owner modules own them.

This package ``__init__`` owns the ``world`` Click group and the shared CLI-only
helpers (binding parsing, the single flag-to-:class:`RenderPolicy` path, JSON
emission). The sibling command modules are imported at the bottom, after the
group and helpers exist, so each can attach its commands via ``@world.command``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, TypeGuard

import click
from click.decorators import FC

from propstore.app.rendering import (
    AppRenderPolicyRequest,
    RenderPolicyValidationError,
    build_render_policy,
)
from propstore.app.world import WorldSidecarMissingError, open_app_world_model
from propstore.cli.helpers import EXIT_VALIDATION, CliContext, fail, require_repo
from propstore.cli.output import emit
from propstore.reporting import JsonReportMixin
from propstore.repository import Repository
from propstore.world import RenderPolicy, WorldQuery


@click.group()
def world() -> None:
    """Query the compiled world model."""


# ── binding parsing ───────────────────────────────────────────────────────────


def parse_world_binding_args(
    args: Sequence[str],
) -> tuple[dict[str, str], str | None]:
    """Split ``key=value`` binding tokens from a trailing concept/context token.

    Returns ``(bindings, target)`` where *target* is the last argument without an
    ``=`` (a concept or context filter), or ``None`` when every token is a
    binding.
    """

    parsed: dict[str, str] = {}
    remaining: list[str] = []
    for arg in args:
        if "=" not in arg:
            remaining.append(arg)
            continue
        key, _, value = arg.partition("=")
        if not key:
            raise click.ClickException("world bindings require a non-empty key")
        parsed[key] = value
    return parsed, remaining[-1] if remaining else None


def format_assumption_ids(assumption_ids: Sequence[str]) -> str:
    if not assumption_ids:
        return "[]"
    return "[" + ", ".join(str(value) for value in assumption_ids) + "]"


def is_json_object(value: object) -> TypeGuard[Mapping[str, Any]]:
    """Narrow a decoded-JSON value to a string-keyed object at the CLI boundary.

    ``json.loads`` is an ``Any`` source; this is the project's standard JSON
    boundary guard (mirroring :func:`propstore.support_revision.state._is_mapping`)
    so the command adapters can validate ``--add`` / ``--atom`` payloads without
    leaking partially-unknown types into the typed owner requests.
    """

    return isinstance(value, dict)


def is_json_array(value: object) -> TypeGuard[list[Any]]:
    """Narrow a decoded-JSON value to a list at the CLI boundary (see above)."""

    return isinstance(value, list)


# ── world opening ─────────────────────────────────────────────────────────────


@contextmanager
def open_world(repo: Repository) -> Iterator[WorldQuery]:
    """Open a world reader, mapping a missing sidecar to a clean CLI failure."""

    try:
        with open_app_world_model(repo) as world_query:
            yield world_query
    except WorldSidecarMissingError as exc:
        fail(str(exc))


def world_repo(obj: CliContext) -> Repository:
    """The repository handle for a ``pks world`` invocation."""

    return require_repo(obj)


# ── JSON rendering ────────────────────────────────────────────────────────────


def emit_report_json(report: JsonReportMixin) -> None:
    emit(json.dumps(report.to_json(), indent=2))


# ── render-policy flags (the single flag→RenderPolicy path) ───────────────────


def format_option(func: FC) -> FC:
    """Attach the shared ``--format text|json`` option."""

    return click.option(
        "--format",
        "fmt",
        type=click.Choice(["text", "json"]),
        default="text",
        help="Output format.",
    )(func)


def lifecycle_options(func: FC) -> FC:
    """Attach the three lifecycle-visibility opt-in flags."""

    func = click.option(
        "--show-quarantined",
        is_flag=True,
        default=False,
        help="Surface build-diagnostic quarantine rows.",
    )(func)
    func = click.option(
        "--include-blocked",
        is_flag=True,
        default=False,
        help="Surface build/promotion-blocked claims.",
    )(func)
    func = click.option(
        "--include-drafts",
        is_flag=True,
        default=False,
        help="Surface draft-stage claims.",
    )(func)
    return func


def build_policy(request: AppRenderPolicyRequest) -> RenderPolicy:
    """Build a :class:`RenderPolicy`, mapping validation errors to exit code 2."""

    try:
        return build_render_policy(request)
    except RenderPolicyValidationError as exc:
        fail(str(exc), exit_code=EXIT_VALIDATION)


def lifecycle_policy(
    *,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> RenderPolicy:
    """A :class:`RenderPolicy` carrying only the lifecycle-visibility opt-ins."""

    return build_policy(
        AppRenderPolicyRequest(
            include_drafts=include_drafts,
            include_blocked=include_blocked,
            show_quarantined=show_quarantined,
        )
    )


# Import the command modules last so they can attach their commands to the
# ``world`` group; re-exported via ``__all__`` so the side-effect imports read as
# the package's public command surface rather than unused imports.
from propstore.cli.world import analysis, query, reasoning, revision  # noqa: E402

__all__ = [
    "analysis",
    "build_policy",
    "emit_report_json",
    "format_assumption_ids",
    "format_option",
    "is_json_array",
    "is_json_object",
    "lifecycle_options",
    "lifecycle_policy",
    "open_world",
    "parse_world_binding_args",
    "query",
    "reasoning",
    "revision",
    "world",
    "world_repo",
]
