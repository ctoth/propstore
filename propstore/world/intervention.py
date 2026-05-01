"""Pearl-style intervention and deterministic observation worlds."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from propstore.core.graph_types import CompiledWorldGraph
from propstore.core.id_types import ConceptId, to_concept_id
from propstore.world.scm import StructuralCausalModel, Value
from propstore.world.types import ValueStatus


INTERVENTION_CLAIM_PREFIX = "__intervention_"
OBSERVATION_CLAIM_PREFIX = "__observation_"


class _CompiledGraphWorld(Protocol):
    def compiled_graph(self) -> CompiledWorldGraph | None: ...


class InterventionWorldUnavailable(RuntimeError):
    """Raised when a world cannot supply the compiled graph needed for SCM surgery."""


@dataclass(frozen=True)
class ObservationInconsistent(ValueError):
    concept_id: ConceptId
    observed_value: Value
    actual_value: Value

    def __init__(
        self,
        concept_id: ConceptId | str,
        observed_value: Value,
        actual_value: Value,
    ) -> None:
        typed_concept_id = to_concept_id(concept_id)
        object.__setattr__(self, "concept_id", typed_concept_id)
        object.__setattr__(self, "observed_value", observed_value)
        object.__setattr__(self, "actual_value", actual_value)
        super().__init__(
            f"Observation {typed_concept_id}={observed_value!r} disagrees "
            f"with deterministic SCM value {actual_value!r}"
        )


@dataclass(frozen=True)
class InterventionDiffEntry:
    concept_id: ConceptId
    old_value: Value
    new_value: Value

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_id", to_concept_id(self.concept_id))


@dataclass(frozen=True)
class CausalValueResult:
    concept_id: ConceptId
    status: ValueStatus
    value: Value | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_id", to_concept_id(self.concept_id))


class InterventionWorld:
    """SCM snapshot after Pearl do-surgery."""

    def __init__(
        self,
        scm: StructuralCausalModel,
        assignment: Mapping[ConceptId | str, Value],
    ) -> None:
        self._base_scm = scm
        self._assignment = {
            str(concept_id): value
            for concept_id, value in assignment.items()
        }
        self.scm = scm.intervene(self._assignment)

    @classmethod
    def from_world(
        cls,
        world: _CompiledGraphWorld,
        assignment: Mapping[ConceptId | str, Value],
    ) -> InterventionWorld:
        graph = world.compiled_graph()
        if graph is None:
            raise InterventionWorldUnavailable(
                "intervention requires a compiled parameterization graph; got None"
            )
        return cls(StructuralCausalModel.from_compiled_graph(graph), assignment)

    @property
    def base_scm(self) -> StructuralCausalModel:
        return self._base_scm

    @property
    def assignment(self) -> Mapping[str, Value]:
        return dict(self._assignment)

    def evaluate(self) -> Mapping[str, Value]:
        return self.scm.evaluate()

    def derived_value(self, concept_id: ConceptId | str) -> CausalValueResult:
        typed_concept_id = to_concept_id(concept_id)
        values = self.scm.evaluate()
        concept_key = str(typed_concept_id)
        if concept_key not in values:
            return CausalValueResult(
                concept_id=typed_concept_id,
                status=ValueStatus.NO_RELATIONSHIP,
            )
        return CausalValueResult(
            concept_id=typed_concept_id,
            status=ValueStatus.DERIVED,
            value=values[concept_key],
        )

    def diff(self) -> dict[str, InterventionDiffEntry]:
        base_values = self._base_scm.evaluate()
        post_values = self.scm.evaluate()
        affected = self._base_scm.descendants_of(set(self._assignment))
        affected |= frozenset(self.scm.descendants_of(set(self._assignment)))
        result: dict[str, InterventionDiffEntry] = {}
        for concept_id in sorted(affected):
            old_value = base_values.get(concept_id)
            new_value = post_values.get(concept_id)
            if old_value != new_value:
                result[str(concept_id)] = InterventionDiffEntry(
                    concept_id=to_concept_id(concept_id),
                    old_value=old_value,
                    new_value=new_value,
                )
        return result

    def trace_ids(self) -> tuple[str, ...]:
        return _trace_ids(INTERVENTION_CLAIM_PREFIX, self._assignment)


class ObservationWorld:
    """Deterministic observation: preserve equations and fail on disagreement."""

    def __init__(
        self,
        scm: StructuralCausalModel,
        assignment: Mapping[ConceptId | str, Value],
    ) -> None:
        self.scm = scm
        self._assignment = {
            str(concept_id): value
            for concept_id, value in assignment.items()
        }
        values = scm.evaluate()
        for concept_id, observed_value in self._assignment.items():
            actual_value = values.get(concept_id)
            if actual_value != observed_value:
                raise ObservationInconsistent(
                    concept_id,
                    observed_value,
                    actual_value,
                )

    @property
    def assignment(self) -> Mapping[str, Value]:
        return dict(self._assignment)

    def derived_value(self, concept_id: ConceptId | str) -> CausalValueResult:
        typed_concept_id = to_concept_id(concept_id)
        values = self.scm.evaluate()
        concept_key = str(typed_concept_id)
        if concept_key not in values:
            return CausalValueResult(
                concept_id=typed_concept_id,
                status=ValueStatus.NO_RELATIONSHIP,
            )
        return CausalValueResult(
            concept_id=typed_concept_id,
            status=ValueStatus.DERIVED,
            value=values[concept_key],
        )

    def trace_ids(self) -> tuple[str, ...]:
        return _trace_ids(OBSERVATION_CLAIM_PREFIX, self._assignment)


def _trace_ids(
    prefix: str,
    assignment: Mapping[str, Value],
) -> tuple[str, ...]:
    return tuple(
        f"{prefix}{concept_id}"
        for concept_id in sorted(assignment)
    )
