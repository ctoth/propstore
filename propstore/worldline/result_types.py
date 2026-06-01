from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, cast

from propstore.world.types import (
    ATMSFutureStatusReport,
    ATMSNodeFutureStatusEntry,
    ATMSNodeRelevanceReport,
    ATMSNodeStabilityReport,
    ATMSNogoodDetail,
    ATMSWhyOutReport,
)

WorldlineScalarValue = float | str | None


def _worldline_scalar_value(value: object, *, field: str) -> WorldlineScalarValue:
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a string or number")
    if isinstance(value, (int, float)):
        return value
    raise ValueError(f"{field} must be a string or number")


def _optional_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return value


def _nested_mapping_items(value: Any, *, field: str) -> dict[str, Mapping[str, Any]]:
    raw = _optional_mapping(value, field=field)
    items: dict[str, Mapping[str, Any]] = {}
    for name, item in raw.items():
        if not isinstance(item, Mapping):
            raise ValueError(f"{field}.{name} must be a mapping")
        items[str(name)] = item
    return items


def _json_native(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_native(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_native(item) for item in value]
    if not isinstance(value, type) and is_dataclass(value):
        return _json_native(asdict(cast(Any, value)))
    return value


class WorldlineCaptureError(Enum):
    ARGUMENTATION = "argumentation"
    REVISION = "revision"
    SENSITIVITY = "sensitivity"


@dataclass(frozen=True)
class WorldlineVariableRef:
    name: str | None = None
    symbol: str | None = None
    concept_id: str | None = None
    value: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.name is not None:
            data["name"] = self.name
        if self.symbol is not None:
            data["symbol"] = self.symbol
        if self.concept_id is not None:
            data["concept_id"] = self.concept_id
        if self.value is not None:
            data["value"] = self.value
        return data


@dataclass(frozen=True)
class WorldlineInputSource:
    source: str
    value: WorldlineScalarValue = None
    claim_id: str | None = None
    formula: str | None = None
    reason: str | None = None
    strategy: str | None = None
    inputs_used: Mapping[str, WorldlineInputSource] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs_used", dict(self.inputs_used))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"source": self.source}
        if self.value is not None:
            data["value"] = self.value
        if self.claim_id is not None:
            data["claim_id"] = self.claim_id
        if self.formula is not None:
            data["formula"] = self.formula
        if self.reason is not None:
            data["reason"] = self.reason
        if self.strategy is not None:
            data["strategy"] = self.strategy
        if self.inputs_used:
            data["inputs_used"] = {
                name: input_source.to_dict()
                for name, input_source in self.inputs_used.items()
            }
        return data


@dataclass(frozen=True)
class WorldlineTargetValue:
    status: str
    value: WorldlineScalarValue = None
    source: str | None = None
    reason: str | None = None
    claim_id: str | None = None
    winning_claim_id: str | None = None
    claim_type: str | None = None
    statement: str | None = None
    expression: str | None = None
    body: str | None = None
    name: str | None = None
    canonical_ast: str | None = None
    variables: tuple[WorldlineVariableRef, ...] = ()
    formula: str | None = None
    strategy: str | None = None
    inputs_used: Mapping[str, WorldlineInputSource] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "inputs_used", dict(self.inputs_used))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"status": self.status}
        if self.value is not None:
            data["value"] = self.value
        if self.source is not None:
            data["source"] = self.source
        if self.reason is not None:
            data["reason"] = self.reason
        if self.claim_id is not None:
            data["claim_id"] = self.claim_id
        if self.winning_claim_id is not None:
            data["winning_claim_id"] = self.winning_claim_id
        if self.claim_type is not None:
            data["claim_type"] = self.claim_type
        if self.statement is not None:
            data["statement"] = self.statement
        if self.expression is not None:
            data["expression"] = self.expression
        if self.body is not None:
            data["body"] = self.body
        if self.name is not None:
            data["name"] = self.name
        if self.canonical_ast is not None:
            data["canonical_ast"] = self.canonical_ast
        if self.variables:
            data["variables"] = [variable.to_dict() for variable in self.variables]
        if self.formula is not None:
            data["formula"] = self.formula
        if self.strategy is not None:
            data["strategy"] = self.strategy
        if self.inputs_used:
            data["inputs_used"] = {
                name: input_source.to_dict()
                for name, input_source in self.inputs_used.items()
            }
        return data


