from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from propstore.families.claims.documents import ClaimLogicalIdDocument
from propstore.families.documents.sources import SourceClaimsDocument

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


@dataclass(frozen=True)
class ClaimReferenceResolver:
    source: ClaimReferenceIndex
    primary: ClaimReferenceIndex = field(default_factory=ClaimReferenceIndex)

    def resolve_promoted_target(self, target: object) -> str:
        if not isinstance(target, str) or not target:
            raise ValueError("stance target must be a non-empty string")
        if target in self.source.local_to_artifact:
            return self.source.local_to_artifact[target]
        if target in self.source.logical_to_artifact:
            return self.source.logical_to_artifact[target]
        if target in self.source.artifact_ids:
            return target
        if target in self.primary.logical_to_artifact:
            return self.primary.logical_to_artifact[target]
        if target in self.primary.artifact_ids:
            return target
        raise ValueError(f"Unresolved promoted stance target: {target}")

    def target_is_known(self, target: object) -> bool:
        if not isinstance(target, str) or not target:
            return False
        return (
            target in self.source.artifact_ids
            or target in self.source.local_to_artifact
            or target in self.primary.artifact_ids
            or target in self.source.logical_to_artifact
            or target in self.primary.logical_to_artifact
        )


@dataclass
class ImportedClaimHandleIndex:
    _local_to_artifact: dict[str, str | None] = field(default_factory=dict)

    def record(self, local_id: str, artifact_id: str) -> bool:
        previous = self._local_to_artifact.get(local_id)
        if previous is None and local_id in self._local_to_artifact:
            return False
        if previous is not None and previous != artifact_id:
            self._local_to_artifact[local_id] = None
            return True
        self._local_to_artifact[local_id] = artifact_id
        return False

    def require_unambiguous(self, reference: object, *, path: str, role: str) -> None:
        if not isinstance(reference, str):
            return
        if reference in self._local_to_artifact and self._local_to_artifact[reference] is None:
            raise ValueError(
                f"Imported stance file {path!r} references ambiguous {role} {reference!r}"
            )

    def resolve(self, reference: object, *, path: str, role: str) -> object:
        self.require_unambiguous(reference, path=path, role=role)
        if not isinstance(reference, str):
            return reference
        resolved = self._local_to_artifact.get(reference)
        if resolved is None:
            return reference
        return resolved

    def rewrite_stance_payload(self, payload: dict[str, Any], *, path: str) -> dict[str, Any]:
        rewritten = dict(payload)
        rewritten["source_claim"] = self.resolve(
            rewritten.get("source_claim"),
            path=path,
            role="source_claim",
        )

        raw_stances = rewritten.get("stances")
        if not isinstance(raw_stances, list):
            return rewritten

        updated_stances: list[Any] = []
        for stance in raw_stances:
            if not isinstance(stance, dict):
                updated_stances.append(stance)
                continue
            rewritten_stance = dict(stance)
            rewritten_stance["target"] = self.resolve(
                rewritten_stance.get("target"),
                path=path,
                role="target",
            )
            updated_stances.append(rewritten_stance)
        rewritten["stances"] = updated_stances
        return rewritten


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
    from propstore.families.registry import SourceRef

    document = repo.families.source_claims.load(SourceRef(source_name))
    return build_source_claim_reference_index(document)


def load_primary_branch_claim_reference_index(repo: Repository) -> ClaimReferenceIndex:
    logical_to_artifact: dict[str, str] = {}
    artifact_ids: set[str] = set()

    for handle in repo.families.claims.iter_handles():
        claim_file = handle.document
        file_namespace = handle.ref.name
        for claim in claim_file.claims:
            artifact_id = claim.artifact_id
            if not isinstance(artifact_id, str) or not artifact_id:
                continue
            artifact_ids.add(artifact_id)
            for logical_id in claim.logical_ids:
                logical_to_artifact[_formatted_logical_id(logical_id)] = artifact_id
                logical_to_artifact[f"{file_namespace}:{logical_id.value}"] = artifact_id

    return ClaimReferenceIndex(
        logical_to_artifact=logical_to_artifact,
        artifact_ids=artifact_ids,
    )


def _formatted_logical_id(logical_id: ClaimLogicalIdDocument) -> str:
    return f"{logical_id.namespace}:{logical_id.value}"
