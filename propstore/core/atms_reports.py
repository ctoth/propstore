"""ATMS inspection and future-analysis reports — the canonical report types.

These are *data*: what an ATMS inspection found, not the engine that found it.
They live in ``core`` rather than ``propstore.world`` because they are persisted
— the ``worldlines`` charter stores a rendered argumentation state, and the
charter is read by the storage layer, which may never import ``world``
(``.importlinter``: ``storage``/``source``/``heuristic`` never reach up into
``world``, and ``propstore.families.registry`` imports the worldline charter).

Owning them here is what lets the worldline charter declare a *typed* result
document instead of a ``dict[str, Any]`` blob with a hand-written mapping codec.
The ATMS engine in :mod:`propstore.world.atms` constructs these and
:mod:`propstore.world.types` re-exports them for its existing consumers; there
is exactly one spelling of each.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias, TypeVar

from propstore.conflict_detector import ConflictClass
from propstore.core.id_types import AssumptionId, QueryableId
from propstore.core.labels import EnvironmentKey, Label, SupportQuality

_T = TypeVar("_T")


def _tuple(values: Iterable[_T]) -> tuple[_T, ...]:
    return tuple(values)


def _tuple_of_tuples(values: Iterable[Iterable[_T]]) -> tuple[tuple[_T, ...], ...]:
    return tuple(tuple(value) for value in values)


SerializedEnvironment: TypeAlias = Mapping[str, Sequence[str]]


class ATMSNodeStatus(Enum):
    """ATMS-native node status derived from the propagated label."""

    TRUE = "TRUE"
    IN = "IN"
    OUT = "OUT"


class ATMSOutKind(Enum):
    """Why an ATMS node is currently OUT."""

    MISSING_SUPPORT = "missing_support"
    NOGOOD_PRUNED = "nogood_pruned"
    PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE = (
        "parameterization_input_type_incompatible"
    )


@dataclass(frozen=True)
class ATMSInspection:
    """Inspectible ATMS status plus support-quality honesty metadata."""

    node_id: str
    status: ATMSNodeStatus
    support_quality: SupportQuality
    label: Label | None
    essential_support: EnvironmentKey | None
    reason: str
    out_kind: ATMSOutKind | None = None
    claim_id: str | None = None
    kind: str | None = None


@dataclass(frozen=True)
class ATMSNodeFutureStatusEntry:
    queryable_ids: Sequence[QueryableId]
    queryable_cels: Sequence[str]
    environment: Sequence[AssumptionId]
    consistent: bool
    status: ATMSNodeStatus
    out_kind: ATMSOutKind | None
    reason: str
    support_quality: SupportQuality
    essential_support: SerializedEnvironment

    def __post_init__(self) -> None:
        object.__setattr__(self, "queryable_ids", _tuple(self.queryable_ids))
        object.__setattr__(self, "queryable_cels", _tuple(self.queryable_cels))
        object.__setattr__(self, "environment", _tuple(self.environment))


@dataclass(frozen=True)
class ATMSFutureStatusReport:
    node_id: str
    claim_id: str | None
    current: ATMSInspection
    could_become_in: bool
    could_become_out: bool
    futures: Sequence[ATMSNodeFutureStatusEntry]

    def __post_init__(self) -> None:
        object.__setattr__(self, "futures", _tuple(self.futures))


@dataclass(frozen=True)
class ATMSWhyOutReport:
    node_id: str
    claim_id: str | None
    status: ATMSNodeStatus
    out_kind: ATMSOutKind | None
    reason: str
    support_quality: SupportQuality
    future_activatable: bool
    candidate_queryable_cels: Sequence[Sequence[str]]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "candidate_queryable_cels",
            _tuple_of_tuples(self.candidate_queryable_cels),
        )


@dataclass(frozen=True)
class ATMSNodeStabilityReport:
    node_id: str
    claim_id: str | None
    current: ATMSInspection
    stable: bool
    limit: int | None
    future_count: int
    consistent_future_count: int
    inconsistent_future_count: int
    witnesses: Sequence[ATMSNodeFutureStatusEntry]

    def __post_init__(self) -> None:
        object.__setattr__(self, "witnesses", _tuple(self.witnesses))


@dataclass(frozen=True)
class ATMSNodeRelevanceState:
    queryable_ids: Sequence[QueryableId]
    queryable_cels: Sequence[str]
    environment: Sequence[AssumptionId]
    consistent: bool
    status: ATMSNodeStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "queryable_ids", _tuple(self.queryable_ids))
        object.__setattr__(self, "queryable_cels", _tuple(self.queryable_cels))
        object.__setattr__(self, "environment", _tuple(self.environment))


@dataclass(frozen=True)
class ATMSNodeWitnessPair:
    queryable_id: QueryableId
    queryable_cel: str
    without_state: ATMSNodeRelevanceState
    with_state: ATMSNodeRelevanceState


@dataclass(frozen=True)
class ATMSNodeRelevanceReport:
    node_id: str
    claim_id: str | None
    current: ATMSInspection
    current_status: ATMSNodeStatus
    relevant_queryables: Sequence[str]
    irrelevant_queryables: Sequence[str]
    witness_pairs: Mapping[str, Sequence[ATMSNodeWitnessPair]]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "relevant_queryables", _tuple(self.relevant_queryables)
        )
        object.__setattr__(
            self, "irrelevant_queryables", _tuple(self.irrelevant_queryables)
        )
        object.__setattr__(
            self,
            "witness_pairs",
            {str(key): _tuple(value) for key, value in self.witness_pairs.items()},
        )


@dataclass(frozen=True)
class ATMSNogoodProvenanceDetail:
    claim_a_id: str
    claim_b_id: str
    concept_id: str | None
    warning_class: ConflictClass | None
    environment_a: Sequence[str]
    environment_b: Sequence[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "environment_a", _tuple(self.environment_a))
        object.__setattr__(self, "environment_b", _tuple(self.environment_b))


@dataclass(frozen=True)
class ATMSNogoodDetail:
    environment: Mapping[str, Sequence[str]]
    provenance: Sequence[ATMSNogoodProvenanceDetail]

    def __post_init__(self) -> None:
        object.__setattr__(self, "provenance", _tuple(self.provenance))


__all__ = [
    "ATMSFutureStatusReport",
    "ATMSInspection",
    "ATMSNodeFutureStatusEntry",
    "ATMSNodeRelevanceReport",
    "ATMSNodeRelevanceState",
    "ATMSNodeStabilityReport",
    "ATMSNodeStatus",
    "ATMSNodeWitnessPair",
    "ATMSNogoodDetail",
    "ATMSNogoodProvenanceDetail",
    "ATMSOutKind",
    "ATMSWhyOutReport",
    "SerializedEnvironment",
]
