"""Stance charter and generated document type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import msgspec
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, FamilyCharter, FamilyModel
from quire.documents import DocumentBatchSpec
from quire.families import FamilyDefinition
from quire.references import ForeignKeySpec
from quire.versions import VersionId

from propstore.stances import StanceType


_STANCE_WORLD_CONTRACT_VERSION = VersionId("2026.05.25", allow_placeholder=False)
SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION = VersionId("2026.05.21")


class Stance(FamilyModel):
    pass


STANCE_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="stance",
        name="stance",
        contract_version=_STANCE_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-stance",
            contract_version=_STANCE_WORLD_CONTRACT_VERSION,
            doc_type=Stance,
            placement=FlatYamlPlacement(".derived/stance", str),
        ),
        identity_field="id",
    ),
    model=Stance,
    fields=(
        CharterField(
            "id",
            str,
            primary_key=True,
            nullable=False,
            document_name="artifact_id",
        ),
        CharterField(
            "source_claim",
            str,
            nullable=False,
            foreign_key=ForeignKeySpec(
                name="stance_source_claim",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="stances",
                source_field="source_claim",
                target_family="claims",
                required=False,
            ),
        ),
        CharterField(
            "target",
            str,
            nullable=False,
            foreign_key=ForeignKeySpec(
                name="stance_target_claim",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="stances",
                source_field="target",
                target_family="claims",
                required=False,
            ),
        ),
        CharterField(
            "type",
            StanceType,
            nullable=False,
            enum_type=StanceType,
        ),
        CharterField("artifact_code", str, nullable=False),
        CharterField("perspective_source_claim_id", str, nullable=True),
        CharterField("strength", str, nullable=True),
        CharterField("note", str, nullable=True),
        CharterField("conditions_differ", str, nullable=True),
        CharterField(
            "resolution",
            dict[str, Any],
            parse_boundary="json",
            nullable=True,
        ),
        CharterField(
            "target_justification_id",
            str,
            nullable=True,
            foreign_key=ForeignKeySpec(
                name="stance_target_justification",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="stances",
                source_field="target_justification_id",
                target_family="justifications",
                required=False,
            ),
        ),
        CharterField("classification_model", str, nullable=True),
        CharterField("classification_date", str, nullable=True),
        CharterField("promoted_from_sha", str, nullable=True),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

STANCE_CHARTERS: tuple[FamilyCharter, ...] = (STANCE_CHARTER,)

if TYPE_CHECKING:

    class StanceDocument(msgspec.Struct, forbid_unknown_fields=True):
        artifact_id: str
        source_claim: str
        target: str
        type: StanceType
        artifact_code: str
        perspective_source_claim_id: str | None = None
        strength: str | None = None
        note: str | None = None
        conditions_differ: str | None = None
        resolution: dict[str, Any] | None = None
        target_justification_id: str | None = None
        classification_model: str | None = None
        classification_date: str | None = None
        promoted_from_sha: str | None = None

else:
    StanceDocument: Any = STANCE_CHARTER.generated_document()
    StanceDocument.__name__ = "StanceDocument"
    StanceDocument.__qualname__ = "StanceDocument"
    StanceDocument.__module__ = __name__


from propstore.families.documents.sources import SourceStanceEntryDocument

SOURCE_STANCE_BATCH_SPEC = DocumentBatchSpec(
    batch_name="source-stances",
    item_type=SourceStanceEntryDocument,
    items_field="stances",
    inherited_item_fields=("source", "produced_by"),
)
object.__setattr__(
    STANCE_CHARTER,
    "batch_specs",
    (SOURCE_STANCE_BATCH_SPEC,),
)
