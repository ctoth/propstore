"""Claim semantic stage objects."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields
from enum import StrEnum
from typing import Any

from ast_equiv import canonical_dump

from propstore.claims import LoadedClaimsFile
from propstore.compiler.context import CompilationContext
from propstore.compiler.ir import ClaimCompilationBundle
from propstore.families.claims.types import ClaimType
from propstore.core.id_types import ConceptId
from propstore.families.claims.documents import VariableBindingDocument

class ClaimStage(StrEnum):
    AUTHORED = "claim.authored"
    CHECKED = "claim.checked"


@dataclass(frozen=True)
class ClaimAlgorithmVariable:
    name: str | None = field(default=None, metadata={"payload": "name"})
    symbol: str | None = field(default=None, metadata={"payload": "symbol"})
    concept_id: ConceptId | None = field(
        default=None,
        metadata={"payload": "concept"},
    )
    role: str | None = field(default=None, metadata={"payload": "role"})
    attributes: Mapping[str, Any] = field(default_factory=dict, metadata={"payload_rest": True})

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))


def claim_algorithm_variable_payload(
    variable: ClaimAlgorithmVariable,
) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for variable_field in fields(ClaimAlgorithmVariable):
        if variable_field.metadata.get("payload_rest") is True:
            data.update(getattr(variable, variable_field.name))
            continue
        payload_name = variable_field.metadata.get("payload")
        if not isinstance(payload_name, str):
            continue
        value = getattr(variable, variable_field.name)
        if value is not None:
            data[payload_name] = value
    return data


def parse_claim_algorithm_variable_entry(
    entry: Mapping[object, object],
) -> ClaimAlgorithmVariable:
    values: dict[str, str] = {}
    consumed_payload_keys: set[str] = set()

    for variable_field in fields(ClaimAlgorithmVariable):
        payload_name = variable_field.metadata.get("payload")
        if not isinstance(payload_name, str):
            continue
        consumed_payload_keys.add(payload_name)
        value = entry.get(payload_name)
        if value is None:
            continue
        if not isinstance(value, str):
            raise TypeError(
                f"algorithm variable field {payload_name!r} must be a string"
            )
        values[variable_field.name] = value

    return ClaimAlgorithmVariable(
        name=values.get("name"),
        symbol=values.get("symbol"),
        concept_id=(
            None
            if values.get("concept_id") is None
            else ConceptId(values["concept_id"])
        ),
        role=values.get("role"),
        attributes={
            key: value
            for key, value in entry.items()
            if isinstance(key, str)
            and key not in consumed_payload_keys
            and value is not None
        },
    )


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
        raise ValueError("algorithm claim variables must be a list of variable bindings")
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
class ClaimAuthoredFiles:
    claim_files: tuple[LoadedClaimsFile, ...]
    context: CompilationContext
    context_ids: frozenset[str] | None = None

    @classmethod
    def from_sequence(
        cls,
        claim_files: Sequence[LoadedClaimsFile],
        context: CompilationContext,
        *,
        context_ids: set[str] | None = None,
    ) -> "ClaimAuthoredFiles":
        return cls(
            claim_files=tuple(claim_files),
            context=context,
            context_ids=None if context_ids is None else frozenset(context_ids),
        )


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
