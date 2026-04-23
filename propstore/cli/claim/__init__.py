"""pks claim - claim inspection and workflow commands."""

from __future__ import annotations

from collections.abc import Callable

import click

from propstore.app.rendering import AppRenderPolicyRequest


@click.group()
def claim() -> None:
    """Manage and validate claims."""


def claim_render_policy_options(
    command: Callable[..., object],
) -> Callable[..., object]:
    command = click.option(
        "--show-quarantined",
        is_flag=True,
        default=False,
        help="Surface quarantined diagnostics under the current render policy.",
    )(command)
    command = click.option(
        "--include-blocked",
        is_flag=True,
        default=False,
        help=(
            "Surface build-blocked and promotion-blocked claims as visible "
            "under the current render policy."
        ),
    )(command)
    command = click.option(
        "--include-drafts",
        is_flag=True,
        default=False,
        help="Surface draft claims as visible under the current render policy.",
    )(command)
    return command


def claim_render_policy_request(
    *,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> AppRenderPolicyRequest:
    return AppRenderPolicyRequest(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )


# Import split command modules after the group and shared helpers are defined.
from propstore.cli.claim import analysis as _analysis
from propstore.cli.claim import display as _display
from propstore.cli.claim import embedding as _embedding
from propstore.cli.claim import relation as _relation
from propstore.cli.claim import validation as _validation
