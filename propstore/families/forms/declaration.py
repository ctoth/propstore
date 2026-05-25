"""Form world-store family charters."""

from __future__ import annotations

from typing import Any, cast

import msgspec

from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, CharterIndex, FamilyCharter
from quire.families import FamilyDefinition
from quire.versions import VersionId

from .models import Form, FormAlgebra, FormDocumentProtocol


_FORM_WORLD_CONTRACT_VERSION = VersionId("2026.05.20", allow_placeholder=False)


class FormAlternativeDocument(msgspec.Struct, forbid_unknown_fields=True):
    unit: str
    type: str
    multiplier: float = 1.0
    offset: float = 0.0
    base: float = 10.0
    divisor: float = 1.0
    reference: float = 1.0


class FormExtraUnitDocument(msgspec.Struct, forbid_unknown_fields=True):
    symbol: str
    dimensions: dict[str, int] = msgspec.field(default_factory=dict)


FORM_CHARTER = FamilyCharter(
    family=FamilyDefinition(
        key="form",
        name="form",
        contract_version=_FORM_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-form",
            contract_version=_FORM_WORLD_CONTRACT_VERSION,
            doc_type=Form,
            placement=FlatYamlPlacement(".derived/form", str),
        ),
        identity_field="name",
    ),
    model=Form,
    fields=(
        CharterField("name", str, primary_key=True, nullable=False),
        CharterField("kind", str, nullable=True),
        CharterField("unit_symbol", str, nullable=True),
        CharterField(
            "is_dimensionless",
            bool,
            nullable=False,
            default_sql="0",
            document_name="dimensionless",
            document_order=0,
        ),
        CharterField("dimensions", dict[str, int], parse_boundary="json", nullable=True),
        CharterField("base", str, nullable=True),
        CharterField("qudt", str, nullable=True),
        CharterField("parameters", dict[str, Any], parse_boundary="json", nullable=True),
        CharterField(
            "common_alternatives",
            tuple[FormAlternativeDocument, ...],
            parse_boundary="json",
            nullable=True,
            default=(),
        ),
        CharterField(
            "delta_alternatives",
            tuple[FormAlternativeDocument, ...],
            parse_boundary="json",
            nullable=True,
            default=(),
        ),
        CharterField("note", str, nullable=True),
        CharterField(
            "extra_units",
            tuple[FormExtraUnitDocument, ...],
            parse_boundary="json",
            nullable=True,
            default=(),
        ),
        CharterField("min", float, nullable=True),
        CharterField("max", float, nullable=True),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

FORM_DOCUMENT_TYPE = cast(type[FormDocumentProtocol], FORM_CHARTER.generated_document())

FORM_ALGEBRA_CHARTER = FamilyCharter(
    family=FamilyDefinition(
        key="form_algebra",
        name="form_algebra",
        contract_version=_FORM_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-form_algebra",
            contract_version=_FORM_WORLD_CONTRACT_VERSION,
            doc_type=FormAlgebra,
            placement=FlatYamlPlacement(".derived/form_algebra", str),
        ),
        identity_field="id",
    ),
    model=FormAlgebra,
    fields=(
        CharterField("id", int, primary_key=True, nullable=False),
        CharterField("output_form", str, nullable=False),
        CharterField("input_forms", str, nullable=False),
        CharterField("operation", str, nullable=False),
        CharterField("source_concept_id", str),
        CharterField("source_formula", str),
        CharterField("dim_verified", int, nullable=False, default_sql="1"),
    ),
    indexes=(CharterIndex("idx_form_algebra_output", ("output_form",)),),
    semantic_metadata={"semantic": "propstore.world"},
)


FORMS_CHARTERS: tuple[FamilyCharter, FamilyCharter] = (
    FORM_CHARTER,
    FORM_ALGEBRA_CHARTER,
)
