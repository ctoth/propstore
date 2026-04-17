from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from propstore.world.types import (
    ATMSFutureStatusReport,
    ATMSNodeFutureStatusEntry,
    ATMSNodeRelevanceReport,
    ATMSNodeStabilityReport,
    ATMSNogoodDetail,
    ATMSWhyOutReport,
)


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


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


@dataclass(frozen=True)
class WorldlineVariableRef:
    name: str | None = None
    symbol: str | None = None
    concept_id: str | None = None
    value: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> WorldlineVariableRef:
        return cls(
            name=None if data.get("name") is None else str(data.get("name")),
            symbol=None if data.get("symbol") is None else str(data.get("symbol")),
            concept_id=(
                None
                if data.get("concept_id") is None and data.get("concept") is None
                else str(data.get("concept_id") or data.get("concept"))
            ),
            value=None if data.get("value") is None else str(data.get("value")),
        )

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
    value: float | str | None = None
    claim_id: str | None = None
    formula: str | None = None
    reason: str | None = None
    strategy: str | None = None
    inputs_used: Mapping[str, WorldlineInputSource] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs_used", dict(self.inputs_used))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> WorldlineInputSource:
        return cls(
            source=str(data.get("source") or "unknown"),
            value=data.get("value"),
            claim_id=None if data.get("claim_id") is None else str(data.get("claim_id")),
            formula=None if data.get("formula") is None else str(data.get("formula")),
            reason=None if data.get("reason") is None else str(data.get("reason")),
            strategy=None if data.get("strategy") is None else str(data.get("strategy")),
            inputs_used={
                name: WorldlineInputSource.from_mapping(value)
                for name, value in _nested_mapping_items(
                    data.get("inputs_used"),
                    field="inputs_used",
                ).items()
            },
        )

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


def _coerce_variable_refs(
    raw_variables: Any,
) -> tuple[WorldlineVariableRef, ...]:
    if isinstance(raw_variables, Sequence) and not isinstance(raw_variables, (str, bytes)):
        refs: list[WorldlineVariableRef] = []
        for index, item in enumerate(raw_variables):
            if not isinstance(item, Mapping):
                raise ValueError(f"worldline variables[{index}] must be a mapping")
            refs.append(WorldlineVariableRef.from_mapping(item))
        return tuple(refs)
    if isinstance(raw_variables, Mapping):
        raise ValueError("worldline variables must be a list of variable bindings")
    return ()


@dataclass(frozen=True)
class WorldlineTargetValue:
    status: str
    value: float | str | None = None
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

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> WorldlineTargetValue:
        variables = _coerce_variable_refs(data.get("variables"))
        inputs_used = {
            name: WorldlineInputSource.from_mapping(value)
            for name, value in _nested_mapping_items(
                data.get("inputs_used"),
                field="inputs_used",
            ).items()
        }
        return cls(
            status=str(data.get("status") or "underspecified"),
            value=data.get("value"),
            source=None if data.get("source") is None else str(data.get("source")),
            reason=None if data.get("reason") is None else str(data.get("reason")),
            claim_id=None if data.get("claim_id") is None else str(data.get("claim_id")),
            winning_claim_id=(
                None
                if data.get("winning_claim_id") is None
                else str(data.get("winning_claim_id"))
            ),
            claim_type=None if data.get("claim_type") is None else str(data.get("claim_type")),
            statement=None if data.get("statement") is None else str(data.get("statement")),
            expression=None if data.get("expression") is None else str(data.get("expression")),
            body=None if data.get("body") is None else str(data.get("body")),
            name=None if data.get("name") is None else str(data.get("name")),
            canonical_ast=(
                None if data.get("canonical_ast") is None else str(data.get("canonical_ast"))
            ),
            variables=variables,
            formula=None if data.get("formula") is None else str(data.get("formula")),
            strategy=None if data.get("strategy") is None else str(data.get("strategy")),
            inputs_used=inputs_used,
        )

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


