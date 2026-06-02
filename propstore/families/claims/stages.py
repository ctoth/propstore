"""Claim semantic stage objects."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ast_equiv import canonical_dump

from propstore.compiler.ir import ClaimCompilationBundle
from propstore.families.claims.types import ClaimType
from propstore.core.id_types import ConceptId
from propstore.families.claims.declaration import VariableBindingDocument


class ClaimStage(StrEnum):
    AUTHORED = "claim.authored"
    CHECKED = "claim.checked"


@dataclass(frozen=True)
class ClaimAlgorithmVariable:
    name: str | None = None
    symbol: str | None = None
    concept_id: ConceptId | None = None
    role: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))


def parse_claim_algorithm_variables(
    raw: object,
) -> tuple[ClaimAlgorithmVariable, ...]:
    if raw is None or raw == "":
        return ()
    loaded = raw
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return ()
    if isinstance(loaded, Mapping):
        raise ValueError(
            "algorithm claim variables must be a list of variable bindings"
        )
    if isinstance(loaded, list):
        variables: list[ClaimAlgorithmVariable] = []
        for entry in loaded:
            if not isinstance(entry, Mapping):
                continue
            variables.append(parse_claim_algorithm_variable_entry(entry))
        return tuple(variables)
    return ()


def claim_algorithm_canonical_ast(
    body: str | None,
    variables: Sequence[ClaimAlgorithmVariable | VariableBindingDocument],
) -> str | None:
    if body is None:
        return None
    bindings: dict[str, str] = {}
    for variable in variables:
        concept_id = (
            variable.concept_id
            if isinstance(variable, ClaimAlgorithmVariable)
            else variable.concept
        )
        if concept_id is None:
            continue
        name = variable.name or variable.symbol
        if name:
            bindings[name] = str(concept_id)
    return canonical_dump(body, bindings)


@dataclass(frozen=True)
class ClaimCheckedBundle:
    bundle: ClaimCompilationBundle
    raw_id_quarantine_records: tuple[RawIdQuarantineRecord, ...] = ()


@dataclass(frozen=True)
class PromotionBlockedReason:
    kind: str
    detail: str


@dataclass(frozen=True)
class PromotionBlockedClaimFact:
    artifact_id: str
    claim_type: ClaimType
    source_branch: str
    source_paper: str
    raw_id: str
    reasons: tuple[PromotionBlockedReason, ...]

    @property
    def source_ref(self) -> str:
        return f"{self.source_branch}:{self.artifact_id}"


@dataclass(frozen=True)
class RawIdQuarantineRecord:
    filename: str
    source_paper: str
    raw_id: str
    seq: int
    synthetic_id: str
    message: str

    @property
    def detail_json(self) -> str:
        return json.dumps(
            {
                "synthetic_id_basis": {
                    "scheme": "sha256(filename|raw_id|seq)",
                    "filename": self.filename,
                    "raw_id": self.raw_id,
                    "seq": self.seq,
                    "prefix": "quarantine:raw_id:",
                },
            },
            sort_keys=True,
        )
