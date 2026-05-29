"""Stance charter and generated document type."""

from __future__ import annotations

from typing import Annotated, Any

from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import FamilyCharter
from quire.documents import DocumentBatchSpec
from quire.lifecycle import ConflictPolicy, FamilyState, FamilyTransition
from quire.references import ForeignKeySpec
from quire.versions import VersionId

from propstore.families.claims.declaration import (
    ClaimSourceDocument,
    ExtractionProvenanceDocument,
    ResolutionDocument,
)
from propstore.opinion import Opinion
from propstore.stances import StanceType


_STANCE_WORLD_CONTRACT_VERSION = VersionId("2026.05.25", allow_placeholder=False)
SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION = VersionId("2026.05.21")


@charter(
    key="stance",
    name="stance",
    contract_version=_STANCE_WORLD_CONTRACT_VERSION,
    placement=".derived/stance",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-stance",
    model_name="Stance",
    states=(
        FamilyState("proposed", document_label="proposal"),
        FamilyState("canonical", document_label="canonical", terminal=True),
    ),
    transitions=(
        FamilyTransition(
            "promote_proposal",
            source="proposed",
            target="canonical",
            materializer="stance_proposal_to_canonical",
            conflict_policy=ConflictPolicy.REPLACE,
        ),
    ),
)
class StanceDocument(CharterDoc):
    artifact_id: Annotated[
        str,
        charter_field(
            column_name="id",
            primary_key=True,
            nullable=False,
            artifact=True,
        ),
    ]
    source_claim: Annotated[
        str,
        charter_field(
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
    ]
    target: Annotated[
        str,
        charter_field(
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
    ]
    type: Annotated[StanceType, charter_field(nullable=False, enum_type=StanceType)]
    artifact_code: Annotated[str, charter_field(artifact=True, nullable=False)]
    perspective_source_claim_id: str | None = None
    strength: str | None = None
    note: str | None = None
    conditions_differ: str | None = None
    opinion: Opinion | None = None
    resolution: Annotated[
        dict[str, Any] | None,
        charter_field(json=True, nullable=True),
    ] = None
    target_justification_id: Annotated[
        str | None,
        charter_field(
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
    ] = None
    classification_model: str | None = None
    classification_date: str | None = None
    promoted_from_sha: str | None = None


STANCE_CHARTER: FamilyCharter = StanceDocument.__charter__

STANCE_CHARTERS: tuple[FamilyCharter, ...] = (STANCE_CHARTER,)


@charter(
    key="source-stance-entry-document",
    name="source-stance-entry",
    contract_version=_STANCE_WORLD_CONTRACT_VERSION,
    placement=".source/stances",
    identity_field="source_claim",
    semantic="propstore.source",
    artifact_family_name="propstore-source-stance-entry-document",
    model_name="SourceStanceEntry",
)
class SourceStanceEntryDocument(CharterDoc, kw_only=True):
    source: Annotated[ClaimSourceDocument | None, charter_field(nullable=True)] = None
    produced_by: Annotated[
        ExtractionProvenanceDocument | None, charter_field(nullable=True)
    ] = None
    source_claim: Annotated[str | None, charter_field(nullable=True)] = None
    perspective_source_claim_id: Annotated[str | None, charter_field(nullable=True)] = None
    target: Annotated[str | None, charter_field(nullable=True)] = None
    type: Annotated[StanceType | None, charter_field(nullable=True, enum_type=StanceType)] = None
    strength: Annotated[str | None, charter_field(nullable=True)] = None
    note: Annotated[str | None, charter_field(nullable=True)] = None
    conditions_differ: Annotated[str | None, charter_field(nullable=True)] = None
    opinion: Annotated[Opinion | None, charter_field(nullable=True)] = None
    resolution: Annotated[ResolutionDocument | None, charter_field(nullable=True)] = None
    target_justification_id: Annotated[str | None, charter_field(nullable=True)] = None
    artifact_code: Annotated[str | None, charter_field(nullable=True)] = None


SOURCE_STANCE_ENTRY_DOCUMENT_CHARTER: FamilyCharter = (
    SourceStanceEntryDocument.__charter__
)

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
