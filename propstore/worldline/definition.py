"""Worldline definitions and materialized results."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from propstore.families.documents.worldlines import (
    WorldlineDefinitionDocument,
    WorldlineInputsDocument,
    WorldlinePolicyDocument,
    WorldlineRevisionQueryDocument,
    WorldlineResultDocument,
)
from quire.documents import convert_document_value, to_document_builtins
from propstore.support_revision.history import TransitionJournal
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


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"worldline field '{field_name}' must be a mapping")
    return value


def _required_document_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"worldline field '{field_name}' must be a mapping")
    return value


class WorldlineRevisionTargetValidationError(ValueError):
    """Raised when a revision target cannot be resolved as an atom id."""


def _validated_revision_target(operation: str, target: object) -> str | None:
    if target is None:
        return None
    target_id = str(target)
    if operation == "contract" and not (
        target_id.startswith("ps:assertion:")
        or target_id.startswith("assumption:")
    ):
        raise WorldlineRevisionTargetValidationError(
            "Worldline revision target must be an assertion or assumption atom id: "
            f"{target_id}"
        )
    return target_id


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
    def from_dict(cls, data: object) -> WorldlineInputs:
        if data is None:
            return cls()
        payload = _optional_mapping(data, "inputs")
        if not payload:
            return cls()
        return cls(
            environment=Environment.from_dict(payload),
            overrides=dict(_optional_mapping(payload.get("overrides"), "overrides")),
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
    profile_atom_ids: tuple[tuple[str, ...], ...] = ()
    integrity_constraint: Mapping[str, Any] | None = None
    merge_parent_commits: tuple[str, ...] = ()
    max_alphabet_size: int | None = None

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
            target=_validated_revision_target(data.operation, data.target),
            conflicts=RevisionConflictSelection(
                {
                    atom_id: tuple(target_ids)
                    for atom_id, target_ids in data.conflicts.items()
                }
            ),
            operator=data.merge_operator or data.operator,
            profile_atom_ids=tuple(tuple(str(atom_id) for atom_id in profile) for profile in data.profile_atom_ids),
            integrity_constraint=None if data.integrity_constraint is None else dict(data.integrity_constraint),
            merge_parent_commits=tuple(str(commit) for commit in data.merge_parent_commits),
            max_alphabet_size=data.max_alphabet_size,
        )

    @classmethod
    def from_dict(cls, data: dict | None) -> WorldlineRevisionQuery | None:
        if not data:
            return None
        return cls(
            operation=str(data.get("operation", "")),
            atom=RevisionAtomRef.from_mapping(data.get("atom")),
            target=_validated_revision_target(str(data.get("operation", "")), data.get("target")),
            conflicts=RevisionConflictSelection.from_mapping(data.get("conflicts")),
            operator=data.get("merge_operator") or data.get("operator"),
            profile_atom_ids=_revision_profile_atom_ids(data.get("profile_atom_ids") or ()),
            integrity_constraint=(
                None
                if data.get("integrity_constraint") is None
                else dict(_optional_mapping(data.get("integrity_constraint"), "integrity_constraint"))
            ),
            merge_parent_commits=tuple(str(commit) for commit in (data.get("merge_parent_commits") or ())),
            max_alphabet_size=(
                None
                if data.get("max_alphabet_size") is None
                else int(data.get("max_alphabet_size"))
            ),
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
        if self.profile_atom_ids:
            data["profile_atom_ids"] = [list(profile) for profile in self.profile_atom_ids]
        if self.integrity_constraint is not None:
            data["integrity_constraint"] = dict(self.integrity_constraint)
        if self.merge_parent_commits:
            data["merge_parent_commits"] = list(self.merge_parent_commits)
        if self.max_alphabet_size is not None:
            data["max_alphabet_size"] = self.max_alphabet_size
        return data


def _revision_profile_atom_ids(value: object) -> tuple[tuple[str, ...], ...]:
    if isinstance(value, str) or not isinstance(value, tuple | list):
        raise ValueError("worldline revision profile_atom_ids must be a sequence")
    profiles: list[tuple[str, ...]] = []
    for profile in value:
        if isinstance(profile, str) or not isinstance(profile, tuple | list):
            raise ValueError("worldline revision profile_atom_ids entries must be sequences")
        profiles.append(tuple(str(atom_id) for atom_id in profile))
    return tuple(profiles)


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
                    _required_document_mapping(
                        to_document_builtins(value),
                        f"values.{target_name}",
                    )
                )
                for target_name, value in data.values.items()
            },
            steps=tuple(
                WorldlineStep.from_mapping(
                    _required_document_mapping(to_document_builtins(step), "steps")
                )
                for step in data.steps
            ),
            dependencies=WorldlineDependencies.from_mapping(
                _required_document_mapping(
                    to_document_builtins(data.dependencies),
                    "dependencies",
                )
            ),
            sensitivity=WorldlineSensitivityReport.from_mapping(data.sensitivity),
            argumentation=WorldlineArgumentationState.from_mapping(data.argumentation),
            revision=WorldlineRevisionState.from_mapping(
                None if data.revision is None else to_document_builtins(data.revision)
            ),
        )

    @classmethod
    def from_dict(cls, data: object) -> WorldlineResult | None:
        if data is None:
            return None
        payload = _optional_mapping(data, "results")
        if not payload:
            return None
        raw_values = _optional_mapping(payload.get("values"), "values")
        values: dict[str, WorldlineTargetValue] = {}
        for target_name, value in raw_values.items():
            if not isinstance(value, Mapping):
                raise ValueError(f"worldline field 'values.{target_name}' must be a mapping")
            values[str(target_name)] = WorldlineTargetValue.from_mapping(value)
        return cls(
            computed=payload.get("computed", ""),
            content_hash=payload.get("content_hash", ""),
            values=values,
            steps=tuple(
                WorldlineStep.from_mapping(step)
                for step in (payload.get("steps") or ())
                if isinstance(step, dict)
            ),
            dependencies=WorldlineDependencies.from_mapping(payload.get("dependencies")),
            sensitivity=WorldlineSensitivityReport.from_mapping(payload.get("sensitivity")),
            argumentation=WorldlineArgumentationState.from_mapping(payload.get("argumentation")),
            revision=WorldlineRevisionState.from_mapping(payload.get("revision")),
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
    journal: TransitionJournal | None = None
    results: WorldlineResult | None = None

    @classmethod
    def from_document(cls, data: WorldlineDefinitionDocument) -> WorldlineDefinition:
        if not data.targets:
            raise ValueError("Worldline definition requires 'targets'")

        policy_payload = None
        if data.policy is not None:
            raw_policy = to_document_builtins(data.policy)
            if not isinstance(raw_policy, Mapping):
                raise ValueError("worldline field 'policy' must be a mapping")
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
            journal=(
                None
                if data.journal is None
                else TransitionJournal.from_mapping(
                    _required_document_mapping(
                        to_document_builtins(data.journal),
                        "journal",
                    )
                )
            ),
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
            journal=(
                None
                if data.get("journal") is None
                else TransitionJournal.from_mapping(
                    _required_document_mapping(data.get("journal"), "journal")
                )
            ),
            results=WorldlineResult.from_dict(data.get("results")),
        )

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
        if self.journal is not None:
            data["journal"] = self.journal.to_dict()
        if self.results is not None:
            data["results"] = self.results.to_dict()
        return data

    def to_document(self) -> WorldlineDefinitionDocument:
        return convert_document_value(
            self.to_dict(),
            WorldlineDefinitionDocument,
            source=f"worldline:{self.id}",
        )

    def is_stale(self, world: Any) -> bool:
        if self.results is None:
            return False

        stored_hash = self.results.content_hash
        if not stored_hash:
            return True

        from propstore.worldline.runner import run_worldline

        current_results = run_worldline(self, world)
        return current_results.content_hash != stored_hash