WorldlineTargetValueInput = WorldlineTargetValue | Mapping[str, Any]


def coerce_worldline_target_value(value: WorldlineTargetValueInput) -> WorldlineTargetValue:
    if isinstance(value, WorldlineTargetValue):
        return value
    return WorldlineTargetValue.from_mapping(value)


@dataclass(frozen=True)
class WorldlineStep:
    concept: str
    source: str
    value: float | str | None = None
    claim_id: str | None = None
    strategy: str | None = None
    reason: str | None = None
    formula: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> WorldlineStep:
        return cls(
            concept=str(data.get("concept") or ""),
            source=str(data.get("source") or "unknown"),
            value=data.get("value"),
            claim_id=None if data.get("claim_id") is None else str(data.get("claim_id")),
            strategy=None if data.get("strategy") is None else str(data.get("strategy")),
            reason=None if data.get("reason") is None else str(data.get("reason")),
            formula=None if data.get("formula") is None else str(data.get("formula")),
        )

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


WorldlineStepInput = WorldlineStep | Mapping[str, Any]


def coerce_worldline_step(step: WorldlineStepInput) -> WorldlineStep:
    if isinstance(step, WorldlineStep):
        return step
    return WorldlineStep.from_mapping(step)


@dataclass(frozen=True)
class WorldlineDependencies:
    claims: tuple[str, ...] = ()
    stances: tuple[str, ...] = ()
    contexts: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> WorldlineDependencies:
        payload = {} if data is None else dict(data)
        return cls(
            claims=tuple(str(item) for item in payload.get("claims") or ()),
            stances=tuple(str(item) for item in payload.get("stances") or ()),
            contexts=tuple(str(item) for item in payload.get("contexts") or ()),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "claims": list(self.claims),
            "stances": list(self.stances),
            "contexts": list(self.contexts),
        }


@dataclass(frozen=True)
class WorldlineSensitivityEntry:
    input_name: str
    elasticity: float | None = None
    partial_derivative: float | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> WorldlineSensitivityEntry:
        return cls(
            input_name=str(data.get("input") or ""),
            elasticity=_optional_float(data.get("elasticity")),
            partial_derivative=_optional_float(data.get("partial_derivative")),
        )

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
    error: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))

    @classmethod
    def from_value(cls, data: Any) -> WorldlineSensitivityOutcome:
        if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
            return cls(
                entries=tuple(
                    WorldlineSensitivityEntry.from_mapping(item)
                    for item in data
                    if isinstance(item, Mapping)
                )
            )
        if isinstance(data, Mapping):
            return cls(
                error=None if data.get("error") is None else str(data.get("error"))
            )
        return cls()

    def to_dict(self) -> list[dict[str, Any]] | dict[str, Any]:
        if self.error is not None:
            return {"error": self.error}
        return [entry.to_dict() for entry in self.entries]