@dataclass(frozen=True)
class WorldlineStep:
    concept: str
    source: str
    value: WorldlineScalarValue = None
    claim_id: str | None = None
    strategy: str | None = None
    reason: str | None = None
    formula: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "concept": self.concept,
            "source": self.source,
        }
        if self.value is not None:
            data["value"] = self.value
        if self.claim_id is not None:
            data["claim_id"] = self.claim_id
        if self.strategy is not None:
            data["strategy"] = self.strategy
        if self.reason is not None:
            data["reason"] = self.reason
        if self.formula is not None:
            data["formula"] = self.formula
        return data


@dataclass(frozen=True)
class WorldlineDependencies:
    claims: tuple[str, ...] = ()
    stances: tuple[str, ...] = ()
    contexts: tuple[str, ...] = ()
    lifting_rules: tuple[str, ...] = ()
    blocked_exceptions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = {
            "claims": list(self.claims),
            "stances": list(self.stances),
            "contexts": list(self.contexts),
        }
        if self.lifting_rules:
            data["lifting_rules"] = list(self.lifting_rules)
        if self.blocked_exceptions:
            data["blocked_exceptions"] = list(self.blocked_exceptions)
        return data


@dataclass(frozen=True)
class WorldlineSensitivityEntry:
    input_name: str
    elasticity: float | None = None
    partial_derivative: float | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"input": self.input_name}
        if self.elasticity is not None:
            data["elasticity"] = self.elasticity
        if self.partial_derivative is not None:
            data["partial_derivative"] = self.partial_derivative
        return data


@dataclass(frozen=True)
class WorldlineSensitivityOutcome:
    entries: tuple[WorldlineSensitivityEntry, ...] = ()
    error: WorldlineCaptureError | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))
        if self.error is not None and not isinstance(self.error, WorldlineCaptureError):
            raise TypeError(
                "WorldlineSensitivityOutcome.error must be a WorldlineCaptureError"
            )

    @classmethod
    def from_value(cls, data: Any) -> WorldlineSensitivityOutcome:
        if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
            return cls(
                entries=tuple(
                    WorldlineSensitivityEntry.from_json_payload(item)
                    for item in data
                    if isinstance(item, Mapping)
                )
            )
        if isinstance(data, Mapping):
            return cls(
                error=(
                    None
                    if data.get("error") is None
                    else WorldlineCaptureError(str(data["error"]))
                )
            )
        return cls()

    def to_dict(self) -> list[dict[str, Any]] | dict[str, Any]:
        if self.error is not None:
            return {"error": self.error.value}
        return [entry.to_dict() for entry in self.entries]


@dataclass(frozen=True)
class WorldlineSensitivityReport:
    targets: Mapping[str, WorldlineSensitivityOutcome] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "targets", dict(self.targets))

    def to_dict(self) -> dict[str, Any]:
        return {
            target_name: outcome.to_dict()
            for target_name, outcome in self.targets.items()
        }


