"""Application-layer worldline workflows."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TypeAlias, TypeGuard

from quire.documents import DocumentSchemaError
from propstore.app.world import WorldSidecarMissingError, open_app_world_model
from propstore.families.registry import WorldlineRef
from propstore.repository import Repository
from propstore.world.types import (
    ReasoningBackend,
    cli_argumentation_semantics_values,
    normalize_argumentation_semantics,
    validate_backend_semantics,
)
from propstore.worldline import WorldlineDefinition, WorldlineResult


JsonValue: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
    | Mapping[str, "JsonValue"]
    | Sequence["JsonValue"]
)
JsonObject: TypeAlias = Mapping[str, JsonValue]


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


def _is_json_value(value: object) -> TypeGuard[JsonValue]:
    if value is None or isinstance(value, str | int | float | bool):
        return True
    if isinstance(value, Mapping):
        return all(
            isinstance(key, str) and _is_json_value(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return all(_is_json_value(item) for item in value)
    return False


def _coerce_json_object(value: object, *, field_name: str) -> dict[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise WorldlineValidationError(f"{field_name} must be a JSON object")
    result: dict[str, JsonValue] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise WorldlineValidationError(f"{field_name} keys must be strings")
        if not _is_json_value(item):
            raise WorldlineValidationError(f"{field_name}.{key} is not JSON-serializable")
        result[key] = item
    return result


def parse_worldline_revision_atom(raw: str | None) -> JsonObject | None:
    if raw is None:
        return None
    try:
        loaded: object = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorldlineValidationError(f"Invalid --revision-atom JSON: {exc}") from exc
    return _coerce_json_object(loaded, field_name="--revision-atom")


def reasoning_backend_values() -> tuple[str, ...]:
    return tuple(backend.value for backend in ReasoningBackend)


def argumentation_semantics_values() -> tuple[str, ...]:
    return cli_argumentation_semantics_values()


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
    atom: JsonObject | None = None
    target: str | None = None
    conflicts: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    operator: str | None = None


@dataclass(frozen=True)
class WorldlineCreateRequest:
    name: str
    bindings: JsonObject
    overrides: Mapping[str, float | str]
    targets: tuple[str, ...]
    context_id: str | None = None
    policy: WorldlinePolicyOptions = field(default_factory=WorldlinePolicyOptions)
    revision: WorldlineRevisionOptions = field(default_factory=WorldlineRevisionOptions)


@dataclass(frozen=True)
class WorldlineRunRequest:
    name: str
    bindings: JsonObject
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


@dataclass(frozen=True)
class WorldlineShowRequest:
    name: str
    check_staleness: bool = False


@dataclass(frozen=True)
class WorldlineShowReport:
    definition: WorldlineDefinition
    stale: bool | None = None
    staleness_unavailable: bool = False


@dataclass(frozen=True)
class WorldlineListEntry:
    name: str
    status: str | None = None
    targets: tuple[str, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class WorldlineListReport:
    entries: tuple[WorldlineListEntry, ...]


@dataclass(frozen=True)
class WorldlineDiffRequest:
    left_name: str
    right_name: str


@dataclass(frozen=True)
class WorldlineInputDifference:
    label: str
    left: JsonObject
    right: JsonObject


@dataclass(frozen=True)
class WorldlineValueDifference:
    target: str
    left_value: float | str | None
    left_status: str
    right_value: float | str | None
    right_status: str


@dataclass(frozen=True)
class WorldlineDiffReport:
    left_id: str
    right_id: str
    input_differences: tuple[WorldlineInputDifference, ...]
    value_differences: tuple[WorldlineValueDifference, ...]
    only_left_dependencies: tuple[str, ...]
    only_right_dependencies: tuple[str, ...]


def load_worldline_definition(repo: Repository, name: str) -> WorldlineDefinition:
    document = repo.families.worldlines.load(WorldlineRef(name))
    if document is None:
        raise WorldlineNotFoundError(name)
    return WorldlineDefinition.from_document(document)


def show_worldline(
    repo: Repository,
    request: WorldlineShowRequest,
) -> WorldlineShowReport:
    definition = load_worldline_definition(repo, request.name)
    if not request.check_staleness:
        return WorldlineShowReport(definition=definition)
    try:
        stale = worldline_is_stale(repo, request.name)
    except WorldSidecarMissingError:
        return WorldlineShowReport(
            definition=definition,
            stale=None,
            staleness_unavailable=True,
        )
    return WorldlineShowReport(definition=definition, stale=stale)


def list_worldlines(repo: Repository) -> WorldlineListReport:
    entries: list[WorldlineListEntry] = []
    for ref in repo.families.worldlines.iter():
        try:
            definition = load_worldline_definition(repo, ref.name)
        except DocumentSchemaError as exc:
            entries.append(WorldlineListEntry(name=ref.name, error=str(exc)))
        except ValueError as exc:
            entries.append(WorldlineListEntry(name=ref.name, error=str(exc)))
        else:
            status = "materialized" if definition.results else "pending"
            entries.append(
                WorldlineListEntry(
                    name=definition.id,
                    status=status,
                    targets=tuple(definition.targets),
                )
            )
    return WorldlineListReport(entries=tuple(entries))


def diff_worldlines(
    repo: Repository,
    request: WorldlineDiffRequest,
) -> WorldlineDiffReport:
    left = load_worldline_definition(repo, request.left_name)
    right = load_worldline_definition(repo, request.right_name)
    if left.results is None or right.results is None:
        raise WorldlineValidationError("Both worldlines must be materialized first")

    input_differences: list[WorldlineInputDifference] = []
    left_bindings = _coerce_json_object(
        dict(left.inputs.environment.bindings),
        field_name="left bindings",
    )
    right_bindings = _coerce_json_object(
        dict(right.inputs.environment.bindings),
        field_name="right bindings",
    )
    if left_bindings != right_bindings:
        input_differences.append(
            WorldlineInputDifference(
                label="Bindings",
                left=left_bindings,
                right=right_bindings,
            )
        )

    left_overrides = _coerce_json_object(dict(left.inputs.overrides), field_name="left overrides")
    right_overrides = _coerce_json_object(dict(right.inputs.overrides), field_name="right overrides")
    if left_overrides != right_overrides:
        input_differences.append(
            WorldlineInputDifference(
                label="Overrides",
                left=left_overrides,
                right=right_overrides,
            )
        )

    value_differences: list[WorldlineValueDifference] = []
    all_targets = set(left.results.values.keys()) | set(right.results.values.keys())
    for target in sorted(all_targets):
        left_value = left.results.values.get(target)
        right_value = right.results.values.get(target)
        left_raw = None if left_value is None else left_value.value
        right_raw = None if right_value is None else right_value.value
        if left_raw != right_raw:
            value_differences.append(
                WorldlineValueDifference(
                    target=target,
                    left_value=left_raw,
                    left_status="absent" if left_value is None else left_value.status,
                    right_value=right_raw,
                    right_status="absent" if right_value is None else right_value.status,
                )
            )

    left_deps = set(left.results.dependencies.claims)
    right_deps = set(right.results.dependencies.claims)
    return WorldlineDiffReport(
        left_id=left.id,
        right_id=right.id,
        input_differences=tuple(input_differences),
        value_differences=tuple(value_differences),
        only_left_dependencies=tuple(sorted(left_deps - right_deps)),
        only_right_dependencies=tuple(sorted(right_deps - left_deps)),
    )


def build_worldline_policy_dict(
    options: WorldlinePolicyOptions,
) -> dict[str, JsonValue] | None:
    try:
        normalized_backend, normalized_semantics = validate_backend_semantics(
            options.reasoning_backend,
            options.semantics,
        )
    except ValueError as exc:
        raise WorldlineValidationError(str(exc)) from exc

    policy: dict[str, JsonValue] = {}
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
) -> dict[str, JsonValue] | None:
    if options.operation is None:
        return None
    if options.operation in {"expand", "revise", "iterated_revise"} and options.atom is None:
        raise WorldlineValidationError(f"--revision-atom is required for {options.operation}")
    if options.operation == "contract" and options.target is None:
        raise WorldlineValidationError("--revision-target is required for contract")
    if options.operation == "iterated_revise" and options.operator is None:
        raise WorldlineValidationError("--revision-operator is required for iterated_revise")

    revision: dict[str, JsonValue] = {"operation": options.operation}
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
    definition: dict[str, JsonValue] = {
        "id": request.name,
        "name": request.name,
        "targets": list(request.targets),
    }

    inputs: dict[str, JsonValue] = {}
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
