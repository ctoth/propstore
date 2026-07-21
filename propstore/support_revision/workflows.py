"""World-bound support-revision workflow APIs.

Owner-layer wrappers that bind a :class:`~propstore.core.environment.WorldStore`
to a revision environment and delegate to the :class:`~propstore.world.bound.BoundWorld`
revision surface. The CLI/web adapters call these; they never reconstruct the
revision math themselves (CLAUDE.md CLI adapter discipline). The world layer is
imported lazily inside :func:`_bind_revision_world` so this module stays a leaf of
the support-revision package (no import cycle through ``world.bound``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.core.environment import Environment
from propstore.core.id_types import to_context_id
from propstore.support_revision.input_normalization import normalize_revision_input

if TYPE_CHECKING:
    from propstore.core.environment import WorldStore
    from propstore.support_revision.entrenchment import EntrenchmentReport
    from propstore.support_revision.explanation_types import RevisionExplanation
    from propstore.support_revision.state import (
        BeliefAtom,
        BeliefBase,
        EpistemicState,
        RevisionResult,
    )
    from propstore.world.bound import BoundWorld


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
    store: WorldStore, request: RevisionWorldRequest
) -> BoundWorld:
    from propstore.world.model import bind

    return bind(
        store,
        Environment(
            bindings=dict(request.bindings),
            context_id=(
                None
                if request.context_id is None
                else to_context_id(request.context_id)
            ),
        ),
    )


def revision_base(store: WorldStore, request: RevisionWorldRequest) -> BeliefBase:
    return _bind_revision_world(store, request).revision_base()


def revision_entrenchment(
    store: WorldStore, request: RevisionWorldRequest
) -> EntrenchmentReport:
    return _bind_revision_world(store, request).revision_entrenchment()


def expand_revision(
    store: WorldStore,
    request: RevisionWorldRequest,
    atom: BeliefAtom | str,
) -> RevisionResult:
    return _bind_revision_world(store, request).expand(atom)


def contract_revision(
    store: WorldStore,
    request: RevisionWorldRequest,
    targets: tuple[str, ...],
) -> RevisionResult:
    bound = _bind_revision_world(store, request)
    target_arg: str | tuple[str, ...] = targets[0] if len(targets) == 1 else targets
    return bound.contract(target_arg, max_candidates=4096)


def revise_world(
    store: WorldStore,
    request: RevisionWorldRequest,
    atom: BeliefAtom | str,
    conflicts: tuple[str, ...],
) -> RevisionResult:
    bound = _bind_revision_world(store, request)
    base = bound.revision_base()
    normalized = normalize_revision_input(base, atom)
    conflict_map = {normalized.atom_id: tuple(conflicts)} if conflicts else None
    return bound.revise(normalized, conflicts=conflict_map, max_candidates=4096)


def explain_revision_operation(
    store: WorldStore,
    request: RevisionWorldRequest,
    *,
    operation: str,
    atom: BeliefAtom | str | None = None,
    targets: tuple[str, ...] = (),
    conflicts: tuple[str, ...] = (),
) -> RevisionExplanation:
    bound = _bind_revision_world(store, request)
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
        result = bound.revise(normalized, conflicts=conflict_map, max_candidates=4096)
    else:
        raise ValueError(f"unsupported revision operation: {operation}")
    return bound.revision_explain(result)


def epistemic_state(store: WorldStore, request: RevisionWorldRequest) -> EpistemicState:
    return _bind_revision_world(store, request).epistemic_state()


def iterated_revise_world(
    store: WorldStore,
    request: RevisionWorldRequest,
    *,
    atom: BeliefAtom | str,
    conflicts: tuple[str, ...],
    operator: str,
) -> IteratedRevisionReport:
    bound = _bind_revision_world(store, request)
    state = bound.epistemic_state()
    normalized = normalize_revision_input(state.base, atom)
    conflict_map = {normalized.atom_id: tuple(conflicts)} if conflicts else None
    result, next_state = bound.iterated_revise(
        normalized,
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
