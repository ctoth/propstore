"""World-to-conflict-detector projection helpers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from propstore.cel_registry import build_store_cel_registry
from propstore.core.conditions.registry import ConceptInfo
from propstore.core.environment import ConditionSolverStore
from propstore.families.concepts.declaration import Concept, Parameterization


@dataclass(frozen=True)
class ConflictDetectorInputs:
    concept_registry: dict[str, dict]
    cel_registry: dict[str, ConceptInfo]


@runtime_checkable
class WorldConflictProjectionStore(Protocol):
    def all_concepts(self) -> Iterable[Concept]: ...

    def parameterizations_for(self, concept_id: str) -> Sequence[Parameterization]: ...


def concept_registry_for_world(world: WorldConflictProjectionStore) -> dict[str, dict]:
    registry: dict[str, dict] = {}
    for concept in world.all_concepts():
        concept_data = concept.conflict_detector_payload()
        concept_id = str(concept_data["id"])
        param_rows = world.parameterizations_for(concept_id)
        if param_rows:
            concept_data["parameterization_relationships"] = [
                param_row.conflict_detector_payload()
                for param_row in param_rows
            ]
        registry[concept_id] = concept_data
    return registry


def conflict_detector_inputs_for_world(
    world: WorldConflictProjectionStore,
) -> ConflictDetectorInputs:
    rows = tuple(world.all_concepts())
    concept_registry = concept_registry_for_world(world)
    if isinstance(world, ConditionSolverStore):
        cel_registry = dict(world.condition_solver().registry)
    else:
        cel_registry = build_store_cel_registry(rows)
    return ConflictDetectorInputs(
        concept_registry=concept_registry,
        cel_registry=cel_registry,
    )
