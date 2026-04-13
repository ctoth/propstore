from __future__ import annotations

from dataclasses import dataclass, field


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
        if target in self.primary.logical_to_artifact:
            return self.primary.logical_to_artifact[target]
        if target in self.primary.artifact_ids or target.startswith("ps:claim:"):
            return target
        raise ValueError(f"Unresolved promoted stance target: {target}")

    def target_is_known(self, target: object) -> bool:
        if not isinstance(target, str) or not target:
            return False
        return (
            target in self.source.artifact_ids
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

    def resolved_map(self) -> dict[str, str]:
        return {
            local_id: artifact_id
            for local_id, artifact_id in self._local_to_artifact.items()
            if artifact_id is not None
        }
