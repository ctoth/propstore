"""Application-layer worldline workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from propstore.app.world import WorldSidecarMissingError, open_app_world_model
from propstore.families.registry import WorldlineRef
from propstore.repository import Repository
from propstore.world.types import (
    ReasoningBackend,
    normalize_argumentation_semantics,
    validate_backend_semantics,
)
from propstore.worldline import WorldlineDefinition, WorldlineResult


class WorldlineAppError(Exception):
    """Base class for expected worldline workflow failures."""


class WorldlineNotFoundError(WorldlineAppError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Worldline '{name}' not found")
        self.name = name


class WorldlineAlreadyExistsError(WorldlineAppError):
    def __init__(self, name: str, path: str) -> None:
        super().__init__(f"Worldline '{name}' already exists at {path}")
        self.name = name
        self.path = path


class WorldlineValidationError(WorldlineAppError):
    pass


@dataclass(frozen=True)
class WorldlinePolicyOptions:
    strategy: str | None = None
    reasoning_backend: str = "claim_graph"
    semantics: str = "grounded"
    set_comparison: str = "elitist"
    link_principle: str = "last"
    decision_criterion: str = "pignistic"
    pessimism_index: float = 0.5
    praf_strategy: str = "auto"
    praf_epsilon: float = 0.01
    praf_confidence: float = 0.95
    praf_seed: int | None = None


@dataclass(frozen=True)
class WorldlineRevisionOptions:
    operation: str | None = None
    atom: Mapping[str, Any] | None = None
    target: str | None = None
    conflicts: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    operator: str | None = None


@dataclass(frozen=True)
class WorldlineCreateRequest:
    name: str
    bindings: Mapping[str, Any]
    overrides: Mapping[str, float | str]
    targets: tuple[str, ...]
    context_id: str | None = None
    policy: WorldlinePolicyOptions = field(default_factory=WorldlinePolicyOptions)
    revision: WorldlineRevisionOptions = field(default_factory=WorldlineRevisionOptions)


@dataclass(frozen=True)
class WorldlineRunRequest:
    name: str
    bindings: Mapping[str, Any]
    overrides: Mapping[str, float | str]
    targets: tuple[str, ...]
    context_id: str | None = None
    policy: WorldlinePolicyOptions = field(default_factory=WorldlinePolicyOptions)
    revision: WorldlineRevisionOptions = field(default_factory=WorldlineRevisionOptions)


@dataclass(frozen=True)
class WorldlineMutationReport:
    name: str
    path: str


@dataclass(frozen=True)
class WorldlineRunReport:
    name: str
    result: WorldlineResult


def load_worldline_definition(repo: Repository, name: str) -> WorldlineDefinition:
    document = repo.families.worldlines.load(WorldlineRef(name))
    if document is None:
        raise WorldlineNotFoundError(name)
    return WorldlineDefinition.from_document(document)


def build_worldline_policy_dict(
    options: WorldlinePolicyOptions,
) -> dict[str, Any] | None:
    try:
        normalized_backend, normalized_semantics = validate_backend_semantics(
            options.reasoning_backend,
            options.semantics,
        )
    except ValueError as exc:
        raise WorldlineValidationError(str(exc)) from exc

    policy: dict[str, Any] = {}
    if options.strategy:
        policy["strategy"] = options.strategy
    if normalized_backend != ReasoningBackend.CLAIM_GRAPH:
        policy["reasoning_backend"] = normalized_backend.value
    if normalized_semantics != normalize_argumentation_semantics("grounded"):
        policy["semantics"] = normalized_semantics.value
    if options.set_comparison != "elitist":
        policy["comparison"] = options.set_comparison
    if options.link_principle != "last":
        policy["link"] = options.link_principle
    if options.decision_criterion != "pignistic":
        policy["decision_criterion"] = options.decision_criterion
    if options.pessimism_index != 0.5:
        policy["pessimism_index"] = options.pessimism_index
    if options.praf_strategy != "auto":
        policy["praf_strategy"] = options.praf_strategy
    if options.praf_epsilon != 0.01:
        policy["praf_mc_epsilon"] = options.praf_epsilon
    if options.praf_confidence != 0.95:
        policy["praf_mc_confidence"] = options.praf_confidence
    if options.praf_seed is not None:
        policy["praf_mc_seed"] = options.praf_seed
    return policy or None


def build_worldline_revision_dict(
    options: WorldlineRevisionOptions,
) -> dict[str, Any] | None:
    if options.operation is None:
        return None
    if options.operation in {"expand", "revise", "iterated_revise"} and options.atom is None:
        raise WorldlineValidationError(f"--revision-atom is required for {options.operation}")
    if options.operation == "contract" and options.target is None:
        raise WorldlineValidationError("--revision-target is required for contract")
    if options.operation == "iterated_revise" and options.operator is None:
        raise WorldlineValidationError("--revision-operator is required for iterated_revise")

    revision: dict[str, Any] = {"operation": options.operation}
    if options.atom is not None:
        revision["atom"] = dict(options.atom)
    if options.target is not None:
        revision["target"] = options.target
    if options.conflicts:
        revision["conflicts"] = {
            atom_id: list(targets)
            for atom_id, targets in options.conflicts.items()
        }
    if options.operator is not None:
        revision["operator"] = options.operator
    return revision


def _definition_from_request(
    request: WorldlineCreateRequest | WorldlineRunRequest,
) -> WorldlineDefinition:
    definition: dict[str, Any] = {
        "id": request.name,
        "name": request.name,
        "targets": list(request.targets),
    }

    inputs: dict[str, Any] = {}
    if request.bindings:
        inputs["bindings"] = dict(request.bindings)
    if request.overrides:
        inputs["overrides"] = dict(request.overrides)
    if request.context_id:
        inputs["context_id"] = request.context_id
    if inputs:
        definition["inputs"] = inputs

    policy = build_worldline_policy_dict(request.policy)
    if policy:
        definition["policy"] = policy

    revision = build_worldline_revision_dict(request.revision)
    if revision:
        definition["revision"] = revision

    return WorldlineDefinition.from_dict(definition)


def create_worldline(
    repo: Repository,
    request: WorldlineCreateRequest,
) -> WorldlineMutationReport:
    ref = WorldlineRef(request.name)
    address = repo.families.worldlines.family.address_for(repo, ref)
    path = address.require_path()
    if repo.families.worldlines.load(ref) is not None:
        raise WorldlineAlreadyExistsError(request.name, path)

    definition = _definition_from_request(request)
    repo.families.worldlines.save(
        ref,
        definition.to_document(),
        message=f"Create worldline: {request.name}",
    )
    repo.snapshot.sync_worktree()
    return WorldlineMutationReport(name=request.name, path=path)


def materialize_worldline(
    repo: Repository,
    request: WorldlineRunRequest,
) -> WorldlineRunReport:
    from propstore.worldline import run_worldline

    ref = WorldlineRef(request.name)
    if repo.families.worldlines.load(ref) is not None:
        definition = load_worldline_definition(repo, request.name)
    else:
        if not request.targets:
            raise WorldlineValidationError(
                "--target required when creating a new worldline"
            )
        definition = _definition_from_request(request)

    with open_app_world_model(repo) as world:
        result = run_worldline(definition, world)
    definition.results = result

    repo.families.worldlines.save(
        ref,
        definition.to_document(),
        message=f"Materialize worldline: {request.name}",
    )
    repo.snapshot.sync_worktree()
    return WorldlineRunReport(name=request.name, result=result)


def worldline_is_stale(repo: Repository, name: str) -> bool:
    definition = load_worldline_definition(repo, name)
    with open_app_world_model(repo) as world:
        return definition.is_stale(world)


def delete_worldline(repo: Repository, name: str) -> WorldlineMutationReport:
    ref = WorldlineRef(name)
    address = repo.families.worldlines.family.address_for(repo, ref)
    path = address.require_path()
    if repo.families.worldlines.load(ref) is None:
        raise WorldlineNotFoundError(name)
    repo.families.worldlines.delete(ref, message=f"Delete worldline: {name}")
    repo.snapshot.sync_worktree()
    return WorldlineMutationReport(name=name, path=path)
