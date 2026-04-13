"""Worldline definitions and materialized results."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import msgspec

from propstore.document_schema import (
    DocumentStruct,
    convert_document_value,
    decode_document_path,
)
from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path
from propstore.world.types import Environment, RenderPolicy
from propstore.worldline.result_types import (
    WorldlineArgumentationState,
    WorldlineDependencies,
    WorldlineSensitivityReport,
    WorldlineStep,
    WorldlineTargetValue,
    coerce_worldline_step,
    coerce_worldline_target_value,
)
from propstore.worldline.revision_types import (
    RevisionAtomRef,
    RevisionConflictSelection,
    WorldlineRevisionState,
)


class WorldlineAssumptionDocument(DocumentStruct):
    assumption_id: str
    kind: str
    source: str
    cel: str


class WorldlineInputsDocument(DocumentStruct):
    bindings: dict[str, Any] = msgspec.field(default_factory=dict)
    context_id: str | None = None
    effective_assumptions: tuple[str, ...] = ()
    assumptions: tuple[WorldlineAssumptionDocument, ...] = ()
    overrides: dict[str, float | str] = msgspec.field(default_factory=dict)


class WorldlinePolicyDocument(DocumentStruct):
    reasoning_backend: str | None = None
    strategy: str | None = None
    semantics: str | None = None
    comparison: str | None = None
    link: str | None = None
    decision_criterion: str | None = None
    pessimism_index: float | None = None
    show_uncertainty_interval: bool | None = None
    praf_strategy: str | None = None
    praf_mc_epsilon: float | None = None
    praf_mc_confidence: float | None = None
    praf_treewidth_cutoff: int | None = None
    praf_mc_seed: int | None = None
    merge_operator: str | None = None
    branch_filter: tuple[str, ...] | None = None
    branch_weights: dict[str, float] | None = None
    integrity_constraints: tuple[dict[str, Any], ...] = ()
    future_queryables: tuple[str, ...] = ()
    future_limit: int | None = None
    overrides: dict[str, str] = msgspec.field(default_factory=dict)
    concept_strategies: dict[str, str] = msgspec.field(default_factory=dict)


class WorldlineVariableRefDocument(DocumentStruct):
    name: str | None = None
    symbol: str | None = None
    concept_id: str | None = None
    value: str | None = None


class WorldlineInputSourceDocument(DocumentStruct):
    source: str
    value: float | str | None = None
    claim_id: str | None = None
    formula: str | None = None
    reason: str | None = None
    strategy: str | None = None
    inputs_used: dict[str, WorldlineInputSourceDocument] = msgspec.field(default_factory=dict)


class WorldlineTargetValueDocument(DocumentStruct):
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
    variables: tuple[WorldlineVariableRefDocument, ...] | dict[str, str] = ()
    formula: str | None = None
    strategy: str | None = None
    inputs_used: dict[str, WorldlineInputSourceDocument] = msgspec.field(default_factory=dict)


class WorldlineStepDocument(DocumentStruct):
    concept: str
    source: str
    value: float | str | None = None
    claim_id: str | None = None
    strategy: str | None = None
    reason: str | None = None
    formula: str | None = None


class WorldlineDependenciesDocument(DocumentStruct):
    claims: tuple[str, ...] = ()
    stances: tuple[str, ...] = ()
    contexts: tuple[str, ...] = ()


class WorldlineRevisionAtomDocument(DocumentStruct):
    kind: str = "claim"
    id: str | None = None
    atom_id: str | None = None
    value: float | str | None = None


class WorldlineRevisionQueryDocument(DocumentStruct):
    operation: str
    atom: WorldlineRevisionAtomDocument | None = None
    target: str | None = None
    conflicts: dict[str, tuple[str, ...]] = msgspec.field(default_factory=dict)
    operator: str | None = None


class WorldlineRevisionResultDocument(DocumentStruct):
    accepted_atom_ids: tuple[str, ...] = ()
    rejected_atom_ids: tuple[str, ...] = ()
    incision_set: tuple[str, ...] = ()
    explanation: dict[str, Any] | None = None


class WorldlineRevisionStateDocument(DocumentStruct):
    operation: str
    input_atom_id: str | None = None
    target_atom_ids: tuple[str, ...] = ()
    result: WorldlineRevisionResultDocument | None = None
    state: dict[str, Any] | None = None
    status: str | None = None
    error: str | None = None


class WorldlineResultDocument(DocumentStruct):
    computed: str
    content_hash: str
    values: dict[str, WorldlineTargetValueDocument]
    dependencies: WorldlineDependenciesDocument
    steps: tuple[WorldlineStepDocument, ...] = ()
    sensitivity: dict[str, Any] | None = None
    argumentation: dict[str, Any] | None = None
    revision: WorldlineRevisionStateDocument | None = None


class WorldlineDefinitionDocument(DocumentStruct):
    id: str
    targets: tuple[str, ...]
    name: str = ""
    created: str = ""
    inputs: WorldlineInputsDocument | None = None
    policy: WorldlinePolicyDocument | None = None
    revision: WorldlineRevisionQueryDocument | None = None
    results: WorldlineResultDocument | None = None


@dataclass
class WorldlineInputs:
    """The input specification for a worldline query."""

    environment: Environment = field(default_factory=Environment)
    overrides: dict[str, float | str] = field(default_factory=dict)

    @classmethod
    def from_document(cls, data: WorldlineInputsDocument | None) -> WorldlineInputs:
        if data is None:
            return cls()
        environment_payload = {
            "bindings": dict(data.bindings),
            "context_id": data.context_id,
            "effective_assumptions": list(data.effective_assumptions),
            "assumptions": [
                {
                    "assumption_id": item.assumption_id,
                    "kind": item.kind,
                    "source": item.source,
                    "cel": item.cel,
                }
                for item in data.assumptions
            ],
        }
        return cls(
            environment=Environment.from_dict(environment_payload),
            overrides=dict(data.overrides),
        )

    @classmethod
    def from_dict(cls, data: dict | None) -> WorldlineInputs:
        if not data:
            return cls()
        return cls(
            environment=Environment.from_dict(data),
            overrides=dict(data.get("overrides") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        data = self.environment.to_dict()
        if self.overrides:
            data["overrides"] = dict(self.overrides)
        return data


@dataclass
class WorldlineRevisionQuery:
    operation: str = ""
    atom: RevisionAtomRef | None = None
    target: str | None = None
    conflicts: RevisionConflictSelection = field(default_factory=RevisionConflictSelection)
    operator: str | None = None

    @classmethod
    def from_document(
        cls,
        data: WorldlineRevisionQueryDocument | None,
    ) -> WorldlineRevisionQuery | None:
        if data is None:
            return None
        atom = None
        if data.atom is not None:
            atom = RevisionAtomRef.from_mapping(
                {
                    "kind": data.atom.kind,
                    "id": data.atom.id,
                    "atom_id": data.atom.atom_id,
                    "value": data.atom.value,
                }
            )
        return cls(
            operation=data.operation,
            atom=atom,
            target=data.target,
            conflicts=RevisionConflictSelection(
                {
                    atom_id: tuple(target_ids)
                    for atom_id, target_ids in data.conflicts.items()
                }
            ),
            operator=data.operator,
        )

    @classmethod
    def from_dict(cls, data: dict | None) -> WorldlineRevisionQuery | None:
        if not data:
            return None
        return cls(
            operation=str(data.get("operation", "")),
            atom=RevisionAtomRef.from_mapping(data.get("atom")),
            target=data.get("target"),
            conflicts=RevisionConflictSelection.from_mapping(data.get("conflicts")),
            operator=data.get("operator"),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"operation": self.operation}
        if self.atom is not None:
            data["atom"] = self.atom.to_dict()
        if self.target is not None:
            data["target"] = self.target
        if self.conflicts.targets_by_atom_id:
            data["conflicts"] = self.conflicts.to_dict()
        if self.operator is not None:
            data["operator"] = self.operator
        return data


@dataclass
class WorldlineResult:
    """The materialized results of a worldline query."""

    computed: str = ""
    content_hash: str = ""
    values: dict[str, WorldlineTargetValue] = field(default_factory=dict)
    steps: tuple[WorldlineStep, ...] = ()
    dependencies: WorldlineDependencies = field(default_factory=WorldlineDependencies)
    sensitivity: WorldlineSensitivityReport | None = None
    argumentation: WorldlineArgumentationState | None = None
    revision: WorldlineRevisionState | None = None

    def __post_init__(self) -> None:
        self.values = {
            str(target_name): coerce_worldline_target_value(value)
            for target_name, value in self.values.items()
        }
        self.steps = tuple(coerce_worldline_step(step) for step in self.steps)
        if not isinstance(self.dependencies, WorldlineDependencies):
            self.dependencies = WorldlineDependencies.from_mapping(self.dependencies)
        if self.sensitivity is not None and not isinstance(self.sensitivity, WorldlineSensitivityReport):
            self.sensitivity = WorldlineSensitivityReport.from_mapping(self.sensitivity)
        if self.argumentation is not None and not isinstance(self.argumentation, WorldlineArgumentationState):
            self.argumentation = WorldlineArgumentationState.from_mapping(self.argumentation)
        if self.revision is not None and not isinstance(self.revision, WorldlineRevisionState):
            self.revision = WorldlineRevisionState.from_mapping(self.revision)

    @classmethod
    def from_document(cls, data: WorldlineResultDocument | None) -> WorldlineResult | None:
        if data is None:
            return None
        return cls(
            computed=data.computed,
            content_hash=data.content_hash,
            values={
                str(target_name): WorldlineTargetValue.from_mapping(
                    msgspec.to_builtins(value)
                )
                for target_name, value in data.values.items()
            },
            steps=tuple(
                WorldlineStep.from_mapping(msgspec.to_builtins(step))
                for step in data.steps
            ),
            dependencies=WorldlineDependencies.from_mapping(
                msgspec.to_builtins(data.dependencies)
            ),
            sensitivity=WorldlineSensitivityReport.from_mapping(data.sensitivity),
            argumentation=WorldlineArgumentationState.from_mapping(data.argumentation),
            revision=WorldlineRevisionState.from_mapping(
                None if data.revision is None else msgspec.to_builtins(data.revision)
            ),
        )

    @classmethod
    def from_dict(cls, data: dict | None) -> WorldlineResult | None:
        if not data:
            return None
        return cls(
            computed=data.get("computed", ""),
            content_hash=data.get("content_hash", ""),
            values={
                str(target_name): WorldlineTargetValue.from_mapping(value)
                for target_name, value in (data.get("values") or {}).items()
                if isinstance(value, dict)
            },
            steps=tuple(
                WorldlineStep.from_mapping(step)
                for step in (data.get("steps") or ())
                if isinstance(step, dict)
            ),
            dependencies=WorldlineDependencies.from_mapping(data.get("dependencies")),
            sensitivity=WorldlineSensitivityReport.from_mapping(data.get("sensitivity")),
            argumentation=WorldlineArgumentationState.from_mapping(data.get("argumentation")),
            revision=WorldlineRevisionState.from_mapping(
                data.get("revision") if isinstance(data.get("revision"), dict) else None
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "computed": self.computed,
            "content_hash": self.content_hash,
            "values": {
                target_name: target_value.to_dict()
                for target_name, target_value in self.values.items()
            },
            "steps": [step.to_dict() for step in self.steps],
            "dependencies": self.dependencies.to_dict(),
        }
        if self.sensitivity is not None:
            data["sensitivity"] = self.sensitivity.to_dict()
        if self.argumentation is not None:
            data["argumentation"] = self.argumentation.to_dict()
        if self.revision is not None:
            data["revision"] = self.revision.to_dict()
        return data


@dataclass
class WorldlineDefinition:
    """A worldline: question + optional answer."""

    id: str
    name: str = ""
    created: str = ""
    inputs: WorldlineInputs = field(default_factory=WorldlineInputs)
    policy: RenderPolicy = field(default_factory=RenderPolicy)
    targets: list[str] = field(default_factory=list)
    revision: WorldlineRevisionQuery | None = None
    results: WorldlineResult | None = None

    @classmethod
    def from_document(cls, data: WorldlineDefinitionDocument) -> WorldlineDefinition:
        if not data.targets:
            raise ValueError("Worldline definition requires 'targets'")

        policy_payload = None
        if data.policy is not None:
            raw_policy = msgspec.to_builtins(data.policy)
            policy_payload = {
                key: value
                for key, value in raw_policy.items()
                if value not in (None, (), {})
            }

        return cls(
            id=data.id,
            name=data.name,
            created=data.created,
            inputs=WorldlineInputs.from_document(data.inputs),
            policy=RenderPolicy.from_dict(policy_payload),
            targets=list(data.targets),
            revision=WorldlineRevisionQuery.from_document(data.revision),
            results=WorldlineResult.from_document(data.results),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorldlineDefinition:
        if "id" not in data:
            raise ValueError("Worldline definition requires 'id'")
        targets = data.get("targets")
        if not targets:
            raise ValueError("Worldline definition requires 'targets'")

        return cls(
            id=data["id"],
            name=data.get("name", ""),
            created=data.get("created", ""),
            inputs=WorldlineInputs.from_dict(data.get("inputs")),
            policy=RenderPolicy.from_dict(data.get("policy")),
            targets=list(targets),
            revision=WorldlineRevisionQuery.from_dict(data.get("revision")),
            results=WorldlineResult.from_dict(data.get("results")),
        )

    @classmethod
    def from_file(cls, path: Path | KnowledgePath) -> WorldlineDefinition:
        document = decode_document_path(
            coerce_knowledge_path(path),
            WorldlineDefinitionDocument,
        )
        return cls.from_document(document)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"id": self.id}
        if self.name:
            data["name"] = self.name
        if self.created:
            data["created"] = self.created

        inputs = self.inputs.to_dict()
        if inputs:
            data["inputs"] = inputs

        policy = self.policy.to_dict()
        if policy:
            data["policy"] = policy

        data["targets"] = list(self.targets)

        if self.revision is not None:
            data["revision"] = self.revision.to_dict()
        if self.results is not None:
            data["results"] = self.results.to_dict()
        return data

    def to_document(self) -> WorldlineDefinitionDocument:
        return convert_document_value(
            self.to_dict(),
            WorldlineDefinitionDocument,
            source=f"worldline:{self.id}",
        )

    def to_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(msgspec.yaml.encode(self.to_document()))

    def is_stale(self, world: Any) -> bool:
        if self.results is None:
            return False

        stored_hash = self.results.content_hash
        if not stored_hash:
            return True

        from propstore.worldline.runner import run_worldline

        current_results = run_worldline(self, world)
        return current_results.content_hash != stored_hash