@dataclass(frozen=True)
class WorldlineSensitivityReport:
    targets: Mapping[str, WorldlineSensitivityOutcome] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "targets", dict(self.targets))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> WorldlineSensitivityReport | None:
        if not data:
            return None
        return cls(
            targets={
                str(target_name): WorldlineSensitivityOutcome.from_value(value)
                for target_name, value in data.items()
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            target_name: outcome.to_dict()
            for target_name, outcome in self.targets.items()
        }


@dataclass(frozen=True)
class WorldlineArgumentationState:
    backend: str | None = None
    status: str | None = None
    error: str | None = None
    justified: tuple[str, ...] = ()
    defeated: tuple[str, ...] = ()
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
    witness_futures: Mapping[str, tuple[ATMSNodeFutureStatusEntry, ...]] = field(default_factory=dict)
    why_out: Mapping[str, ATMSWhyOutReport] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "justified", tuple(self.justified))
        object.__setattr__(self, "defeated", tuple(self.defeated))
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

    @classmethod
    def from_mapping(cls, data: object) -> WorldlineArgumentationState | None:
        if data is None:
            return None
        if not isinstance(data, Mapping):
            raise ValueError("worldline argumentation must be a mapping")
        if not data:
            return None
        raw_nogoods = data.get("nogoods") or ()
        acceptance_probs = _optional_mapping(
            data.get("acceptance_probs"),
            field="acceptance_probs",
        )
        node_statuses = _optional_mapping(data.get("node_statuses"), field="node_statuses")
        support_quality = _optional_mapping(
            data.get("support_quality"),
            field="support_quality",
        )
        essential_support = _optional_mapping(
            data.get("essential_support"),
            field="essential_support",
        )
        status_reasons = _optional_mapping(data.get("status_reasons"), field="status_reasons")
        future_statuses = _optional_mapping(
            data.get("future_statuses"),
            field="future_statuses",
        )
        stability = _optional_mapping(data.get("stability"), field="stability")
        relevance = _optional_mapping(data.get("relevance"), field="relevance")
        witness_futures = _optional_mapping(
            data.get("witness_futures"),
            field="witness_futures",
        )
        why_out = _optional_mapping(data.get("why_out"), field="why_out")
        return cls(
            backend=None if data.get("backend") is None else str(data.get("backend")),
            status=None if data.get("status") is None else str(data.get("status")),
            error=None if data.get("error") is None else str(data.get("error")),
            justified=tuple(str(item) for item in data.get("justified") or ()),
            defeated=tuple(str(item) for item in data.get("defeated") or ()),
            acceptance_probs={
                str(claim_id): float(value)
                for claim_id, value in acceptance_probs.items()
            },
            strategy_used=(
                None if data.get("strategy_used") is None else str(data.get("strategy_used"))
            ),
            samples=_optional_int(data.get("samples")),
            confidence_interval_half=_optional_float(data.get("confidence_interval_half")),
            semantics=None if data.get("semantics") is None else str(data.get("semantics")),
            supported=tuple(str(item) for item in data.get("supported") or ()),
            nogoods=tuple(
                tuple(str(item) for item in entry)
                for entry in raw_nogoods
                if isinstance(entry, Sequence) and not isinstance(entry, (str, bytes))
            ),
            node_statuses={
                str(node_id): str(status)
                for node_id, status in node_statuses.items()
            },
            support_quality={
                str(claim_id): str(status)
                for claim_id, status in support_quality.items()
            },
            essential_support={
                str(claim_id): tuple(str(item) for item in support)
                for claim_id, support in essential_support.items()
            },
            status_reasons={
                str(claim_id): None if reason is None else str(reason)
                for claim_id, reason in status_reasons.items()
            },
            nogood_details=tuple(data.get("nogood_details") or ()),
            declared_queryables=tuple(str(item) for item in data.get("declared_queryables") or ()),
            future_statuses=dict(future_statuses),
            stability=dict(stability),
            relevance=dict(relevance),
            witness_futures={
                str(claim_id): tuple(entries)
                for claim_id, entries in witness_futures.items()
            },
            why_out=dict(why_out),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.backend is not None:
            data["backend"] = self.backend
        if self.status is not None:
            data["status"] = self.status
        if self.error is not None:
            data["error"] = self.error
        if self.justified:
            data["justified"] = list(self.justified)
        if self.defeated:
            data["defeated"] = list(self.defeated)
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
            data["nogood_details"] = list(self.nogood_details)
        if self.declared_queryables:
            data["declared_queryables"] = list(self.declared_queryables)
        if self.future_statuses:
            data["future_statuses"] = dict(self.future_statuses)
        if self.stability:
            data["stability"] = dict(self.stability)
        if self.relevance:
            data["relevance"] = dict(self.relevance)
        if self.witness_futures:
            data["witness_futures"] = {
                claim_id: list(entries)
                for claim_id, entries in self.witness_futures.items()
            }
        if self.why_out:
            data["why_out"] = dict(self.why_out)
        return data
