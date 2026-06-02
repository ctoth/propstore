"""World consistency owner APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping

from propstore.reporting import JsonReportMixin
from propstore.core.environment import Environment
from propstore.world.conflict_projection import conflict_detector_inputs_for_world

if TYPE_CHECKING:
    from propstore.repository import Repository
    from propstore.world.model import WorldQuery


@dataclass(frozen=True)
class WorldConsistencyRequest:
    bindings: Mapping[str, str]
    transitive: bool = False


@dataclass(frozen=True)
class WorldConsistencyConflictLine:
    concept_id: str
    warning_class: str | None = None
    claim_a_id: str | None = None
    claim_b_id: str | None = None
    value_a: object = None
    value_b: object = None
    derivation_chain: object = None


@dataclass(frozen=True)
class WorldConsistencyReport(JsonReportMixin):
    transitive: bool
    conflicts: tuple[WorldConsistencyConflictLine, ...]


def check_world_consistency(
    repo: Repository,
    world: WorldQuery,
    request: WorldConsistencyRequest,
) -> WorldConsistencyReport:
    if request.transitive:
        return _check_transitive_consistency(repo, world)

    bound = world.bind(Environment(bindings=dict(request.bindings)))
    return WorldConsistencyReport(
        transitive=False,
        conflicts=tuple(
            WorldConsistencyConflictLine(
                concept_id=str(conflict.concept_id),
                warning_class=conflict.warning_class or "?",
                claim_a_id=str(conflict.claim_a_id),
                claim_b_id=str(conflict.claim_b_id),
            )
            for conflict in bound.conflicts()
        ),
    )


def _check_transitive_consistency(
    repo: Repository,
    world: WorldQuery,
) -> WorldConsistencyReport:
    from propstore.conflict_detector import detect_transitive_conflicts
    from propstore.conflict_detector.collectors import (
        conflict_claims_from_claim_documents,
    )

    claims = [handle.document for handle in repo.families.claims.iter_handles()]
    records = detect_transitive_conflicts(
        conflict_claims_from_claim_documents(claims),
        conflict_detector_inputs_for_world(world).concept_registry,
    )
    return WorldConsistencyReport(
        transitive=True,
        conflicts=tuple(
            WorldConsistencyConflictLine(
                concept_id=str(record.concept_id),
                value_a=record.value_a,
                value_b=record.value_b,
                derivation_chain=record.derivation_chain,
            )
            for record in records
        ),
    )
