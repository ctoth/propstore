from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from propstore.artifacts.documents.claims import ClaimLogicalIdDocument
from propstore.artifacts.documents.sources import SourceClaimsDocument

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class ClaimReferenceIndex:
    local_to_artifact: dict[str, str] = field(default_factory=dict)
    logical_to_artifact: dict[str, str] = field(default_factory=dict)
    artifact_ids: set[str] = field(default_factory=set)

    def resolve_local(self, reference: object) -> str:
        if not isinstance(reference, str) or not reference:
            raise ValueError("claim reference must be a non-empty string")
        if reference.startswith("ps:claim:"):
            return reference
        artifact_id = self.local_to_artifact.get(reference)
        if artifact_id is None:
            raise ValueError(f"unresolved local claim reference: {reference}")
        return artifact_id

    def rewrite_local_target(self, reference: object) -> object:
        if not isinstance(reference, str) or not reference:
            return reference
        return self.local_to_artifact.get(reference, reference)

    def has_artifact(self, reference: object) -> bool:
        return isinstance(reference, str) and reference in self.artifact_ids

    def has_logical(self, reference: object) -> bool:
        return isinstance(reference, str) and reference in self.logical_to_artifact


def build_source_claim_reference_index(document: SourceClaimsDocument | None) -> ClaimReferenceIndex:
    local_to_artifact: dict[str, str] = {}
    logical_to_artifact: dict[str, str] = {}
    artifact_ids: set[str] = set()
    if document is None:
        return ClaimReferenceIndex()

    for claim in document.claims:
        artifact_id = claim.artifact_id
        if artifact_id is None:
            continue
        artifact_ids.add(artifact_id)
        local_id = claim.source_local_id
        if local_id:
            local_to_artifact[local_id] = artifact_id
        for logical_id in claim.logical_ids:
            logical_to_artifact[_formatted_logical_id(logical_id)] = artifact_id

    return ClaimReferenceIndex(
        local_to_artifact=local_to_artifact,
        logical_to_artifact=logical_to_artifact,
        artifact_ids=artifact_ids,
    )


def load_source_claim_reference_index(repo: Repository, source_name: str) -> ClaimReferenceIndex:
    from propstore.artifacts.refs import SourceRef

    document = repo.families.source_claims.load(SourceRef(source_name))
    return build_source_claim_reference_index(document)


def load_primary_branch_claim_reference_index(repo: Repository) -> ClaimReferenceIndex:
    logical_to_artifact: dict[str, str] = {}
    artifact_ids: set[str] = set()

    for ref in repo.families.claims.list():
        claim_file = repo.families.claims.require(ref)
        for claim in claim_file.claims:
            artifact_id = claim.artifact_id
            if not isinstance(artifact_id, str) or not artifact_id:
                continue
            artifact_ids.add(artifact_id)
            for logical_id in claim.logical_ids:
                logical_to_artifact[_formatted_logical_id(logical_id)] = artifact_id

    return ClaimReferenceIndex(
        logical_to_artifact=logical_to_artifact,
        artifact_ids=artifact_ids,
    )


def _formatted_logical_id(logical_id: ClaimLogicalIdDocument) -> str:
    return f"{logical_id.namespace}:{logical_id.value}"
