from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from propstore.core.environment import WorldStore, Environment
from propstore.core.graph_types import WorldActivationGraph
from propstore.world.types import BeliefSpace, RenderPolicy

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem
    from propstore.support_revision.explanation_types import RevisionExplanation
    from propstore.support_revision.state import EpistemicState, RevisionResult


class WorldlineBoundView(BeliefSpace, Protocol):
    def expand(self, atom: Mapping[str, Any] | None) -> RevisionResult: ...

    def contract(
        self,
        targets: str | None,
        *,
        max_candidates: int,
    ) -> RevisionResult: ...

    def revise(
        self,
        atom: Mapping[str, Any] | None,
        *,
        max_candidates: int,
        conflicts: Mapping[str, tuple[str, ...]] | None = None,
    ) -> RevisionResult: ...

    def iterated_revise(
        self,
        atom: Mapping[str, Any] | None,
        *,
        max_candidates: int,
        conflicts: Mapping[str, tuple[str, ...]] | None = None,
        operator: str,
    ) -> tuple[RevisionResult, EpistemicState]: ...

    def revision_explain(self, result: RevisionResult) -> RevisionExplanation: ...

    def epistemic_state(self) -> EpistemicState: ...

    def revision_state_snapshot(self, state: EpistemicState) -> object: ...


@runtime_checkable
class HasBindings(Protocol):
    _bindings: Mapping[str, Any]


@runtime_checkable
class HasEnvironment(Protocol):
    @property
    def environment(self) -> Environment: ...


@runtime_checkable
class HasLiftingSystem(Protocol):
    @property
    def lifting_system(self) -> LiftingSystem | None: ...


@runtime_checkable
class HasActiveGraph(Protocol):
    _active_graph: WorldActivationGraph | None


class WorldlineStore(WorldStore, Protocol):
    def bind(
        self,
        environment: Environment | None = None,
        *,
        policy: RenderPolicy | None = None,
        **conditions: Any,
    ) -> WorldlineBoundView: ...
