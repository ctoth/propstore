from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from propstore.core.environment import WorldStore, Environment
from propstore.core.graph_types import WorldActivationGraph
from propstore.support_revision.input_normalization import RevisionInput
from propstore.world.types import BeliefSpace, RenderPolicy

if TYPE_CHECKING:
    from propstore.families.contexts.lifting import LiftingSystem
    from propstore.support_revision.explanation_types import RevisionExplanation
    from propstore.support_revision.state import EpistemicState, RevisionResult


class WorldlineBoundView(BeliefSpace, Protocol):
    def expand(self, atom: RevisionInput) -> RevisionResult: ...

    def contract(
        self,
        targets: RevisionInput | Sequence[RevisionInput],
        *,
        max_candidates: int,
    ) -> RevisionResult: ...

    def revise(
        self,
        atom: RevisionInput,
        *,
        max_candidates: int,
        conflicts: Mapping[str, Sequence[str]] | None = None,
    ) -> RevisionResult: ...

    def iterated_revise(
        self,
        atom: RevisionInput,
        *,
        max_candidates: int,
        conflicts: Mapping[str, Sequence[str]] | None = None,
        operator: str,
    ) -> tuple[RevisionResult, EpistemicState]: ...

    def revision_explain(self, result: RevisionResult) -> RevisionExplanation: ...

    def epistemic_state(self) -> EpistemicState: ...

    def revision_state_snapshot(self, state: EpistemicState) -> object: ...


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
    @property
    def active_graph(self) -> WorldActivationGraph | None: ...


class WorldlineStore(WorldStore, Protocol):
    def bind(
        self,
        environment: Environment | None = None,
        *,
        policy: RenderPolicy | None = None,
        **conditions: object,
    ) -> WorldlineBoundView: ...