@dataclass(frozen=True)
class WorldlineArgumentationState:
    backend: str | None = None
    status: str | None = None
    error: WorldlineCaptureError | None = None
    justified: tuple[str, ...] = ()
    defeated: tuple[str, ...] = ()
    extensions: tuple[tuple[str, ...], ...] = ()
    inference_mode: str | None = None
    acceptance_probs: Mapping[str, float] = field(default_factory=dict)
    strategy_used: str | None = None
    samples: int | None = None
    confidence_interval_half: float | None = None
    semantics: str | None = None
    supported: tuple[str, ...] = ()
    nogoods: tuple[tuple[str, ...], ...] = ()
    node_statuses: Mapping[str, str] = field(default_factory=dict)
    support_quality: Mapping[str, str] = field(default_factory=dict)
    essential_support: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    status_reasons: Mapping[str, str | None] = field(default_factory=dict)
    nogood_details: tuple[ATMSNogoodDetail, ...] = ()
    declared_queryables: tuple[str, ...] = ()
    future_statuses: Mapping[str, ATMSFutureStatusReport] = field(default_factory=dict)
    stability: Mapping[str, ATMSNodeStabilityReport] = field(default_factory=dict)
    relevance: Mapping[str, ATMSNodeRelevanceReport] = field(default_factory=dict)
    witness_futures: Mapping[str, tuple[ATMSNodeFutureStatusEntry, ...]] = field(
        default_factory=dict
    )
    why_out: Mapping[str, ATMSWhyOutReport] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.error is not None and not isinstance(self.error, WorldlineCaptureError):
            raise TypeError(
                "WorldlineArgumentationState.error must be a WorldlineCaptureError"
            )
        object.__setattr__(self, "justified", tuple(self.justified))
        object.__setattr__(self, "defeated", tuple(self.defeated))
        object.__setattr__(
            self,
            "extensions",
            tuple(
                tuple(str(item) for item in extension) for extension in self.extensions
            ),
        )
        object.__setattr__(self, "acceptance_probs", dict(self.acceptance_probs))
        object.__setattr__(self, "supported", tuple(self.supported))
        object.__setattr__(
            self,
            "nogoods",
            tuple(tuple(str(item) for item in entry) for entry in self.nogoods),
        )
        object.__setattr__(self, "node_statuses", dict(self.node_statuses))
        object.__setattr__(self, "support_quality", dict(self.support_quality))
        object.__setattr__(
            self,
            "essential_support",
            {
                str(claim_id): tuple(str(item) for item in support)
                for claim_id, support in self.essential_support.items()
            },
        )
        object.__setattr__(self, "status_reasons", dict(self.status_reasons))
        object.__setattr__(self, "nogood_details", tuple(self.nogood_details))
        object.__setattr__(self, "declared_queryables", tuple(self.declared_queryables))
        object.__setattr__(self, "future_statuses", dict(self.future_statuses))
        object.__setattr__(self, "stability", dict(self.stability))
        object.__setattr__(self, "relevance", dict(self.relevance))
        object.__setattr__(
            self,
            "witness_futures",
            {
                str(claim_id): tuple(entries)
                for claim_id, entries in self.witness_futures.items()
            },
        )
        object.__setattr__(self, "why_out", dict(self.why_out))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.backend is not None:
            data["backend"] = self.backend
        if self.status is not None:
            data["status"] = self.status
        if self.error is not None:
            data["error"] = self.error.value
        if self.justified:
            data["justified"] = list(self.justified)
        if self.defeated:
            data["defeated"] = list(self.defeated)
        if self.extensions:
            data["extensions"] = [list(extension) for extension in self.extensions]
        if self.inference_mode is not None:
            data["inference_mode"] = self.inference_mode
        if self.acceptance_probs:
            data["acceptance_probs"] = dict(self.acceptance_probs)
        if self.strategy_used is not None:
            data["strategy_used"] = self.strategy_used
        if self.samples is not None:
            data["samples"] = self.samples
        if self.confidence_interval_half is not None:
            data["confidence_interval_half"] = self.confidence_interval_half
        if self.semantics is not None:
            data["semantics"] = self.semantics
        if self.supported:
            data["supported"] = list(self.supported)
        if self.nogoods:
            data["nogoods"] = [list(entry) for entry in self.nogoods]
        if self.node_statuses:
            data["node_statuses"] = dict(self.node_statuses)
        if self.support_quality:
            data["support_quality"] = dict(self.support_quality)
        if self.essential_support:
            data["essential_support"] = {
                claim_id: list(support)
                for claim_id, support in self.essential_support.items()
            }
        if self.status_reasons:
            data["status_reasons"] = dict(self.status_reasons)
        if self.nogood_details:
            data["nogood_details"] = _json_native(self.nogood_details)
        if self.declared_queryables:
            data["declared_queryables"] = list(self.declared_queryables)
        if self.future_statuses:
            data["future_statuses"] = _json_native(self.future_statuses)
        if self.stability:
            data["stability"] = _json_native(self.stability)
        if self.relevance:
            data["relevance"] = _json_native(self.relevance)
        if self.witness_futures:
            data["witness_futures"] = _json_native(self.witness_futures)
        if self.why_out:
            data["why_out"] = _json_native(self.why_out)
        return data
