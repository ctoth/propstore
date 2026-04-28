"""World-bound support revision workflow APIs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping

from propstore.core.environment import Environment
from propstore.core.id_types import to_context_id
from propstore.support_revision.operators import normalize_revision_input

if TYPE_CHECKING:
    from propstore.support_revision.explanation_types import RevisionExplanation
    from propstore.support_revision.state import (
        BeliefBase,
        EpistemicState,
        RevisionResult,
    )
    from propstore.world import BoundWorld, WorldModel


@dataclass(frozen=True)
class RevisionWorldRequest:
    bindings: Mapping[str, str]
    context_id: str | None = None


@dataclass(frozen=True)
class IteratedRevisionReport:
    result: RevisionResult
    previous_state: EpistemicState
    next_state: EpistemicState
    operator: str


def _bind_revision_world(
    world: WorldModel,
    request: RevisionWorldRequest,
) -> BoundWorld:
    return world.bind(
        Environment(
            bindings=dict(request.bindings),
            context_id=(
                None
                if request.context_id is None
                else to_context_id(request.context_id)
            ),
        )
    )


def revision_base(
    world: WorldModel,
    request: RevisionWorldRequest,
) -> BeliefBase:
    return _bind_revision_world(world, request).revision_base()


def revision_entrenchment(
    world: WorldModel,
    request: RevisionWorldRequest,
):
    return _bind_revision_world(world, request).revision_entrenchment()


def expand_revision(
    world: WorldModel,
    request: RevisionWorldRequest,
    atom: Mapping[str, Any],
) -> RevisionResult:
    return _bind_revision_world(world, request).expand(atom)


def contract_revision(
    world: WorldModel,
    request: RevisionWorldRequest,
    targets: tuple[str, ...],
) -> RevisionResult:
    bound = _bind_revision_world(world, request)
    target_arg: str | tuple[str, ...] = targets[0] if len(targets) == 1 else targets
    return bound.contract(target_arg, max_candidates=4096)


def revise_world(
    world: WorldModel,
    request: RevisionWorldRequest,
    atom: Mapping[str, Any],
    conflicts: tuple[str, ...],
) -> RevisionResult:
    bound = _bind_revision_world(world, request)
    base = bound.revision_base()
    normalized = normalize_revision_input(base, atom)
    conflict_map = {normalized.atom_id: tuple(conflicts)} if conflicts else None
    return bound.revise(atom, conflicts=conflict_map, max_candidates=4096)


def explain_revision_operation(
    world: WorldModel,
    request: RevisionWorldRequest,
    *,
    operation: str,
    atom: Mapping[str, Any] | None = None,
    targets: tuple[str, ...] = (),
    conflicts: tuple[str, ...] = (),
) -> RevisionExplanation:
    bound = _bind_revision_world(world, request)
    if operation == "expand":
        if atom is None:
            raise ValueError("atom is required for expand")
        result = bound.expand(atom)
    elif operation == "contract":
        if not targets:
            raise ValueError("target is required for contract")
        target_arg: str | tuple[str, ...] = targets[0] if len(targets) == 1 else targets
        result = bound.contract(target_arg, max_candidates=4096)
    elif operation == "revise":
        if atom is None:
            raise ValueError("atom is required for revise")
        base = bound.revision_base()
        normalized = normalize_revision_input(base, atom)
        conflict_map = {normalized.atom_id: tuple(conflicts)} if conflicts else None
        result = bound.revise(atom, conflicts=conflict_map, max_candidates=4096)
    else:
        raise ValueError(f"unsupported revision operation: {operation}")
    return bound.revision_explain(result)


def epistemic_state(
    world: WorldModel,
    request: RevisionWorldRequest,
) -> EpistemicState:
    return _bind_revision_world(world, request).epistemic_state()


def iterated_revise_world(
    world: WorldModel,
    request: RevisionWorldRequest,
    *,
    atom: Mapping[str, Any],
    conflicts: tuple[str, ...],
    operator: str,
) -> IteratedRevisionReport:
    bound = _bind_revision_world(world, request)
    state = bound.epistemic_state()
    normalized = normalize_revision_input(state.base, atom)
    conflict_map = {normalized.atom_id: tuple(conflicts)} if conflicts else None
    result, next_state = bound.iterated_revise(
        atom,
        conflicts=conflict_map,
        max_candidates=4096,
        operator=operator,
        state=state,
    )
    return IteratedRevisionReport(
        result=result,
        previous_state=state,
        next_state=next_state,
        operator=operator,
    )
