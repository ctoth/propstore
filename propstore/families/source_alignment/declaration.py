"""Source alignment charter and generated document type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import msgspec
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, FamilyCharter, FamilyModel
from quire.families import FamilyDefinition
from quire.versions import VersionId


SOURCE_ALIGNMENT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")


class AlignmentArgumentDocument(msgspec.Struct, forbid_unknown_fields=True):
    id: str
    source: str
    local_handle: str
    proposed_name: str
    proposed_uri: str
    definition: str
    form: str


class AlignmentFrameworkDocument(msgspec.Struct, forbid_unknown_fields=True):
    attacks: tuple[tuple[str, str], ...]
    ignorance: tuple[tuple[str, str], ...]
    non_attacks: tuple[tuple[str, str], ...]


class AlignmentQueriesDocument(msgspec.Struct, forbid_unknown_fields=True):
    skeptical_acceptance: tuple[str, ...]
    credulous_acceptance: tuple[str, ...]
    operator_scores: dict[str, dict[str, int]]


class AlignmentDecisionDocument(msgspec.Struct, forbid_unknown_fields=True):
    status: str
    accepted: tuple[str, ...]
    rejected: tuple[str, ...]
    promoted_concept: str | None = None


class ConceptAlignmentArtifact(FamilyModel):
    pass


CONCEPT_ALIGNMENT_ARTIFACT_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="concept_alignment_artifact",
        name="concept_alignment_artifact",
        contract_version=SOURCE_ALIGNMENT_FAMILY_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-concept_alignment_artifact",
            contract_version=SOURCE_ALIGNMENT_FAMILY_CONTRACT_VERSION,
            doc_type=ConceptAlignmentArtifact,
            placement=FlatYamlPlacement(".derived/concept_alignment_artifact", str),
        ),
        identity_field="id",
    ),
    model=ConceptAlignmentArtifact,
    fields=(
        CharterField("kind", str, nullable=False),
        CharterField("id", str, primary_key=True, nullable=False),
        CharterField(
            "sources",
            tuple[str, ...],
            parse_boundary="json",
            nullable=False,
        ),
        CharterField(
            "arguments",
            tuple[AlignmentArgumentDocument, ...],
            parse_boundary="json",
            nullable=False,
        ),
        CharterField(
            "framework",
            AlignmentFrameworkDocument,
            parse_boundary="json",
            nullable=False,
        ),
        CharterField(
            "queries",
            AlignmentQueriesDocument,
            parse_boundary="json",
            nullable=False,
        ),
        CharterField(
            "decision",
            AlignmentDecisionDocument,
            parse_boundary="json",
            nullable=False,
        ),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

SOURCE_ALIGNMENT_CHARTERS: tuple[FamilyCharter, ...] = (
    CONCEPT_ALIGNMENT_ARTIFACT_CHARTER,
)

if TYPE_CHECKING:

    class ConceptAlignmentArtifactDocument(msgspec.Struct, forbid_unknown_fields=True):
        kind: str
        id: str
        sources: tuple[str, ...]
        arguments: tuple[AlignmentArgumentDocument, ...]
        framework: AlignmentFrameworkDocument
        queries: AlignmentQueriesDocument
        decision: AlignmentDecisionDocument

else:
    ConceptAlignmentArtifactDocument: Any = (
        CONCEPT_ALIGNMENT_ARTIFACT_CHARTER.generated_document()
    )
    ConceptAlignmentArtifactDocument.__name__ = "ConceptAlignmentArtifactDocument"
    ConceptAlignmentArtifactDocument.__qualname__ = "ConceptAlignmentArtifactDocument"
    ConceptAlignmentArtifactDocument.__module__ = __name__
