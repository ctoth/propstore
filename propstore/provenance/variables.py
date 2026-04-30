"""Stable source variables for provenance polynomials."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import NewType

from propstore.provenance import Provenance


SourceVariableId = NewType("SourceVariableId", str)


class SourceRole(StrEnum):
    CLAIM = "claim"
    RULE = "rule"
    MEASUREMENT = "measurement"
    CALIBRATION = "calibration"
    LIFTING_RULE = "lifting_rule"
    SOLVER_WITNESS = "solver_witness"
    ASSUMPTION = "assumption"
    CONTEXT = "context"


@dataclass(frozen=True)
class SourceVariable:
    id: SourceVariableId
    role: SourceRole
    artifact_id: str
    canonical_body_hash: str
    provenance: Provenance

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", SourceRole(self.role))
        object.__setattr__(self, "artifact_id", str(self.artifact_id))
        object.__setattr__(self, "canonical_body_hash", str(self.canonical_body_hash))
        expected = derive_source_variable_id(
            self.role,
            self.artifact_id,
            self.canonical_body_hash,
        )
        if self.id != expected:
            raise ValueError(
                "SourceVariable id must be derived from role, artifact_id, "
                "and canonical_body_hash"
            )


def derive_source_variable_id(
    role: SourceRole,
    artifact_id: str,
    canonical_body_hash: str,
) -> SourceVariableId:
    normalized_role = SourceRole(role)
    body = "\0".join((normalized_role.value, str(artifact_id), str(canonical_body_hash)))
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return SourceVariableId(f"ps:source:{normalized_role.value}:{digest}")
