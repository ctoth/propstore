"""Typed intervention surfaces for fragility.

Fragility ranks *interventions* — the concrete actions (resolve an assumption,
measure a missing input, resolve a conflict, inspect a grounded fact/rule, or a
bridge undercut) that would most reduce the instability of the rendered world.
Each intervention is a typed :class:`InterventionTarget` carrying a kind-specific
:class:`InterventionPayload`, validated so a kind, its family, and its payload
type can never drift apart (CLAUDE.md non-commitment: the surface records *what*
could change, never silently committing to a change).

Provenance rides beside every intervention. The optional
:class:`provenance_semiring.SupportEvidence` on :class:`InterventionProvenance`
is the live witness polynomial behind an ATMS-derived score, kept out-of-band so
it never enters the intervention's identity.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from condition_ir import CelExpr, to_cel_expr
from provenance_semiring import SupportEvidence

from propstore.core.environment import WorldStore
from propstore.core.graph_types import ActiveWorldGraph
from propstore.reporting import JsonReportMixin
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
    support: SupportEvidence | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", InterventionFamily(self.family))
        object.__setattr__(
            self, "source_ids", tuple(str(item) for item in self.source_ids)
        )
        object.__setattr__(
            self,
            "subject_concept_ids",
            tuple(str(item) for item in self.subject_concept_ids),
        )
        object.__setattr__(self, "notes", tuple(str(item) for item in self.notes))


@dataclass(frozen=True)
class AssumptionTarget:
    queryable_id: str
    cel: CelExpr
    stabilizes_concepts: tuple[str, ...]
    witness_count: int
    consistent_future_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "cel", to_cel_expr(self.cel))


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


InterventionPayload = (
    AssumptionTarget
    | MissingMeasurementTarget
    | ConflictTarget
    | GroundFactTarget
    | GroundedRuleTarget
    | BridgeUndercutTarget
)


_KIND_TO_PAYLOAD_TYPE: dict[InterventionKind, type[InterventionPayload]] = {
    InterventionKind.ASSUMPTION: AssumptionTarget,
    InterventionKind.MISSING_MEASUREMENT: MissingMeasurementTarget,
    InterventionKind.CONFLICT: ConflictTarget,
    InterventionKind.GROUND_FACT: GroundFactTarget,
    InterventionKind.GROUNDED_RULE: GroundedRuleTarget,
    InterventionKind.BRIDGE_UNDERCUT: BridgeUndercutTarget,
}

_KIND_TO_FAMILY: dict[InterventionKind, InterventionFamily] = {
    InterventionKind.ASSUMPTION: InterventionFamily.ATMS,
    InterventionKind.MISSING_MEASUREMENT: InterventionFamily.DISCOVERY,
    InterventionKind.CONFLICT: InterventionFamily.CONFLICT,
    InterventionKind.GROUND_FACT: InterventionFamily.GROUNDING,
    InterventionKind.GROUNDED_RULE: InterventionFamily.GROUNDING,
    InterventionKind.BRIDGE_UNDERCUT: InterventionFamily.BRIDGE,
}


@dataclass(frozen=True)
class InterventionTarget:
    intervention_id: str
    kind: InterventionKind
    family: InterventionFamily
    subject_id: str | None
    description: str
    cost_tier: int
    provenance: InterventionProvenance
    payload: InterventionPayload

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", InterventionKind(self.kind))
        object.__setattr__(self, "family", InterventionFamily(self.family))
        object.__setattr__(
            self,
            "subject_id",
            None if self.subject_id is None else str(self.subject_id),
        )
        object.__setattr__(self, "intervention_id", str(self.intervention_id))
        object.__setattr__(self, "description", str(self.description))
        object.__setattr__(self, "cost_tier", int(self.cost_tier))
        expected_family = _KIND_TO_FAMILY[self.kind]
        if self.family is not expected_family:
            raise ValueError(
                f"Intervention kind {self.kind.value!r} requires family {expected_family.value!r}"
            )
        if self.provenance.family is not self.family:
            raise ValueError(
                "Intervention provenance family must match the target family"
            )
        if self.cost_tier <= 0:
            raise ValueError("Intervention cost_tier must be a positive integer")
        expected_payload_type = _KIND_TO_PAYLOAD_TYPE[self.kind]
        if not isinstance(self.payload, expected_payload_type):
            raise TypeError(
                f"Intervention payload for kind {self.kind.value!r} must be "
                f"{expected_payload_type.__name__}"
            )


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
        if not 0.0 <= self.local_fragility <= 1.0:
            raise ValueError("RankedIntervention local_fragility must be in [0, 1]")
        if self.roi < 0.0:
            raise ValueError("RankedIntervention roi must be non-negative")


@dataclass(frozen=True)
class FragilityInteraction:
    intervention_a_id: str
    intervention_b_id: str
    interaction_type: InteractionType
    subjects_affected: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "interaction_type", InteractionType(self.interaction_type)
        )
        object.__setattr__(
            self,
            "subjects_affected",
            tuple(str(item) for item in self.subjects_affected),
        )


@dataclass(frozen=True)
class FragilityReport(JsonReportMixin):
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
        *,
        limit: int | None,
    ) -> ATMSConceptStabilityReport: ...


@runtime_checkable
class FragilityWorld(BeliefSpace, Protocol):
    @property
    def store(self) -> WorldStore: ...

    @property
    def active_graph(self) -> ActiveWorldGraph | None: ...

    def atms_engine(self) -> FragilityATMSEngine: ...
