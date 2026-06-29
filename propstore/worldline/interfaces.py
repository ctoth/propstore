from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from propstore.core.environment import WorldStore, Environment
from propstore.world.types import BeliefSpace, RenderPolicy

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem


class WorldlineBoundView(BeliefSpace, Protocol):
    pass


@runtime_checkable
class HasEnvironment(Protocol):
    @property
    def environment(self) -> Environment: ...


@runtime_checkable
class HasLiftingSystem(Protocol):
    @property
    def lifting_system(self) -> LiftingSystem | None: ...


class WorldlineStore(WorldStore, Protocol):
    def bind(
        self,
        environment: Environment | None = None,
        *,
        policy: RenderPolicy | None = None,
        **conditions: Any,
    ) -> WorldlineBoundView: ...
