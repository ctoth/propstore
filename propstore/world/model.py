"""World-query glue — bind / chain / intervene / observe over a ``WorldStore``.

This module holds the render-time *query behaviour* that turns a
:class:`~propstore.core.environment.WorldStore` into a bound belief space and
answers goal-directed queries over it. It is the 7a-world-C query glue, kept
deliberately separate from the concrete sidecar reader: the functions here take
the ``WorldStore`` protocol as an argument (substrate-style composition — a call,
not a conversion), so the Phase-9 repo-backed ``WorldQuery`` can satisfy the
protocol and reuse this glue unchanged rather than re-implementing it.

What lives here (7a-world-C):

* :func:`compiled_graph` / :func:`active_graph` — lower a store into the compiled
  semantic graph and activate it under an :class:`Environment`.
* :func:`bind` — build a :class:`~propstore.world.bound.BoundWorld` over a store
  and an environment (binding compilation + context lifting).
* :func:`intervene` / :func:`observe` — Pearl ``do()`` / deterministic
  observation worlds, built through the ``causal_models`` substrate package via
  :func:`propstore.world.causal.from_compiled_graph` (no ``world/scm`` mirror).
* :func:`chain_query` — backward-chaining derivation of a target concept over the
  bind + value/derived/resolved surface.

What does NOT live here:

* The concrete sqlite/sidecar reader (``WorldQuery.__init__`` / ``from_path`` /
  ``select_*`` / embeddings / diagnostics / form-algebra / grounding) — Phase 9.
  When it lands it implements the ``WorldStore`` protocol and its ``bind`` /
  ``chain_query`` / ``intervene`` / ``observe`` methods delegate straight to the
  functions here.
* The git-journal / worldline bridge (``at_journal_step`` / ``bind_for_view``) —
  Phase 8 (``support_revision``).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from causal_models import InterventionWorld, ObservationWorld, Value
from condition_ir import to_cel_exprs

from propstore.core.activation import activate_compiled_world_graph
from propstore.core.active_claims import ActiveClaim
from propstore.core.environment import Environment, WorldStore
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.graph_types import ActiveWorldGraph, CompiledWorldGraph
from propstore.core.id_types import to_concept_id
from propstore.core.labels import compile_environment_assumptions
from propstore.world.bound import BoundWorld
from propstore.world.causal import from_compiled_graph
from propstore.world.types import (
    ChainResult,
    ChainStep,
    DerivedResult,
    RenderPolicy,
    ResolutionStrategy,
    ValueResult,
    ValueStatus,
)

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem


def compiled_graph(store: WorldStore) -> CompiledWorldGraph:
    """Build the canonical compiled semantic graph from a store's charters."""

    return build_compiled_world_graph(store)


def active_graph(
    store: WorldStore,
    environment: Environment,
    *,
    lifting_system: LiftingSystem | None = None,
) -> ActiveWorldGraph:
    """Activate the store's compiled graph under ``environment``."""

    return activate_compiled_world_graph(
        compiled_graph(store),
        environment=environment,
        solver=store.condition_solver(),
        lifting_system=lifting_system,
    )


def bind(
    store: WorldStore,
    environment: Environment | None = None,
    *,
    policy: RenderPolicy | None = None,
    lifting_system: LiftingSystem | None = None,
    **conditions: object,
) -> BoundWorld:
    """Bind ``store`` to an environment and return the live belief space.

    ``conditions`` are convenience keyword bindings merged into ``environment``'s
    bindings. When the environment names a context and a ``lifting_system`` is
    supplied, the context's effective assumptions are lifted into the frame
    before the binding/context assumptions are compiled.
    """

    if environment is None:
        environment = Environment(bindings=dict(conditions))
    elif conditions:
        merged = dict(environment.bindings)
        merged.update(conditions)
        environment = Environment(
            bindings=merged,
            context_id=environment.context_id,
            effective_assumptions=tuple(environment.effective_assumptions),
            assumptions=tuple(environment.assumptions),
        )

    if environment.context_id is not None and lifting_system is not None:
        environment = Environment(
            bindings=environment.bindings,
            context_id=environment.context_id,
            effective_assumptions=to_cel_exprs(
                lifting_system.effective_assumptions(str(environment.context_id))
            ),
            assumptions=tuple(environment.assumptions),
        )

    environment = Environment(
        bindings=environment.bindings,
        context_id=environment.context_id,
        effective_assumptions=tuple(environment.effective_assumptions),
        assumptions=compile_environment_assumptions(
            bindings=environment.bindings,
            effective_assumptions=environment.effective_assumptions,
            context_id=environment.context_id,
        ),
    )

    return BoundWorld(
        store,
        environment=environment,
        lifting_system=lifting_system,
        policy=policy,
        active_graph=active_graph(store, environment, lifting_system=lifting_system),
    )


