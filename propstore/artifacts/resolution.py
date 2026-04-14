from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from propstore.artifacts.indexes import ClaimReferenceIndex


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
