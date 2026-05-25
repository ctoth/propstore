"""SameAs assertion charter and generated document type."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

import msgspec
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, FamilyCharter, FamilyModel
from quire.families import FamilyDefinition
from quire.versions import VersionId


_SAMEAS_WORLD_CONTRACT_VERSION = VersionId("2026.05.25", allow_placeholder=False)


class SameAsRelation(StrEnum):
    SAME_INDIVIDUAL = "sim:sameIndividual"
    CLAIMS_IDENTICAL = "sim:claimsIdentical"
    ALMOST_SAME_AS = "sim:almostSameAs"


class SameAsAssertion(FamilyModel):
    pass


SAMEAS_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="sameas_assertion",
        name="sameas_assertion",
        contract_version=_SAMEAS_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-sameas_assertion",
            contract_version=_SAMEAS_WORLD_CONTRACT_VERSION,
            doc_type=SameAsAssertion,
            placement=FlatYamlPlacement(".derived/sameas_assertion", str),
        ),
        identity_field="id",
    ),
    model=SameAsAssertion,
    fields=(
        CharterField(
            "id",
            str,
            primary_key=True,
            nullable=False,
            document_name="artifact_id",
        ),
        CharterField("left_artifact_id", str, nullable=False),
        CharterField("right_artifact_id", str, nullable=False),
        CharterField(
            "relation",
            SameAsRelation,
            nullable=False,
            enum_type=SameAsRelation,
        ),
        CharterField("evidence_source", str, nullable=True),
        CharterField(
            "provenance",
            dict[str, Any],
            parse_boundary="json",
            nullable=True,
        ),
        CharterField("confidence", float, nullable=True),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

SAMEAS_CHARTERS: tuple[FamilyCharter, ...] = (SAMEAS_CHARTER,)

if TYPE_CHECKING:

    class SameAsAssertionDocument(msgspec.Struct, forbid_unknown_fields=True):
        artifact_id: str
        left_artifact_id: str
        right_artifact_id: str
        relation: SameAsRelation
        evidence_source: str | None = None
        provenance: dict[str, Any] | None = None
        confidence: float | None = None

else:
    SameAsAssertionDocument: Any = SAMEAS_CHARTER.generated_document()
    SameAsAssertionDocument.__name__ = "SameAsAssertionDocument"
    SameAsAssertionDocument.__qualname__ = "SameAsAssertionDocument"
    SameAsAssertionDocument.__module__ = __name__
