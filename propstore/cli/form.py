"""``pks form`` — presentation adapter over the form read-view tier.

Thin Click adapter (CLAUDE.md "CLI adapter discipline"): ``form show`` calls
:func:`propstore.app.forms.show_form` and renders the returned
:class:`~propstore.app.forms.FormShowReport`. The rewrite owner layer exposes only
the single-form show view (no list / search / mutation owner), so this module
builds only ``show``; the absent surfaces are deferred to the phase that lands
their owners rather than fabricated here.
"""
from __future__ import annotations

import click

from propstore.app.forms import FormNotFoundError, show_form
from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit


@click.group()
def form() -> None:
    """Read views over form definitions."""


@form.command("show")
@click.argument("name")
@click.pass_obj
def form_show(obj: CliContext, name: str) -> None:
    """Show one form definition as its rendered YAML source."""

    repo = require_repo(obj)
    try:
        report = show_form(repo, name)
    except FormNotFoundError:
        fail(f"Form '{name}' not found")
    emit(report.yaml_text)
