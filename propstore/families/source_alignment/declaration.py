"""Source alignment declarative charter class and embedded documents."""

from __future__ import annotations

from typing import Annotated

from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import FamilyCharter
from quire.versions import VersionId


SOURCE_ALIGNMENT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")


class AlignmentArgumentDocument(CharterDoc):
    id: str
    source: str
    local_handle: str
    proposed_name: str
    proposed_uri: str
    definition: str
    form: str


class AlignmentFrameworkDocument(CharterDoc):
    attacks: tuple[tuple[str, str], ...]
    ignorance: tuple[tuple[str, str], ...]
    non_attacks: tuple[tuple[str, str], ...]


class AlignmentQueriesDocument(CharterDoc):
    skeptical_acceptance: tuple[str, ...]
    credulous_acceptance: tuple[str, ...]
    operator_scores: dict[str, dict[str, int]]


class AlignmentDecisionDocument(CharterDoc):
    status: str
    accepted: tuple[str, ...]
    rejected: tuple[str, ...]
    promoted_concept: str | None = None


@charter(
    key="concept_alignment_artifact",
    name="concept_alignment_artifact",
    contract_version=SOURCE_ALIGNMENT_FAMILY_CONTRACT_VERSION,
    placement=".derived/concept_alignment_artifact",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-concept_alignment_artifact",
    model_name="ConceptAlignmentArtifact",
)
class ConceptAlignmentArtifactDocument(CharterDoc):
    kind: str
    id: Annotated[str, charter_field(primary_key=True)]
    sources: Annotated[tuple[str, ...], charter_field(json=True)]
    arguments: Annotated[tuple[AlignmentArgumentDocument, ...], charter_field(json=True)]
    framework: Annotated[AlignmentFrameworkDocument, charter_field(json=True)]
    queries: Annotated[AlignmentQueriesDocument, charter_field(json=True)]
    decision: Annotated[AlignmentDecisionDocument, charter_field(json=True)]


CONCEPT_ALIGNMENT_ARTIFACT_CHARTER: FamilyCharter = (
    ConceptAlignmentArtifactDocument.__charter__
)
SOURCE_ALIGNMENT_CHARTERS: tuple[FamilyCharter, ...] = (
    CONCEPT_ALIGNMENT_ARTIFACT_CHARTER,
)
