"""Application-layer worldline workflows.

The owner surface for the ``worldlines`` family: create / materialize / show /
list / diff / delete a worldline, build its transition journal, and project the
claims accepted at a journal step. Every function takes a
:class:`~propstore.repository.Repository` plus a typed request object and returns
a typed report; expected failures surface as the :class:`WorldlineAppError`
hierarchy. Per CLAUDE.md "CLI adapter discipline" this layer owns the behaviour:
it never imports Click, writes to stdout/stderr, or calls ``sys.exit``, and its
requests carry typed domain values rather than flag-shaped CLI inputs.

The worldline is a single canonical charter
(:class:`~propstore.worldline.definition.WorldlineDefinition`), so persistence is
a direct charter ``save``/``load`` — there is no ``to_document`` mirror. The
world-shaped compute forms (render policy, query environment, revision query,
result) ride as their dict serialization on the charter and are compiled one-way
at use time by :mod:`propstore.worldline.runner` / :mod:`propstore.worldline.query`
(``RenderPolicy.from_dict`` etc.); this owner never rebuilds a ``RenderPolicy``
from flag booleans.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from quire.documents import DocumentSchemaError

from propstore.app.world import WorldSidecarMissingError, open_app_world_model
from propstore.families.registry import WorldlineRef
from propstore.policies import policy_profile_from_render_policy
from propstore.world.types import (
    Environment,
    ReasoningBackend,
    RenderPolicy,
    cli_argumentation_semantics_values,
    normalize_argumentation_semantics,
    validate_backend_semantics,
)
from propstore.core.id_types import to_context_id
from propstore.worldline.definition import (
    WorldlineDefinition,
    WorldlineInputs,
    validated_revision_target,
)
from propstore.worldline.query import (
    WorldlineResult,
    WorldlineRevisionQuery,
)
from propstore.worldline.revision_capture import capture_journal
from propstore.worldline.runner import run_worldline
from propstore.worldline.runner import worldline_is_stale as _render_is_stale

if TYPE_CHECKING:
    from propstore.repository import Repository


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
    atom: Mapping[str, Any] | None = None
    target: str | None = None
    conflicts: Mapping[str, tuple[str, ...]] = field(
        default_factory=dict[str, tuple[str, ...]]
    )
    operator: str | None = None


@dataclass(frozen=True)
class WorldlineCreateRequest:
    name: str
    bindings: Mapping[str, str | int | float | bool] = field(
        default_factory=dict[str, str | int | float | bool]
    )
    overrides: Mapping[str, float | str] = field(
        default_factory=dict[str, float | str]
    )
    targets: tuple[str, ...] = ()
    context_id: str | None = None
    policy: WorldlinePolicyOptions = field(default_factory=WorldlinePolicyOptions)
    revision: WorldlineRevisionOptions = field(default_factory=WorldlineRevisionOptions)


@dataclass(frozen=True)
class WorldlineRunRequest:
    name: str
    bindings: Mapping[str, str | int | float | bool] = field(
        default_factory=dict[str, str | int | float | bool]
    )
    overrides: Mapping[str, float | str] = field(
        default_factory=dict[str, float | str]
    )
    targets: tuple[str, ...] = ()
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
class WorldlineBuildJournalRequest:
    name: str


@dataclass(frozen=True)
class WorldlineJournalReport:
    name: str
    step_count: int


@dataclass(frozen=True)
class WorldlineAtStepRequest:
    name: str
    step: int
    heavy: bool = False


@dataclass(frozen=True)
class WorldlineAtStepReport:
    name: str
    step: int
    claim_ids: tuple[str, ...]


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
    left: Mapping[str, Any]
    right: Mapping[str, Any]


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
    definition = repo.families.worldlines.load(WorldlineRef(name))
    if definition is None:
        raise WorldlineNotFoundError(name)
    return definition


def create_worldline(
    repo: Repository,
    request: WorldlineCreateRequest,
) -> WorldlineMutationReport:
    ref = WorldlineRef(request.name)
    path = repo.families.worldlines.address(ref).require_path()
    if repo.families.worldlines.exists(ref):
        raise WorldlineAlreadyExistsError(request.name, path)

    definition = _definition_from_request(request)
    repo.families.worldlines.save(
        ref, definition, message=f"Create worldline: {request.name}"
    )
    return WorldlineMutationReport(name=request.name, path=path)


def materialize_worldline(
    repo: Repository,
    request: WorldlineRunRequest,
) -> WorldlineRunReport:
    ref = WorldlineRef(request.name)
    existing = repo.families.worldlines.load(ref)
    if existing is not None:
        definition = existing
    else:
        if not request.targets:
            raise WorldlineValidationError(
                "targets are required when creating a new worldline"
            )
        definition = _definition_from_request(request)

    with open_app_world_model(repo) as world:
        result = run_worldline(definition, world)
    definition.results = result.to_dict()

    repo.families.worldlines.save(
        ref, definition, message=f"Materialize worldline: {request.name}"
    )
    return WorldlineRunReport(name=request.name, result=result)


def delete_worldline(repo: Repository, name: str) -> WorldlineMutationReport:
    ref = WorldlineRef(name)
    path = repo.families.worldlines.address(ref).require_path()
    if not repo.families.worldlines.exists(ref):
        raise WorldlineNotFoundError(name)
    repo.families.worldlines.delete(ref, message=f"Delete worldline: {name}")
    return WorldlineMutationReport(name=name, path=path)


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


def worldline_is_stale(repo: Repository, name: str) -> bool:
    definition = load_worldline_definition(repo, name)
    with open_app_world_model(repo) as world:
        return _render_is_stale(definition, world)


def list_worldlines(repo: Repository) -> WorldlineListReport:
    entries: list[WorldlineListEntry] = []
    for ref in repo.families.worldlines.iter_refs():
        try:
            definition = load_worldline_definition(repo, ref.name)
        except (DocumentSchemaError, ValueError) as exc:
            entries.append(WorldlineListEntry(name=ref.name, error=str(exc)))
        else:
            status = "materialized" if definition.results else "pending"
            entries.append(
                WorldlineListEntry(
                    name=definition.id or ref.name,
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
    left_results = WorldlineResult.from_dict(left.results)
    right_results = WorldlineResult.from_dict(right.results)
    if left_results is None or right_results is None:
        raise WorldlineValidationError("Both worldlines must be materialized first")

    left_inputs = left.inputs
    right_inputs = right.inputs

    input_differences: list[WorldlineInputDifference] = []
    left_bindings = dict(left_inputs.environment.bindings)
    right_bindings = dict(right_inputs.environment.bindings)
    if left_bindings != right_bindings:
        input_differences.append(
            WorldlineInputDifference(
                label="Bindings", left=left_bindings, right=right_bindings
            )
        )

    left_overrides: dict[str, Any] = dict(left_inputs.overrides)
    right_overrides: dict[str, Any] = dict(right_inputs.overrides)
    if left_overrides != right_overrides:
        input_differences.append(
            WorldlineInputDifference(
                label="Overrides", left=left_overrides, right=right_overrides
            )
        )

    value_differences: list[WorldlineValueDifference] = []
    all_targets = set(left_results.values.keys()) | set(right_results.values.keys())
    for target in sorted(all_targets):
        left_value = left_results.values.get(target)
        right_value = right_results.values.get(target)
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

    left_deps = set(left_results.dependencies.claims)
    right_deps = set(right_results.dependencies.claims)
    return WorldlineDiffReport(
        left_id=left.id,
        right_id=right.id,
        input_differences=tuple(input_differences),
        value_differences=tuple(value_differences),
        only_left_dependencies=tuple(sorted(left_deps - right_deps)),
        only_right_dependencies=tuple(sorted(right_deps - left_deps)),
    )


def build_worldline_journal(
    repo: Repository,
    request: WorldlineBuildJournalRequest,
) -> WorldlineJournalReport:
    ref = WorldlineRef(request.name)
    definition = load_worldline_definition(repo, request.name)
    revision_query = WorldlineRevisionQuery.from_dict(definition.revision)
    if revision_query is None:
        raise WorldlineValidationError("worldline has no revision query to capture")

    inputs = definition.inputs
    policy = RenderPolicy.from_dict(definition.policy)
    with open_app_world_model(repo) as world:
        bound = world.bind(inputs.environment, policy=policy)
        try:
            journal = capture_journal(
                bound,
                (revision_query,),
                policy_payload=policy_profile_from_render_policy(policy).to_dict(),
            )
        except ValueError as exc:
            raise WorldlineValidationError(str(exc)) from exc

    definition.journal = journal.to_dict()
    repo.families.worldlines.save(
        ref, definition, message=f"Build worldline journal: {request.name}"
    )
    return WorldlineJournalReport(name=request.name, step_count=len(journal.entries))


def worldline_at_step(
    repo: Repository,
    request: WorldlineAtStepRequest,
) -> WorldlineAtStepReport:
    definition = load_worldline_definition(repo, request.name)
    journal = definition.transition_journal()
    if journal is None:
        raise WorldlineValidationError(
            "worldline has no journal; build the journal first"
        )
    if request.step < 0:
        raise WorldlineValidationError("journal step must be non-negative")

    with open_app_world_model(repo) as world:
        try:
            view = world.at_journal_step(journal, request.step, heavy=request.heavy)
        except (IndexError, ValueError) as exc:
            raise WorldlineValidationError(str(exc)) from exc
    return WorldlineAtStepReport(
        name=request.name,
        step=request.step,
        claim_ids=tuple(sorted(view.claim_ids())),
    )


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
    if (
        options.operation in {"expand", "revise", "iterated_revise"}
        and options.atom is None
    ):
        raise WorldlineValidationError(
            f"revision atom is required for {options.operation}"
        )
    if options.operation == "contract" and options.target is None:
        raise WorldlineValidationError("revision target is required for contract")
    if options.operation == "iterated_revise" and options.operator is None:
        raise WorldlineValidationError(
            "revision operator is required for iterated_revise"
        )

    revision: dict[str, Any] = {"operation": options.operation}
    if options.atom is not None:
        revision["atom"] = dict(options.atom)
    if options.target is not None:
        revision["target"] = options.target
    if options.conflicts:
        revision["conflicts"] = {
            atom_id: list(targets) for atom_id, targets in options.conflicts.items()
        }
    if options.operator is not None:
        revision["operator"] = options.operator
    return revision


def _definition_from_request(
    request: WorldlineCreateRequest | WorldlineRunRequest,
) -> WorldlineDefinition:
    if not request.targets:
        raise ValueError("Worldline definition requires 'targets'")
    policy = build_worldline_policy_dict(request.policy)
    revision = build_worldline_revision_dict(request.revision)
    if revision:
        validated_revision_target(
            str(revision.get("operation", "")),
            revision.get("target"),
        )
    return WorldlineDefinition(
        id=request.name,
        name=request.name,
        targets=list(request.targets),
        inputs=WorldlineInputs(
            environment=Environment(
                bindings=dict(request.bindings),
                context_id=(
                    None
                    if request.context_id is None
                    else to_context_id(request.context_id)
                ),
            ),
            overrides=dict(request.overrides),
        ),
        policy=policy or {},
        revision=revision or None,
    )
