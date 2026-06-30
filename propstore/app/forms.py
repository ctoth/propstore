"""Owner-layer form show report.

``show_form`` loads one authored :class:`FormDefinition` and renders it back to
its YAML source for the ``pks form show`` adapter. The form definition *is* the
charter document (no separate parse step), so the report carries the typed
``FormDefinition`` alongside its rendered text.

Form-algebra decomposition/use views (a form expressed as the dimensional product
of other forms) are not part of this slice: the charter rewrite has no
form-algebra projection on :class:`~propstore.world.WorldQuery`, so rather than
fabricate empty decomposition rows the report omits them until that projection
lands.
"""

from __future__ import annotations

from dataclasses import dataclass

from quire.documents import render_document

from propstore.families.forms import FormDefinition
from propstore.reporting import JsonReportMixin
from propstore.repository import Repository


class FormNotFoundError(Exception):
    """Raised when no form is authored under the requested name."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Unknown form: {name}")
        self.name = name


@dataclass(frozen=True)
class FormShowReport(JsonReportMixin):
    """A form's rendered YAML source plus its typed definition."""

    yaml_text: str
    form: FormDefinition


def show_form(repo: Repository, name: str) -> FormShowReport:
    """Load form ``name`` and return its rendered YAML plus typed definition.

    Raises :class:`FormNotFoundError` when no form is authored under ``name``.
    """

    loaded = repo.families.form.load(name)
    if not isinstance(loaded, FormDefinition):
        raise FormNotFoundError(name)
    return FormShowReport(yaml_text=render_document(loaded), form=loaded)
