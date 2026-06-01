"""World-to-conflict-detector projection helpers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from propstore.cel_registry import build_store_cel_registry
from propstore.conflict_detector.models import (
    ConflictConcept,
    ConflictConceptRegistry,
    ConflictParameterization,
)
from propstore.core.conditions.registry import ConceptInfo
from propstore.core.environment import ConditionSolverStore
from propstore.families.concepts.declaration import Concept, Parameterization


@dataclass(frozen=True)
class ConflictDetectorInputs:
    concept_registry: ConflictConceptRegistry
    cel_registry: dict[str, ConceptInfo]


@runtime_checkable
class WorldConflictProjectionStore(Protocol):
    def all_concepts(self) -> Iterable[Concept]: ...

    def parameterizations_for(self, concept_id: str) -> Sequence[Parameterization]: ...


def _world_concept_reference_keys(concept: Concept) -> tuple[str, ...]:
    keys: list[str] = []
    seen: set[str] = set()

    def add(candidate: object) -> None:
        if not isinstance(candidate, str) or not candidate or candidate in seen:
            return
        seen.add(candidate)
        keys.append(candidate)

    add(concept.id)
    add(concept.primary_logical_id)
    add(concept.canonical_name)
    for logical_id in concept.parsed_logical_ids():
        add(logical_id.get("value"))
        namespace = logical_id.get("namespace")
        value = logical_id.get("value")
        if (
            isinstance(namespace, str)
            and isinstance(value, str)
            and namespace
            and value
        ):
            add(f"{namespace}:{value}")
    return tuple(keys)


def conflict_detector_inputs_for_world(
    world: WorldConflictProjectionStore,
) -> ConflictDetectorInputs:
    rows = tuple(world.all_concepts())
    entries: list[ConflictConcept] = []
    for concept in rows:
        concept_id = str(concept.id)
        param_rows = world.parameterizations_for(concept_id)
        entries.append(
            ConflictConcept(
                concept_id=concept_id,
                canonical_name=concept.canonical_name,
                form_name=concept.form,
                reference_keys=_world_concept_reference_keys(concept),
                parameterizations=tuple(
                    ConflictParameterization(
                        inputs=param_row.input_concept_ids,
                        sympy=param_row.sympy,
                        exactness=param_row.exactness,
                        conditions=param_row.condition_expressions,
                    )
                    for param_row in param_rows
                ),
            )
        )
    concept_registry = ConflictConceptRegistry(tuple(entries))
    if isinstance(world, ConditionSolverStore):
        cel_registry = dict(world.condition_solver().registry)
    else:
        cel_registry = build_store_cel_registry(rows)
    return ConflictDetectorInputs(
        concept_registry=concept_registry,
        cel_registry=cel_registry,
    )
