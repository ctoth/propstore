"""SameAs assertion charter and generated document type."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import FamilyCharter


class SameAsRelation(StrEnum):
    SAME_INDIVIDUAL = "sim:sameIndividual"
    CLAIMS_IDENTICAL = "sim:claimsIdentical"
    ALMOST_SAME_AS = "sim:almostSameAs"


@charter(
    key="sameas_assertion",
    name="sameas_assertion",
    contract_version="2026.05.25",
    placement=".derived/sameas_assertion",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-sameas_assertion",
    model_name="SameAsAssertion",
)
class SameAsAssertionDocument(CharterDoc):
    artifact_id: Annotated[str, charter_field(column_name="id", primary_key=True)]
    left_artifact_id: str
    right_artifact_id: str
    relation: Annotated[SameAsRelation, charter_field(enum_type=SameAsRelation)]
    evidence_source: str | None = None
    provenance: Annotated[dict[str, Any] | None, charter_field(json=True)] = None
    confidence: float | None = None


# `@charter` generates the SQLAlchemy-mappable model and binds it into this module
# as `SameAsAssertion`, so `build_sqlalchemy_schema`'s dotted-path model lookup resolves.
SAMEAS_CHARTER: FamilyCharter = SameAsAssertionDocument.__charter__
SAMEAS_CHARTERS: tuple[FamilyCharter, ...] = (SAMEAS_CHARTER,)
