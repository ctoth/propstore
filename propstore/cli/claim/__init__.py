"""``pks claim`` — presentation adapters over the claim render-view tier.

Thin Click adapters (CLAUDE.md "CLI adapter discipline"): each command parses
its flags into a typed request / render policy, opens a
:class:`~propstore.world.WorldQuery` via
:func:`~propstore.app.world.open_app_world_model`, calls the owner-layer view
builder, and renders the typed report. No claim view / world query semantics live
here; the owner modules in :mod:`propstore.app` own them.

This package ``__init__`` owns the ``claim`` Click group and the shared CLI-only
helpers (the lifecycle-visibility render-policy flags, the single
flag-to-:class:`RenderPolicy` path, world opening, JSON emission). The sibling
command module is imported at the bottom, after the group and helpers exist, so it
can attach its commands via ``@claim.command``.
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
def claim() -> None:
    """Read views over claims."""


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


# Import the command module last so it can attach its commands to the ``claim``
# group; re-exported via ``__all__`` so the side-effect import reads as the
# package's public command surface rather than an unused import.
from propstore.cli.claim import display  # noqa: E402

__all__ = [
    "claim",
    "display",
    "emit_report_json",
    "format_option",
    "lifecycle_options",
    "lifecycle_policy",
    "open_world",
]
