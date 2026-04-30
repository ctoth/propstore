"""World consistency owner APIs."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import TYPE_CHECKING, Mapping

from propstore.core.environment import Environment

if TYPE_CHECKING:
    from propstore.repository import Repository
    from propstore.world import WorldQuery


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
class WorldConsistencyReport:
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
                warning_class=(
                    conflict.warning_class.value
                    if conflict.warning_class is not None
                    else "?"
                ),
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
    from propstore.conflict_detector.collectors import conflict_claims_from_claim_files
    from propstore.core.row_types import (
        coerce_concept_row,
        coerce_parameterization_row,
    )

    claim_files = [
        handle
        for handle in repo.families.claims.iter_handles()
    ]
    concept_registry: dict[str, dict] = {}
    for concept_input in world.all_concepts():
        concept_data = coerce_concept_row(concept_input).to_dict()
        concept_id = str(concept_data["id"])
        param_rows = world.parameterizations_for(concept_id)
        if param_rows:
            concept_data["parameterization_relationships"] = []
            for param_row in param_rows:
                param_data = coerce_parameterization_row(param_row).to_dict()
                concept_data["parameterization_relationships"].append(
                    {
                        "inputs": json.loads(param_data["concept_ids"]),
                        "sympy": param_data.get("sympy"),
                        "exactness": param_data.get("exactness"),
                        "conditions": (
                            json.loads(param_data["conditions_cel"])
                            if param_data.get("conditions_cel")
                            else []
                        ),
                    }
                )
        concept_registry[concept_id] = concept_data

    records = detect_transitive_conflicts(
        conflict_claims_from_claim_files(claim_files),
        concept_registry,
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
