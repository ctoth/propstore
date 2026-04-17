"""Typed world query owner APIs.

Request/result/failure types owned here:
- `WorldStatusRequest`
- `WorldStatusReport`
- `WorldQueryError`
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.world.types import RenderPolicy

if TYPE_CHECKING:
    from propstore.world.model import WorldModel


class WorldQueryError(Exception):
    """Base class for expected world-query failures."""


@dataclass(frozen=True)
class WorldStatusRequest:
    policy: RenderPolicy


@dataclass(frozen=True)
class WorldStatusReport:
    concept_count: int
    visible_claim_count: int
    conflict_count: int
    diagnostic_count: int


def get_world_status(
    world: WorldModel,
    request: WorldStatusRequest,
) -> WorldStatusReport:
    stats = world.stats()
    visible_claims = len(world.claims_with_policy(None, request.policy))
    diagnostics = world.build_diagnostics(request.policy)
    return WorldStatusReport(
        concept_count=stats.concepts,
        visible_claim_count=visible_claims,
        conflict_count=stats.conflicts,
        diagnostic_count=len(diagnostics),
    )
