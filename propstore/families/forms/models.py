"""Form family declarative charter classes and generated documents.

``FormDocument`` and ``Form_algebraDocument`` are declarative ``@charter``
classes: each class IS the typed document, and ``@charter`` derives the
:class:`~quire.charters.FamilyCharter` plus the SQLAlchemy model (``Form`` /
``FormAlgebra``) from it. The embedded nested value types
(``FormAlternativeDocument`` / ``FormExtraUnitDocument``) live in
:mod:`propstore.families.forms.declaration` and are referenced here as
``json=True`` fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import CharterIndex, FamilyCharter, FamilyModel

from propstore.families.forms.declaration import (
    FormAlternativeDocument,
    FormExtraUnitDocument,
)


if TYPE_CHECKING:
    # ``@charter`` generates these SQLAlchemy-mappable models at runtime (via
    # ``model_name=``) and binds them into this module's namespace. The static
    # stubs let importers type-check ``Form(...)`` / ``FormAlgebra(...)``
    # construction and attribute access; the runtime classes replace them.
    class Form(FamilyModel): ...

    class FormAlgebra(FamilyModel): ...


_FORM_WORLD_CONTRACT_VERSION = "2026.05.20"


@charter(
    key="form",
    name="form",
    contract_version=_FORM_WORLD_CONTRACT_VERSION,
    placement=".derived/form",
    identity_field="name",
    semantic="propstore.world",
    artifact_family_name="propstore-world-form",
    model_name="Form",
)
class FormDocument(CharterDoc, kw_only=True):
    name: Annotated[str, charter_field(primary_key=True)]
    dimensionless: Annotated[
        bool, charter_field(column_name="is_dimensionless", default_sql="0", order=0)
    ]
    kind: str | None = None
    unit_symbol: str | None = None
    dimensions: Annotated[dict[str, int] | None, charter_field(json=True)] = None
    base: str | None = None
    qudt: str | None = None
    parameters: Annotated[dict[str, Any] | None, charter_field(json=True)] = None
    common_alternatives: Annotated[
        tuple[FormAlternativeDocument, ...] | None, charter_field(json=True)
    ] = ()
    delta_alternatives: Annotated[
        tuple[FormAlternativeDocument, ...] | None, charter_field(json=True)
    ] = ()
    note: str | None = None
    extra_units: Annotated[
        tuple[FormExtraUnitDocument, ...] | None, charter_field(json=True)
    ] = ()
    min: float | None = None
    max: float | None = None


@charter(
    key="form_algebra",
    name="form_algebra",
    contract_version=_FORM_WORLD_CONTRACT_VERSION,
    placement=".derived/form_algebra",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-form_algebra",
    model_name="FormAlgebra",
    indexes=(CharterIndex("idx_form_algebra_output", ("output_form",)),),
)
class Form_algebraDocument(CharterDoc):
    id: Annotated[int, charter_field(primary_key=True)]
    output_form: str
    input_forms: str
    operation: str
    source_concept_id: str
    source_formula: str
    dim_verified: Annotated[int, charter_field(default_sql="1")]


FORM_CHARTER: FamilyCharter = FormDocument.__charter__
FORM_ALGEBRA_CHARTER: FamilyCharter = Form_algebraDocument.__charter__
FORM_DOCUMENT_TYPE = FormDocument
FORMS_CHARTERS: tuple[FamilyCharter, FamilyCharter] = (
    FORM_CHARTER,
    FORM_ALGEBRA_CHARTER,
)
