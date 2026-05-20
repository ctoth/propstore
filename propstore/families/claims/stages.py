"""Claim semantic stage objects."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import Field, dataclass, field, fields
from enum import StrEnum
from typing import TYPE_CHECKING, Any, cast

from propstore.claims import ClaimFileEntry
from propstore.compiler.context import CompilationContext
from propstore.compiler.ir import ClaimCompilationBundle
from propstore.core.id_types import ConceptId, to_concept_id

if TYPE_CHECKING:
    from quire.projections import ProjectionRow
    from propstore.families.diagnostics.declaration import QuarantineDiagnostic


class ClaimStage(StrEnum):
    AUTHORED = "claim.authored"
    CHECKED = "claim.checked"


@dataclass(frozen=True)
class ClaimAlgorithmVariable:
    name: str | None = field(default=None, metadata={"payload": "name", "coerce": "str"})
    symbol: str | None = field(default=None, metadata={"payload": "symbol", "coerce": "str"})
    concept_id: ConceptId | None = field(
        default=None,
        metadata={"payload": "concept", "coerce": "concept_id"},
    )
    role: str | None = field(default=None, metadata={"payload": "role", "coerce": "str"})
    attributes: Mapping[str, Any] = field(default_factory=dict, metadata={"payload_rest": True})

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))
        if self.concept_id is not None:
            object.__setattr__(self, "concept_id", to_concept_id(self.concept_id))


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


def _claim_algorithm_variable_kwargs(
    entry: Mapping[object, object],
) -> dict[str, object]:
    kwargs: dict[str, object] = {}
    consumed_payload_keys: set[str] = set()
    rest_field: Field[Any] | None = None

    for variable_field in fields(ClaimAlgorithmVariable):
        payload_name = variable_field.metadata.get("payload")
        if variable_field.metadata.get("payload_rest") is True:
            rest_field = variable_field
        if not isinstance(payload_name, str):
            continue
        consumed_payload_keys.add(payload_name)
        value = entry.get(payload_name)
        if value is None:
            continue
        if variable_field.metadata.get("coerce") == "concept_id":
            kwargs[variable_field.name] = to_concept_id(value)
        elif variable_field.metadata.get("coerce") == "str":
            kwargs[variable_field.name] = str(value)
        else:
            kwargs[variable_field.name] = value

    if rest_field is not None:
        kwargs[rest_field.name] = {
            str(key): value
            for key, value in entry.items()
            if key not in consumed_payload_keys and value is not None
        }
    return kwargs


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
            variables.append(
                ClaimAlgorithmVariable(
                    **cast(Any, _claim_algorithm_variable_kwargs(entry))
                )
            )
        return tuple(variables)
    return ()


@dataclass(frozen=True)
class ClaimAuthoredFiles:
    claim_files: tuple[ClaimFileEntry, ...]
    context: CompilationContext
    context_ids: frozenset[str] | None = None

    @classmethod
    def from_sequence(
        cls,
        claim_files: Sequence[ClaimFileEntry],
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
class ClaimSidecarRows:
    claim_core_rows: tuple["ProjectionRow", ...]
    numeric_payload_rows: tuple["ProjectionRow", ...]
    text_payload_rows: tuple["ProjectionRow", ...]
    algorithm_payload_rows: tuple["ProjectionRow", ...]
    claim_link_rows: tuple["ProjectionRow", ...]
    stance_rows: tuple["ProjectionRow", ...]
    quarantine_diagnostics: tuple["QuarantineDiagnostic", ...]


@dataclass(frozen=True)
class RawIdQuarantineSidecarRows:
    claim_rows: tuple["ProjectionRow", ...]
    diagnostic_rows: tuple[object, ...]


@dataclass(frozen=True)
class PromotionBlockedReason:
    kind: str
    detail: str


@dataclass(frozen=True)
class PromotionBlockedClaimFact:
    artifact_id: str
    source_branch: str
    source_paper: str
    raw_id: str
    reasons: tuple[PromotionBlockedReason, ...]

    @property
    def source_ref(self) -> str:
        return f"{self.source_branch}:{self.artifact_id}"


@dataclass(frozen=True)
class PromotionBlockedSidecarRows:
    claim_rows: tuple["ProjectionRow", ...]
    diagnostic_rows: tuple[object, ...]


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
