"""``pks concept`` — presentation adapters over the concept render-view tier
and the concept-alignment lifecycle.

Thin Click adapters (CLAUDE.md "CLI adapter discipline"). The read views open a
:class:`~propstore.world.WorldQuery` and call the owner builders in
:mod:`propstore.app.concepts` / :mod:`propstore.app.concept_views`; the alignment
commands call the propose/decide/promote owner functions in
:mod:`propstore.source.alignment`. No concept view, world query, or alignment math
lives here.

This package ``__init__`` owns the ``concept`` Click group and the shared CLI-only
helpers (lifecycle-visibility render-policy flags, the single
flag-to-:class:`RenderPolicy` path, world opening, JSON emission). The sibling
command modules are imported at the bottom so they can attach commands via
``@concept.command``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager

import click
from click.decorators import FC

from propstore.app.rendering import (
    AppRenderPolicyRequest,
    RenderPolicyValidationError,
    build_render_policy,
)
from propstore.app.world import WorldSidecarMissingError, open_app_world_model
from propstore.cli.helpers import EXIT_VALIDATION, fail
from propstore.cli.output import emit
from propstore.reporting import JsonReportMixin
from propstore.repository import Repository
from propstore.world import RenderPolicy, WorldQuery


@click.group()
def concept() -> None:
    """Read views over concepts and the concept-alignment lifecycle."""


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
        help="Surface build/promotion-blocked concepts.",
    )(func)
    func = click.option(
        "--include-drafts",
        is_flag=True,
        default=False,
        help="Surface draft-stage concepts.",
    )(func)
    return func


def lifecycle_policy(
    *,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> RenderPolicy:
    """Build a :class:`RenderPolicy` carrying the lifecycle-visibility opt-ins."""

    try:
        return build_render_policy(
            AppRenderPolicyRequest(
                include_drafts=include_drafts,
                include_blocked=include_blocked,
                show_quarantined=show_quarantined,
            )
        )
    except RenderPolicyValidationError as exc:
        fail(str(exc), exit_code=EXIT_VALIDATION)


# ── world opening + JSON rendering ────────────────────────────────────────────


@contextmanager
def open_world(repo: Repository) -> Iterator[WorldQuery]:
    """Open a world reader, mapping a missing sidecar to a clean CLI failure."""

    try:
        with open_app_world_model(repo) as world_query:
            yield world_query
    except WorldSidecarMissingError as exc:
        fail(str(exc))


def emit_report_json(report: JsonReportMixin) -> None:
    emit(json.dumps(report.to_json(), indent=2))


# Import the command modules last so they can attach their commands to the
# ``concept`` group; re-exported via ``__all__``.
from propstore.cli.concept import alignment, display, embedding  # noqa: E402

__all__ = [
    "alignment",
    "concept",
    "display",
    "embedding",
    "emit_report_json",
    "format_option",
    "lifecycle_options",
    "lifecycle_policy",
    "open_world",
]