def intervene(
    store: WorldStore,
    assignment: Mapping[str, Value],
    *,
    exogenous_assignment: Mapping[str, Value] | None = None,
) -> InterventionWorld:
    """Return a Pearl-style intervention world over the store's compiled graph."""

    scm = from_compiled_graph(
        compiled_graph(store),
        exogenous_assignment=exogenous_assignment,
    )
    return InterventionWorld(scm, assignment)


def observe(
    store: WorldStore,
    assignment: Mapping[str, Value],
    *,
    exogenous_assignment: Mapping[str, Value] | None = None,
) -> ObservationWorld:
    """Return a deterministic observation world over the store's compiled graph."""

    scm = from_compiled_graph(
        compiled_graph(store),
        exogenous_assignment=exogenous_assignment,
    )
    return ObservationWorld(scm, assignment)


def chain_query(
    store: WorldStore,
    target_concept_id: str,
    strategy: ResolutionStrategy | None = None,
    *,
    lifting_system: LiftingSystem | None = None,
    **bindings: object,
) -> ChainResult:
    """Backward-chain over the parameter space to derive ``target_concept_id``.

    Binds the store under ``bindings``, then iterates the target's
    parameterization group, resolving each concept by direct value, then by the
    chosen resolution ``strategy`` when conflicted, then by derivation from the
    values resolved so far, until no further progress is made.
    """

    policy = RenderPolicy(strategy=strategy) if strategy is not None else None
    bound = bind(
        store,
        Environment(bindings=dict(bindings)),
        policy=policy,
        lifting_system=lifting_system,
    )
    steps: list[ChainStep] = []
    resolved_values: dict[str, float | str | None] = {}
    visited: set[str] = set()
    unresolved_conflicted: list[str] = []

    for key, value in bindings.items():
        steps.append(ChainStep(concept_id=key, value=_as_scalar(value), source="binding"))

    group = store.group_members(target_concept_id)
    if not group:
        group = [target_concept_id]

    changed = True
    while changed:
        changed = False
        for concept_id in group:
            if concept_id in visited:
                continue

            value_result = bound.value_of(concept_id)
            if value_result.status is ValueStatus.DETERMINED:
                value = (
                    _claim_scalar(value_result.claims[0])
                    if value_result.claims
                    else None
                )
                if value is not None:
                    resolved_values[concept_id] = value
                    steps.append(ChainStep(concept_id=concept_id, value=value, source="claim"))
                    visited.add(concept_id)
                    changed = True
                    continue

            if value_result.status is ValueStatus.CONFLICTED and strategy is not None:
                resolved = bound.resolved_value(concept_id)
                if resolved.status is ValueStatus.RESOLVED and resolved.value is not None:
                    resolved_values[concept_id] = resolved.value
                    steps.append(
                        ChainStep(concept_id=concept_id, value=resolved.value, source="resolved")
                    )
                    visited.add(concept_id)
                    changed = True
                    continue

            if (
                value_result.status is ValueStatus.CONFLICTED
                and concept_id not in unresolved_conflicted
            ):
                unresolved_conflicted.append(concept_id)

            derived = bound.derived_value(concept_id, override_values=resolved_values)
            if derived.status is ValueStatus.DERIVED and derived.value is not None:
                resolved_values[concept_id] = derived.value
                steps.append(ChainStep(concept_id=concept_id, value=derived.value, source="derived"))
                visited.add(concept_id)
                changed = True

    result = _target_result(bound, target_concept_id, steps, resolved_values)

    return ChainResult(
        target_concept_id=to_concept_id(target_concept_id),
        result=result,
        steps=steps,
        bindings_used={key: _as_scalar(value) for key, value in bindings.items()},
        unresolved_dependencies=[
            to_concept_id(concept_id) for concept_id in unresolved_conflicted
        ],
    )


def _target_result(
    bound: BoundWorld,
    target_concept_id: str,
    steps: list[ChainStep],
    resolved_values: Mapping[str, float | str | None],
) -> ValueResult | DerivedResult:
    if target_concept_id in resolved_values:
        target_step = next(
            (step for step in steps if step.concept_id == target_concept_id), None
        )
        if target_step is not None and target_step.source == "derived":
            return bound.derived_value(target_concept_id, override_values=resolved_values)
        return bound.value_of(target_concept_id)

    derived = bound.derived_value(target_concept_id, override_values=resolved_values)
    if derived.status is ValueStatus.DERIVED:
        return derived
    return bound.value_of(target_concept_id)


def _claim_scalar(claim: ActiveClaim) -> float | str | None:
    """The scalar value an active claim carries (it rides in ``attributes``)."""

    return _as_scalar(claim.attribute_value("value"))


def _as_scalar(value: object) -> float | str | None:
    """Narrow a keyword binding to the scalar a :class:`ChainStep` records."""

    if value is None or isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return float(value)
    return str(value)
