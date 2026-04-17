"""ATMS world workflow helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping

from propstore.core.environment import Environment
from propstore.core.id_types import to_context_id
from propstore.world.types import ReasoningBackend, RenderPolicy

if TYPE_CHECKING:
    from propstore.world import BoundWorld, WorldModel


@dataclass(frozen=True)
class ATMSBindRequest:
    bindings: Mapping[str, str]
    context_id: str | None = None


def bind_atms_world(
    world: WorldModel,
    request: ATMSBindRequest,
) -> BoundWorld:
    return world.bind(
        Environment(
            bindings=dict(request.bindings),
            context_id=(
                None
                if request.context_id is None
                else to_context_id(request.context_id)
            ),
        ),
        policy=RenderPolicy(reasoning_backend=ReasoningBackend.ATMS),
    )
