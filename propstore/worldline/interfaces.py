from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from propstore.core.environment import ArtifactStore, Environment
from propstore.core.graph_types import ActiveWorldGraph
from propstore.world.types import BeliefSpace, RenderPolicy


class WorldlineBoundView(BeliefSpace, Protocol):
    pass


@runtime_checkable
class HasBindings(Protocol):
    _bindings: Mapping[str, Any]


@runtime_checkable
class HasEnvironment(Protocol):
    _environment: Environment


@runtime_checkable
class HasActiveGraph(Protocol):
    _active_graph: ActiveWorldGraph | None


class WorldlineStore(ArtifactStore, Protocol):
    def bind(
        self,
        environment: Environment | None = None,
        *,
        policy: RenderPolicy | None = None,
        **conditions: Any,
    ) -> WorldlineBoundView: ...
