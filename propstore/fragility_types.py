"""Typed intervention surfaces for fragility."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from propstore.core.environment import ArtifactStore
from propstore.world.types import (
    ATMSConceptStabilityReport,
    BeliefSpace,
    QueryableAssumption,
)


class InterventionKind(StrEnum):
    ASSUMPTION = "assumption"
    MISSING_MEASUREMENT = "missing_measurement"
    CONFLICT = "conflict"
    GROUND_FACT = "ground_fact"
    GROUNDED_RULE = "grounded_rule"
    BRIDGE_UNDERCUT = "bridge_undercut"


class InterventionFamily(StrEnum):
    ATMS = "atms"
    DISCOVERY = "discovery"
    CONFLICT = "conflict"
    GROUNDING = "grounding"
    BRIDGE = "bridge"


class RankingPolicy(StrEnum):
    HEURISTIC_ROI = "heuristic_roi"
    FAMILY_LOCAL_ONLY = "family_local_only"
    PARETO = "pareto"


class InteractionType(StrEnum):
    SYNERGISTIC = "synergistic"
    REDUNDANT = "redundant"
    MIXED = "mixed"
    INDEPENDENT = "independent"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class InterventionProvenance:
    family: InterventionFamily
    source_ids: tuple[str, ...]
    subject_concept_ids: tuple[str, ...]
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", InterventionFamily(self.family))
        object.__setattr__(self, "source_ids", tuple(str(item) for item in self.source_ids))
        object.__setattr__(
            self,
            "subject_concept_ids",
            tuple(str(item) for item in self.subject_concept_ids),
        )
        object.__setattr__(self, "notes", tuple(str(item) for item in self.notes))


@dataclass(frozen=True)
class AssumptionTarget:
    queryable_id: str
    cel: str
    stabilizes_concepts: tuple[str, ...]
    witness_count: int
    consistent_future_count: int


@dataclass(frozen=True)
class MissingMeasurementTarget:
    concept_id: str
    discovered_from_parameterizations: tuple[str, ...]
    downstream_subjects: tuple[str, ...]


@dataclass(frozen=True)
class ConflictTarget:
    claim_a_id: str
    claim_b_id: str
    affected_concept_ids: tuple[str, ...]


@dataclass(frozen=True)
class GroundFactTarget:
    section: str
    predicate_id: str
    row: tuple[object, ...]


@dataclass(frozen=True)
class GroundedRuleTarget:
    rule_name: str
    substitution_key: str
    head_literal: str


@dataclass(frozen=True)
class BridgeUndercutTarget:
    defeater_rule_name: str
    target_rule_name: str
    undercut_literal_key: str


@dataclass(frozen=True)
class InterventionTarget:
    intervention_id: str
    kind: InterventionKind
    family: InterventionFamily
    subject_id: str | None
    description: str
    cost_tier: int
    provenance: InterventionProvenance
    payload: object

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", InterventionKind(self.kind))
        object.__setattr__(self, "family", InterventionFamily(self.family))
        object.__setattr__(self, "subject_id", None if self.subject_id is None else str(self.subject_id))
        object.__setattr__(self, "intervention_id", str(self.intervention_id))
        object.__setattr__(self, "description", str(self.description))
        object.__setattr__(self, "cost_tier", int(self.cost_tier))


@dataclass(frozen=True)
class RankedIntervention:
    target: InterventionTarget
    local_fragility: float
    roi: float
    ranking_policy: RankingPolicy
    score_explanation: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ranking_policy", RankingPolicy(self.ranking_policy))
        object.__setattr__(self, "local_fragility", float(self.local_fragility))
        object.__setattr__(self, "roi", float(self.roi))
        object.__setattr__(self, "score_explanation", str(self.score_explanation))


@dataclass(frozen=True)
class FragilityInteraction:
    intervention_a_id: str
    intervention_b_id: str
    interaction_type: InteractionType
    subjects_affected: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "interaction_type", InteractionType(self.interaction_type))
        object.__setattr__(self, "subjects_affected", tuple(str(item) for item in self.subjects_affected))


@dataclass(frozen=True)
class FragilityReport:
    interventions: tuple[RankedIntervention, ...] = ()
    world_fragility: float = 0.0
    analysis_scope: str = ""
    interactions: tuple[FragilityInteraction, ...] = ()


@runtime_checkable
class FragilityATMSEngine(Protocol):
    def concept_stability(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> ATMSConceptStabilityReport: ...


@runtime_checkable
class FragilityWorld(BeliefSpace, Protocol):
    _store: ArtifactStore

    def atms_engine(self) -> FragilityATMSEngine: ...
