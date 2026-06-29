"""The ``FormDefinition`` entity — a physical-dimension form.

A *form* is the dimensional/kind contract a concept's quantities live in: its SI
base-dimension exponents, its measurement :class:`~condition_ir.KindType`, its
canonical and alternative units, and (for category/structural kinds) free-form
parameters. ``LexicalEntry.physical_dimension_form`` (the lemon entry side, Phase
2a) references one of these by ``name`` — dimensions live on the *entry*, never on
:class:`~propstore.core.lemon.forms.LexicalForm`.

Discipline (PLAN.md §12, CLAUDE.md substrate boundary):

* ONE canonical ``FormDefinition`` — a quire charter. There is no ``FormDocument``
  / ``FormRecord`` / ``FormRow`` second spelling and no ``to_payload`` /
  ``from_payload`` / ``coerce_``: the git document, the sidecar columns, and the
  contract all fall out of these field annotations (see :class:`FormRepository`).
* ``KindType`` is imported from ``condition_ir`` and used directly — propstore
  does not mirror it.
* Dimensional *algebra* is bridgman's: :func:`verify_form_algebra` composes
  ``propstore.dimensions`` (which calls ``bridgman``) and never re-spells a
  signature. Dimensionally invalid algebra is reported (``dim_verified`` False),
  never dropped — non-commitment holds at the form layer too.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Protocol

import msgspec
from condition_ir import KindType
from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import charter_catalog
from quire.family_store import DocumentFamilyStore
from quire.git_store import GitStore
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.sqlalchemy_store import create_sqlalchemy_store, readonly_session, writable_session
from sqlalchemy import select

from propstore.dimensions import (
    ExtraUnitDefinition,
    UnitConversion,
    dimensions_match,
)


def _empty_conversions() -> dict[str, UnitConversion]:
    return {}


def _empty_parameters() -> dict[str, object]:
    return {}


@charter(
    key="form",
    name="form",
    contract_version="2026.06.28",
    placement="form",
    identity_field="name",
    semantic="propstore.form",
)
class FormDefinition(CharterDoc):
    """A physical-dimension form: dimensions, kind, units, and parameters.

    The class *is* the document: its annotated attributes are exactly the stored
    fields and the sidecar ``form`` columns. ``name`` is the identity. JSON-typed
    fields (dimensions, units, conversions, parameters) project to JSON columns.
    """

    name: Annotated[str, charter_field(primary_key=True)]
    kind: KindType
    unit_symbol: str | None = None
    is_dimensionless: bool = False
    dimensions: Annotated[dict[str, int] | None, charter_field(json=True)] = None
    allowed_units: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    extra_units: Annotated[tuple[ExtraUnitDefinition, ...], charter_field(json=True)] = ()
    conversions: Annotated[dict[str, UnitConversion], charter_field(json=True)] = msgspec.field(
        default_factory=_empty_conversions
    )
    delta_conversions: Annotated[
        dict[str, UnitConversion], charter_field(json=True)
    ] = msgspec.field(default_factory=_empty_conversions)
    parameters: Annotated[dict[str, object], charter_field(json=True)] = msgspec.field(
        default_factory=_empty_parameters
    )
    min_value: float | None = None
    max_value: float | None = None


def validate_form_definition(form: FormDefinition) -> tuple[str, ...]:
    """Return authoring problems with a form (empty tuple if consistent).

    This is a render/diagnostics check, not a storage gate: an inconsistent form
    is still stored and projected (non-commitment); the caller decides what to do
    with the reported problems.
    """

    errors: list[str] = []
    dims = form.dimensions
    if dims is not None:
        for key in dims:
            if not key.isidentifier():
                errors.append(f"invalid dimension key '{key}'")
    nonzero = {} if dims is None else {k: v for k, v in dims.items() if v != 0}
    if form.is_dimensionless and nonzero:
        errors.append("dimensionless form cannot declare non-empty dimensions")
    if (
        form.kind == KindType.QUANTITY
        and not form.is_dimensionless
        and dims is not None
        and not nonzero
    ):
        errors.append("non-dimensionless quantity form must have a non-zero dimension")
    return tuple(errors)


def verify_form_algebra(
    output: FormDefinition,
    factors: Sequence[tuple[FormDefinition, int]],
) -> bool:
    """Whether ``output`` is the dimensional product of ``factors`` (form, exponent).

    Verification is via bridgman's dimensional algebra (through
    ``propstore.dimensions.dimensions_match``). When the output or any factor
    lacks dimensions the relation is *unverifiable* — this returns ``False``
    (``dim_verified`` is recorded, not dropped), it never fabricates a pass.
    """

    if output.dimensions is None:
        return False
    factor_dims: list[tuple[dict[str, int], int]] = []
    for form_def, exponent in factors:
        if form_def.dimensions is None:
            return False
        factor_dims.append((form_def.dimensions, exponent))
    return dimensions_match(output.dimensions, factor_dims)


@dataclass(frozen=True)
class _StoreOwner:
    """Placement owner for the document store (mirrors ``ConceptRepository``)."""

    branch: str = "master"


class _FormRow(Protocol):
    """Structural view of a sidecar ``form`` row.

    The sidecar model is built dynamically from the charter, so it has no static
    class to import; this names the charter-derived columns the repository reads
    back, giving typed access without a cast or ignore.
    """

    name: str
    kind: KindType | str
    unit_symbol: str | None
    is_dimensionless: bool
    dimensions: dict[str, int] | None
    allowed_units: tuple[str, ...]
    extra_units: tuple[ExtraUnitDefinition, ...]
    conversions: dict[str, UnitConversion]
    delta_conversions: dict[str, UnitConversion]
    parameters: dict[str, object]
    min_value: float | None
    max_value: float | None


def _row_to_form(row: _FormRow) -> FormDefinition:
    """Rebuild the one ``FormDefinition`` from a sidecar row (not a second spelling)."""

    kind = row.kind if isinstance(row.kind, KindType) else KindType(row.kind)
    return FormDefinition(
        name=row.name,
        kind=kind,
        unit_symbol=row.unit_symbol,
        is_dimensionless=row.is_dimensionless,
        dimensions=row.dimensions,
        allowed_units=row.allowed_units,
        extra_units=row.extra_units,
        conversions=row.conversions,
        delta_conversions=row.delta_conversions,
        parameters=row.parameters,
        min_value=row.min_value,
        max_value=row.max_value,
    )


class FormRepository:
    """Author physical-dimension forms to git and project them into a sidecar.

    Same shape as ``propstore.storage.ConceptRepository``: a charter-driven
    ``DocumentFamilyStore`` for the canonical document and a charter-derived
    SQLAlchemy sidecar. The ``form`` table and its columns are not hand-authored —
    they are the charter's fields.
    """

    def __init__(self, backend: GitStore | None = None) -> None:
        self._store = DocumentFamilyStore(
            owner=_StoreOwner(),
            backend=backend if backend is not None else GitStore.init_memory(),
            codec=FormDefinition.__charter__.document_codec(),
        )
        self._family = FormDefinition.__charter__.family.artifact_family

    def author(self, form: FormDefinition, *, message: str) -> str:
        """Store the RAW authored form keyed by ``name``; return the commit sha."""

        return self._store.save(self._family, form.name, form, message=message)

    def get(self, name: str) -> FormDefinition | None:
        """Load a form by name from the git store, or ``None``."""

        return self._store.load(self._family, name)

    def iter_forms(self) -> Iterator[FormDefinition]:
        """Iterate every authored form document in the git store."""

        for handle in self._store.iter_handles(self._family):
            yield handle.document

    def build_sidecar(self, path: Path) -> SqlAlchemySchema:
        """Project EVERY authored form into a fresh sqlite sidecar.

        Never filters: an inconsistent form lands as a row just like a clean one.
        Returns the built schema so the render layer can query the same instance.
        """

        schema = build_sqlalchemy_schema(charter_catalog(FormDefinition.__charter__))
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema) as session:
            for form in self.iter_forms():
                session.add_family(
                    "form",
                    {
                        "name": form.name,
                        "kind": form.kind,
                        "unit_symbol": form.unit_symbol,
                        "is_dimensionless": form.is_dimensionless,
                        "dimensions": form.dimensions,
                        "allowed_units": form.allowed_units,
                        "extra_units": form.extra_units,
                        "conversions": form.conversions,
                        "delta_conversions": form.delta_conversions,
                        "parameters": form.parameters,
                        "min_value": form.min_value,
                        "max_value": form.max_value,
                    },
                )
            session.commit()
        return schema

    def render_forms(self, path: Path, schema: SqlAlchemySchema) -> list[FormDefinition]:
        """Return every form from the sidecar, rebuilt as ``FormDefinition``."""

        model = schema.model("form")
        with readonly_session(path, schema) as session:
            rows = list(session.scalars(select(model)))
        return [_row_to_form(row) for row in rows]
