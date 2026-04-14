"""ATMS-style exact-support propagation plus bounded replay, planning, and inquiry.

This engine propagates exact labels globally across active claims and
compatible parameterization justifications, then prunes them with nogoods
induced by active conflicts. It exposes ATMS-native inspection over current
labels and a bounded replay surface for future/queryable assumptions. Those
future views support honest "could this change?" analysis without upgrading
semantic compatibility into exact support. Run 6 adds bounded stability and
relevance analysis, and Run 7 adds bounded additive intervention planning and
next-query suggestions over that same replay substrate. This remains a bounded
ATMS-native analysis over rebuilt future bound worlds rather than AGM-style
revision, entrenchment maintenance, or a full de Kleer runtime manager.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field, replace
from collections.abc import Iterable, Sequence
from itertools import combinations, product
from typing import TYPE_CHECKING, Any, Callable, Protocol, TypeGuard, TypeVar, runtime_checkable

from propstore.core.activation import activate_compiled_world_graph
from propstore.core.active_claims import ActiveClaim
from propstore.core.environment import ArtifactStore
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.id_types import (
    AssumptionId,
    ClaimId,
    QueryableId,
    to_assumption_id,
    to_assumption_ids,
    to_claim_ids,
    to_queryable_ids,
)
from propstore.core.graph_types import ActiveWorldGraph, ClaimNode, ConflictWitness, ParameterizationEdge
from propstore.propagation import evaluate_parameterization
from propstore.core.labels import (
    AssumptionRef,
    EnvironmentKey,
    Label,
    NogoodSet,
    cel_to_binding,
    combine_labels,
    merge_labels,
    SupportQuality,
)
from propstore.core.row_types import (
    ClaimRow,
    ConflictRow,
    ConflictRowInput,
    ParameterizationRow,
    ParameterizationRowInput,
    coerce_conflict_row,
    coerce_parameterization_row,
)
from propstore.world.types import (
    ATMSConceptFutureStatusEntry,
    ATMSConceptInterventionPlan,
    ATMSConceptRelevanceReport,
    ATMSConceptRelevanceState,
    ATMSConceptStabilityReport,
    ATMSAssumptionAntecedent,
    ATMSCycleAntecedent,
    ATMSExplanationAntecedent,
    ATMSFutureEnvironmentReport,
    ATMSFutureStatusReport,
    ATMSInspection,
    ATMSJustificationExplanation,
    ATMSNextQuerySuggestion,
    ATMSNestedNodeExplanation,
    ATMSNodeExplanation,
    ATMSNodeStatus,
    ATMSNodeFutureStatusEntry,
    ATMSNodeInterventionPlan,
    ATMSNodeRelevanceReport,
    ATMSNodeRelevanceState,
    ATMSNodeStabilityReport,
    ATMSNogoodDetail,
    ATMSNogoodProvenanceDetail,
    ATMSOutKind,
    ATMSConceptWitnessPair,
    ATMSLabelVerificationReport,
    ATMSNodeWitnessPair,
    ATMSWhyOutReport,
    Environment,
    QueryableAssumption,
    ValueStatus,
    ValueResult,
    coerce_value_status,
)

if TYPE_CHECKING:
    from propstore.context_hierarchy import ContextHierarchy
    from propstore.world.bound import BoundWorld


@runtime_checkable
class _ATMSRuntimeLike(Protocol):
    @property
    def environment(self) -> Environment: ...

    @property
    def active_graph(self) -> ActiveWorldGraph: ...

    @property
    def all_parameterizations(self) -> Callable[[], list[ParameterizationRowInput]]: ...

    @property
    def active_claims(self) -> Callable[[], list[ActiveClaim]]: ...

    @property
    def conflicts(self) -> Callable[[], list[ConflictRowInput]]: ...

    @property
    def is_param_compatible(self) -> Callable[[str | None], bool]: ...

    @property
    def claim_support(self) -> Callable[[ActiveClaim], tuple[Label | None, SupportQuality]]: ...

    @property
    def concept_status(self) -> Callable[[str], ValueStatus]: ...

    @property
    def replay(self) -> Callable[[tuple[QueryableAssumption, ...]], "_ATMSRuntimeLike"]: ...


@runtime_checkable
class _ATMSBoundLike(Protocol):
    _environment: Environment
    _active_graph: ActiveWorldGraph | None
    _store: ArtifactStore
    _context_hierarchy: ContextHierarchy | None
    _policy: Any

    def is_param_compatible(self, conditions_cel: str | None) -> bool: ...
    def claim_support(self, claim: ActiveClaim) -> tuple[Label | None, SupportQuality]: ...
    def value_of(self, concept_id: str) -> ValueResult: ...
    def rebind(
        self,
        environment: Environment,
        *,
        policy: Any = None,
    ) -> "_ATMSBoundLike": ...


@dataclass(frozen=True)
class ATMSAssumptionNode:
    node_id: str
    assumption: AssumptionRef
    label: Label = field(default_factory=Label)
    justification_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def kind(self) -> str:
        return "assumption"

    @property
    def cel(self) -> str:
        return self.assumption.cel


@dataclass(frozen=True)
class ATMSClaimNode:
    node_id: str
    claim: ActiveClaim
    label: Label = field(default_factory=Label)
    justification_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def kind(self) -> str:
        return "claim"

    @property
    def claim_id(self) -> str:
        return str(self.claim.claim_id)

    @property
    def concept_id(self) -> str | None:
        return None if self.claim.concept_id is None else str(self.claim.concept_id)

    @property
    def value(self) -> float | str | None:
        return self.claim.value


@dataclass(frozen=True)
class ATMSDerivedNode:
    node_id: str
    concept_id: str
    value: float | str
    parameterization_index: int
    formula: str | None = None
    label: Label = field(default_factory=Label)
    justification_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def kind(self) -> str:
        return "derived"


ATMSNode = ATMSAssumptionNode | ATMSClaimNode | ATMSDerivedNode


def _is_assumption_node(node: ATMSNode) -> TypeGuard[ATMSAssumptionNode]:
    return isinstance(node, ATMSAssumptionNode)


def _is_claim_node(node: ATMSNode) -> TypeGuard[ATMSClaimNode]:
    return isinstance(node, ATMSClaimNode)


def _is_derived_node(node: ATMSNode) -> TypeGuard[ATMSDerivedNode]:
    return isinstance(node, ATMSDerivedNode)


@dataclass(frozen=True)
class ATMSJustification:
    justification_id: str
    antecedent_ids: tuple[str, ...]
    consequent_ids: tuple[str, ...]
    informant: str


@dataclass(frozen=True)
class _ATMSRuntime:
    environment: Environment
    active_graph: ActiveWorldGraph
    all_parameterizations: Callable[[], list[ParameterizationRowInput]]
    active_claims: Callable[[], list[ActiveClaim]]
    conflicts: Callable[[], list[ConflictRowInput]]
    is_param_compatible: Callable[[str | None], bool]
    claim_support: Callable[[ActiveClaim], tuple[Label | None, SupportQuality]]
    concept_status: Callable[[str], str]
    replay: Callable[[tuple[QueryableAssumption, ...]], "_ATMSRuntime"]

    @property
    def _environment(self) -> Environment:
        return self.environment

    @property
    def _active_graph(self) -> ActiveWorldGraph:
        return self.active_graph


@dataclass(frozen=True)
class _FutureReplay:
    queryable_ids: tuple[QueryableId, ...]
    queryable_cels: tuple[str, ...]
    environment_key: EnvironmentKey
    consistent: bool
    future_engine: ATMSEngine


_FutureEntryT = TypeVar(
    "_FutureEntryT",
    ATMSNodeFutureStatusEntry,
    ATMSConceptFutureStatusEntry,
)


def _queryable_id_list(values: Iterable[object]) -> list[QueryableId]:
    return list(to_queryable_ids(values))


def _assumption_id_list(values: Iterable[object]) -> list[AssumptionId]:
    return list(to_assumption_ids(values))


def _claim_id_list(values: list[str] | tuple[str, ...] | set[str]) -> list[ClaimId]:
    return list(to_claim_ids(sorted(values)))


def _is_runtime_like(candidate: object) -> TypeGuard[_ATMSRuntimeLike]:
    return isinstance(candidate, _ATMSRuntimeLike)


def _claim_node_to_active_claim(claim_node: ClaimNode) -> ActiveClaim:
    row_data: dict[str, object] = {
        "id": claim_node.claim_id,
        "artifact_id": claim_node.claim_id,
        "concept_id": claim_node.concept_id,
        "type": claim_node.claim_type,
        "value": claim_node.scalar_value,
    }
    row_data.update(dict(claim_node.attributes))
    return ActiveClaim.from_claim_row(ClaimRow.from_mapping(row_data))


def _parameterization_edge_to_row(edge: ParameterizationEdge) -> ParameterizationRow:
    return ParameterizationRow(
        output_concept_id=edge.output_concept_id,
        concept_ids=json.dumps(list(edge.input_concept_ids)),
        formula=edge.formula,
        sympy=edge.sympy,
        exactness=edge.exactness,
        conditions_cel=(None if not edge.conditions else json.dumps(list(edge.conditions))),
    )


def _conflict_witness_to_row(conflict: ConflictWitness) -> ConflictRow:
    return ConflictRow(
        claim_a_id=conflict.left_claim_id,
        claim_b_id=conflict.right_claim_id,
        warning_class=conflict.kind,
        attributes=dict(conflict.details),
    )


def _node_claim(node: ATMSNode) -> ActiveClaim | None:
    return node.claim if _is_claim_node(node) else None


def _node_claim_id(node: ATMSNode) -> str | None:
    return node.claim_id if _is_claim_node(node) else None


def _node_concept_id(node: ATMSNode) -> str | None:
    if _is_claim_node(node):
        return node.concept_id
    if _is_derived_node(node):
        return node.concept_id
    return None


def _node_value(node: ATMSNode) -> float | str | None:
    if _is_claim_node(node):
        return node.value
    if _is_derived_node(node):
        return node.value
    return None


def _node_assumption(node: ATMSNode) -> AssumptionRef | None:
    return node.assumption if _is_assumption_node(node) else None


def _extend_environment(
    environment: Environment,
    queryable_set: tuple[QueryableAssumption, ...],
) -> Environment:
    future_assumptions = tuple(
        sorted(
            environment.assumptions
            + tuple(
                AssumptionRef(
                    assumption_id=to_assumption_id(queryable.assumption_id),
                    kind=queryable.kind,
                    source=queryable.source,
                    cel=queryable.cel,
                )
                for queryable in queryable_set
            ),
            key=lambda assumption: assumption.assumption_id,
        )
    )
    future_effective_assumptions = tuple(
        dict.fromkeys(
            environment.effective_assumptions
            + tuple(queryable.cel for queryable in queryable_set)
        )
    )
    future_bindings = dict(environment.bindings)
    for queryable in queryable_set:
        parsed = cel_to_binding(queryable.cel)
        if parsed is not None:
            key, value = parsed
            future_bindings[key] = value
    return replace(
        environment,
        bindings=future_bindings,
        effective_assumptions=future_effective_assumptions,
        assumptions=future_assumptions,
    )


def _runtime_from_bound(bound: _ATMSBoundLike) -> _ATMSRuntime:
    active_graph = bound._active_graph
    if active_graph is None:
        active_graph = activate_compiled_world_graph(
            build_compiled_world_graph(bound._store),
            environment=bound._environment,
            solver=bound._store.condition_solver(),
            context_hierarchy=bound._context_hierarchy,
        )

    compiled_claims = {
        claim.claim_id: claim
        for claim in active_graph.compiled.claims
    }

    def _active_claims() -> list[ActiveClaim]:
        return [
            _claim_node_to_active_claim(compiled_claims[claim_id])
            for claim_id in active_graph.active_claim_ids
            if claim_id in compiled_claims
        ]

    def _conflicts() -> list[ConflictRowInput]:
        active_ids = set(active_graph.active_claim_ids)
        return [
            _conflict_witness_to_row(conflict)
            for conflict in active_graph.compiled.conflicts
            if conflict.left_claim_id in active_ids and conflict.right_claim_id in active_ids
        ]

    def _all_parameterizations() -> list[ParameterizationRowInput]:
        return [
            _parameterization_edge_to_row(edge)
            for edge in active_graph.compiled.parameterizations
        ]

    def _replay(queryable_set: tuple[QueryableAssumption, ...]) -> _ATMSRuntime:
        future_environment = _extend_environment(bound._environment, queryable_set)
        future_bound = bound.rebind(
            environment=future_environment,
            policy=bound._policy,
        )
        return _runtime_from_bound(future_bound)

    return _ATMSRuntime(
        environment=bound._environment,
        active_graph=active_graph,
        all_parameterizations=_all_parameterizations,
        active_claims=_active_claims,
        conflicts=_conflicts,
        is_param_compatible=lambda conditions_cel: bound.is_param_compatible(conditions_cel),
        claim_support=lambda claim: bound.claim_support(claim),
        concept_status=lambda concept_id: bound.value_of(concept_id).status,
        replay=_replay,
    )


class ATMSEngine:
    """Global exact-support propagation engine for one bound world."""

    def __init__(self, bound: _ATMSRuntimeLike | _ATMSBoundLike) -> None:
        runtime: _ATMSRuntimeLike | _ATMSRuntime
        if _is_runtime_like(bound):
            runtime = bound
        else:
            assert isinstance(bound, _ATMSBoundLike)
            runtime = _runtime_from_bound(bound)
        self._runtime = runtime
        self._bound = self._runtime
        self._nodes: dict[str, ATMSNode] = {}
        self._justifications: dict[str, ATMSJustification] = {}
        self._claim_node_ids: dict[str, str] = {}
        self._assumption_node_ids: dict[str, str] = {}
        self._all_parameterizations = tuple(self._sorted_parameterizations())
        self.nogoods = NogoodSet()
        self._nogood_provenance: dict[EnvironmentKey, tuple[ATMSNogoodProvenanceDetail, ...]] = {}
        self._build()

    def claim_label(self, claim_id: str) -> Label | None:
        node_id = self._claim_node_ids.get(claim_id)
        if node_id is None:
            return None
        return self._label_or_none(self._nodes[node_id].label)

    def supported_claim_ids(self, concept_id: str | None = None) -> set[str]:
        supported: set[str] = set()
        for claim_id, node_id in self._claim_node_ids.items():
            node = self._nodes[node_id]
            if concept_id is not None and _node_concept_id(node) != concept_id:
                continue
            if node.label.environments:
                supported.add(claim_id)
        return supported

    def derived_label(self, concept_id: str, value: float | str | None) -> Label | None:
        if value is None:
            return None
        labels: list[Label] = []
        for node in self._nodes.values():
            if node.kind != "derived":
                continue
            if _node_concept_id(node) != concept_id:
                continue
            if self._normalize_value(_node_value(node)) != self._normalize_value(value):
                continue
            if node.label.environments:
                labels.append(node.label)
        if not labels:
            return None
        merged = merge_labels(labels, nogoods=self.nogoods)
        return self._label_or_none(merged)

    def node_status(self, node_id: str) -> ATMSInspection:
        node = self._nodes.get(node_id)
        if node is None:
            raise KeyError(f"Unknown ATMS node: {node_id}")

        label = self._label_or_none(node.label)
        status = self._status_from_label(node.label)
        support_quality = self._support_quality_for_node(node)
        out_kind = self._out_kind_for_node(node.node_id, status)
        return ATMSInspection(
            node_id=node_id,
            claim_id=_node_claim_id(node),
            kind=node.kind,
            status=status,
            support_quality=support_quality,
            label=label,
            essential_support=self.essential_support(node_id),
            reason=self._reason_for_node(node, status, support_quality),
            out_kind=out_kind,
        )

    def claim_status(self, claim_id: str) -> ATMSInspection:
        node_id = self._claim_node_ids.get(claim_id)
        if node_id is None:
            raise KeyError(f"Unknown ATMS claim: {claim_id}")
        return self.node_status(node_id)

    def future_environments(
        self,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> list[ATMSFutureEnvironmentReport]:
        futures: list[ATMSFutureEnvironmentReport] = []
        for future in self._future_entries(queryables, limit):
            future_engine = future.future_engine
            futures.append({
                "queryable_ids": _queryable_id_list(future.queryable_ids),
                "queryable_cels": list(future.queryable_cels),
                "environment": _assumption_id_list(future.environment_key.assumption_ids),
                "consistent": future.consistent,
                "supported_claim_ids": _claim_id_list(future_engine.supported_claim_ids()),
                "nogoods": [
                    _assumption_id_list(environment.assumption_ids)
                    for environment in future_engine.nogoods.environments
                ],
            })
        return futures

    def node_future_statuses(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> ATMSFutureStatusReport:
        current = self.node_status(node_id)
        futures: list[ATMSNodeFutureStatusEntry] = []
        for future in self._future_entries(queryables, limit):
            future_engine = future.future_engine
            inspection = future_engine._future_node_inspection(node_id, fallback=self._nodes.get(node_id))
            essential_support = self._serialize_environment_key(inspection.essential_support) or []
            futures.append({
                "queryable_ids": _queryable_id_list(future.queryable_ids),
                "queryable_cels": list(future.queryable_cels),
                "environment": _assumption_id_list(future.environment_key.assumption_ids),
                "consistent": future.consistent,
                "status": inspection.status,
                "out_kind": inspection.out_kind,
                "reason": inspection.reason,
                "support_quality": inspection.support_quality,
                "essential_support": _assumption_id_list(essential_support),
            })
        return {
            "node_id": node_id,
            "claim_id": current.claim_id,
            "current": current,
            "could_become_in": current.status == ATMSNodeStatus.OUT
            and any(entry["status"] != ATMSNodeStatus.OUT for entry in futures),
            "could_become_out": (
                current.status != ATMSNodeStatus.OUT
                or any(entry["status"] != ATMSNodeStatus.OUT for entry in futures)
            )
            and any(
                entry["status"] == ATMSNodeStatus.OUT
                and entry["out_kind"] == ATMSOutKind.NOGOOD_PRUNED
                for entry in futures
            ),
            "futures": futures,
        }

    def claim_future_statuses(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> ATMSFutureStatusReport:
        node_id = self._claim_node_ids.get(claim_id)
        if node_id is None:
            raise KeyError(f"Unknown ATMS claim: {claim_id}")
        return self.node_future_statuses(node_id, queryables, limit=limit)

    def why_out(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption] | None = None,
        limit: int = 8,
    ) -> ATMSWhyOutReport:
        inspection = self.node_status(node_id)
        candidate_queryable_cels: list[list[str]] = []
        if inspection.status == ATMSNodeStatus.OUT and queryables:
            for future in self.could_become_in(node_id, queryables, limit=limit):
                candidate_queryable_cels.append(list(future["queryable_cels"]))
        return {
            "node_id": node_id,
            "claim_id": inspection.claim_id,
            "status": inspection.status,
            "out_kind": inspection.out_kind,
            "reason": inspection.reason,
            "support_quality": inspection.support_quality,
            "future_activatable": bool(candidate_queryable_cels),
            "candidate_queryable_cels": candidate_queryable_cels,
        }

    def could_become_in(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> list[ATMSNodeFutureStatusEntry]:
        report = self.node_future_statuses(node_id, queryables, limit=limit)
        return [
            future
            for future in report["futures"]
            if future["status"] != ATMSNodeStatus.OUT
        ]

    def could_become_out(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> list[ATMSNodeFutureStatusEntry]:
        report = self.node_future_statuses(node_id, queryables, limit=limit)
        return [
            future
            for future in report["futures"]
            if future["status"] == ATMSNodeStatus.OUT
            and future["out_kind"] == ATMSOutKind.NOGOOD_PRUNED
        ]

    def status_flip_witnesses(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> list[ATMSNodeFutureStatusEntry]:
        """Return minimal bounded consistent futures whose ATMS status flips."""
        report = self.node_future_statuses(node_id, queryables, limit=limit)
        current_status = report["current"].status
        witnesses = [
            future
            for future in report["futures"]
            if future["consistent"] and future["status"] != current_status
        ]
        return self._minimal_future_entries(witnesses)

    def is_stable(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> bool:
        """Whether the node keeps its current ATMS status in all bounded consistent futures."""
        return self.node_stability(node_id, queryables, limit=limit)["stable"]

    def claim_is_stable(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> bool:
        node_id = self._claim_node_ids.get(claim_id)
        if node_id is None:
            raise KeyError(f"Unknown ATMS claim: {claim_id}")
        return self.is_stable(node_id, queryables, limit=limit)

    def concept_is_stable(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> bool:
        return self.concept_stability(concept_id, queryables, limit=limit)["stable"]

    def node_stability(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> ATMSNodeStabilityReport:
        """Summarize bounded ATMS stability over the implemented replay substrate."""
        report = self.node_future_statuses(node_id, queryables, limit=limit)
        consistent_futures = [future for future in report["futures"] if future["consistent"]]
        witnesses = self._minimal_future_entries([
            future
            for future in consistent_futures
            if future["status"] != report["current"].status
        ])
        return {
            "node_id": report["node_id"],
            "claim_id": report["claim_id"],
            "current": report["current"],
            "stable": not witnesses,
            "limit": limit,
            "future_count": len(report["futures"]),
            "consistent_future_count": len(consistent_futures),
            "inconsistent_future_count": len(report["futures"]) - len(consistent_futures),
            "witnesses": witnesses,
        }

    def claim_stability(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> ATMSNodeStabilityReport:
        node_id = self._claim_node_ids.get(claim_id)
        if node_id is None:
            raise KeyError(f"Unknown ATMS claim: {claim_id}")
        return self.node_stability(node_id, queryables, limit=limit)

    def concept_stability(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> ATMSConceptStabilityReport:
        """Summarize bounded concept stability using the current BoundWorld value status."""
        current_status = self._runtime.concept_status(concept_id)
        futures = self._concept_future_entries(concept_id, queryables, limit=limit)
        consistent_futures = [future for future in futures if future["consistent"]]
        witnesses = self._minimal_future_entries([
            future
            for future in consistent_futures
            if future["status"] != current_status
        ])
        return {
            "concept_id": concept_id,
            "current_status": current_status,
            "stable": not witnesses,
            "limit": limit,
            "future_count": len(futures),
            "consistent_future_count": len(consistent_futures),
            "inconsistent_future_count": len(futures) - len(consistent_futures),
            "witnesses": witnesses,
        }

    def relevant_queryables(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> list[str]:
        """Return queryables whose inclusion changes the bounded ATMS status somewhere."""
        return self.node_relevance(node_id, queryables, limit=limit)["relevant_queryables"]

    def claim_relevant_queryables(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> list[str]:
        node_id = self._claim_node_ids.get(claim_id)
        if node_id is None:
            raise KeyError(f"Unknown ATMS claim: {claim_id}")
        return self.relevant_queryables(node_id, queryables, limit=limit)

    def concept_relevant_queryables(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> list[str]:
        return self.concept_relevance(concept_id, queryables, limit=limit)["relevant_queryables"]

    def node_relevance(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> ATMSNodeRelevanceReport:
        """Summarize which queryables can flip a node's bounded ATMS status."""
        current = self.node_status(node_id)
        states = self._node_relevance_states(node_id, queryables, limit=limit)
        relevant_queryables, irrelevant_queryables, witness_pairs = self._node_relevance_from_states(
            states,
            current.status,
        )
        return {
            "node_id": node_id,
            "claim_id": current.claim_id,
            "current": current,
            "current_status": current.status,
            "relevant_queryables": relevant_queryables,
            "irrelevant_queryables": irrelevant_queryables,
            "witness_pairs": witness_pairs,
        }

    def claim_relevance(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> ATMSNodeRelevanceReport:
        node_id = self._claim_node_ids.get(claim_id)
        if node_id is None:
            raise KeyError(f"Unknown ATMS claim: {claim_id}")
        return self.node_relevance(node_id, queryables, limit=limit)

    def concept_relevance(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int = 8,
    ) -> ATMSConceptRelevanceReport:
        """Summarize which queryables can flip a concept's bounded value status."""
        current_status = self._runtime.concept_status(concept_id)
        states = self._concept_relevance_states(concept_id, queryables, limit=limit)
        relevant_queryables, irrelevant_queryables, witness_pairs = self._concept_relevance_from_states(
            states,
            current_status,
        )
        return {
            "concept_id": concept_id,
            "current_status": current_status,
            "relevant_queryables": relevant_queryables,
            "irrelevant_queryables": irrelevant_queryables,
            "witness_pairs": witness_pairs,
        }

    def node_interventions(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption],
        target_status: ATMSNodeStatus | str,
        *,
        limit: int = 8,
        max_plans: int | None = None,
    ) -> list[ATMSNodeInterventionPlan]:
        """Return minimal additive plans that reach the requested ATMS node status."""
        normalized_target = self._coerce_node_target_status(target_status)
        current = self.node_status(node_id)
        candidates = [
            future
            for future in self.node_future_statuses(node_id, queryables, limit=limit)["futures"]
            if future["consistent"] and self._future_reaches_node_target(future, normalized_target)
        ]
        plans = [
            self._node_intervention_plan(
                node_id,
                current=current,
                target_status=normalized_target,
                future=future,
            )
            for future in self._minimal_future_entries(candidates)
        ]
        if max_plans is not None:
            return plans[:max_plans]
        return plans

    def claim_interventions(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        target_status: ATMSNodeStatus | str,
        *,
        limit: int = 8,
        max_plans: int | None = None,
    ) -> list[ATMSNodeInterventionPlan]:
        node_id = self._claim_node_ids.get(claim_id)
        if node_id is None:
            raise KeyError(f"Unknown ATMS claim: {claim_id}")
        return self.node_interventions(
            node_id,
            queryables,
            target_status,
            limit=limit,
            max_plans=max_plans,
        )

    def concept_interventions(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        target_value_status: ValueStatus,
        *,
        limit: int = 8,
        max_plans: int | None = None,
    ) -> list[ATMSConceptInterventionPlan]:
        """Return minimal additive plans that reach the requested concept value status."""
        current_status = self._runtime.concept_status(concept_id)
        normalized_target = self._coerce_concept_target_status(target_value_status)
        candidates = [
            future
            for future in self._concept_future_entries(concept_id, queryables, limit=limit)
            if future["consistent"] and future["status"] == normalized_target
        ]
        plans = [
            self._concept_intervention_plan(
                concept_id,
                current_status=current_status,
                target_status=normalized_target,
                future=future,
            )
            for future in self._minimal_future_entries(candidates)
        ]
        if max_plans is not None:
            return plans[:max_plans]
        return plans

    def next_queryables_for_node(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption],
        target_status: ATMSNodeStatus | str,
        *,
        limit: int = 8,
        max_suggestions: int | None = None,
    ) -> list[ATMSNextQuerySuggestion]:
        plans = self.node_interventions(
            node_id,
            queryables,
            target_status,
            limit=limit,
        )
        return self._next_queryables_from_plans(plans, max_suggestions=max_suggestions)

    def next_queryables_for_claim(
        self,
        claim_id: str,
        queryables: Sequence[QueryableAssumption],
        target_status: ATMSNodeStatus | str,
        *,
        limit: int = 8,
        max_suggestions: int | None = None,
    ) -> list[ATMSNextQuerySuggestion]:
        node_id = self._claim_node_ids.get(claim_id)
        if node_id is None:
            raise KeyError(f"Unknown ATMS claim: {claim_id}")
        return self.next_queryables_for_node(
            node_id,
            queryables,
            target_status,
            limit=limit,
            max_suggestions=max_suggestions,
        )

    def next_queryables_for_concept(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        target_value_status: ValueStatus,
        *,
        limit: int = 8,
        max_suggestions: int | None = None,
    ) -> list[ATMSNextQuerySuggestion]:
        plans = self.concept_interventions(
            concept_id,
            queryables,
            target_value_status,
            limit=limit,
        )
        return self._next_queryables_from_plans(plans, max_suggestions=max_suggestions)

    def essential_support(
        self,
        node_id: str,
        environment: EnvironmentKey | tuple[str, ...] | list[str] | None = None,
    ) -> EnvironmentKey | None:
        node = self._nodes.get(node_id)
        if node is None:
            raise KeyError(f"Unknown ATMS node: {node_id}")
        if not node.label.environments:
            return None

        bound_environment = (
            self._bound_environment_key()
            if environment is None
            else self._coerce_environment_key(environment)
        )
        compatible = [
            env
            for env in node.label.environments
            if env.subsumes(bound_environment)
        ]
        if not compatible:
            return None

        shared = set(compatible[0].assumption_ids)
        for env in compatible[1:]:
            shared.intersection_update(env.assumption_ids)
        return EnvironmentKey(tuple(sorted(shared)))

    def nodes_in_environment(
        self,
        environment: EnvironmentKey | tuple[str, ...] | list[str],
    ) -> list[str]:
        environment_key = self._coerce_environment_key(environment)
        return sorted(
            node_id
            for node_id, node in self._nodes.items()
            if any(label_env.subsumes(environment_key) for label_env in node.label.environments)
        )

    def explain_node(self, node_id: str) -> ATMSNodeExplanation:
        return self._explain_node(node_id, seen_nodes={node_id})

    def explain_nogood(
        self,
        environment_key: EnvironmentKey | tuple[str, ...] | list[str],
    ) -> ATMSNogoodDetail | None:
        query = self._coerce_environment_key(environment_key)
        if query not in self.nogoods.environments:
            return None
        return self._serialize_nogood_detail(query)

    def verify_labels(self) -> ATMSLabelVerificationReport:
        consistency_errors: list[str] = []
        minimality_errors: list[str] = []
        soundness_errors: list[str] = []
        completeness_errors: list[str] = []
        known_assumptions = set(self._assumption_node_ids)

        for node_id, node in sorted(self._nodes.items()):
            environments = node.label.environments
            for environment in environments:
                if self.nogoods.excludes(environment):
                    consistency_errors.append(
                        f"{node_id}: environment {environment.assumption_ids} is excluded by a nogood"
                    )
                unknown = [
                    assumption_id
                    for assumption_id in environment.assumption_ids
                    if assumption_id not in known_assumptions
                ]
                if unknown:
                    consistency_errors.append(
                        f"{node_id}: environment {environment.assumption_ids} references unknown assumptions {unknown}"
                    )

            for index, environment in enumerate(environments):
                for other in environments[index + 1:]:
                    if environment.subsumes(other) or other.subsumes(environment):
                        minimality_errors.append(
                            f"{node_id}: label contains non-minimal environments {environment.assumption_ids} and {other.assumption_ids}"
                        )

            expected = self._expected_label_for_node(node_id)
            actual_environments = set(environments)
            expected_environments = set(expected.environments)
            missing = sorted(expected_environments - actual_environments, key=lambda env: env.assumption_ids)
            extra = sorted(actual_environments - expected_environments, key=lambda env: env.assumption_ids)
            for environment in extra:
                soundness_errors.append(
                    f"{node_id}: environment {environment.assumption_ids} is not justified by the current ATMS graph"
                )
            for environment in missing:
                completeness_errors.append(
                    f"{node_id}: missing justified environment {environment.assumption_ids}"
                )

        return {
            "ok": not (
                consistency_errors
                or minimality_errors
                or soundness_errors
                or completeness_errors
            ),
            "consistency_errors": consistency_errors,
            "minimality_errors": minimality_errors,
            "soundness_errors": soundness_errors,
            "completeness_errors": completeness_errors,
        }

    def argumentation_state(
        self,
        *,
        queryables: Sequence[QueryableAssumption] | None = None,
        future_limit: int = 8,
    ) -> dict[str, Any]:
        claim_inspections = {
            str(claim.claim_id): self.claim_status(str(claim.claim_id))
            for claim in self._runtime.active_claims()
            if str(claim.claim_id) in self._claim_node_ids
        }
        result = {
            "backend": "atms",
            "supported": sorted(self.supported_claim_ids()),
            "defeated": sorted(
                str(claim.claim_id)
                for claim in self._runtime.active_claims()
                if str(claim.claim_id) not in self.supported_claim_ids()
            ),
            "nogoods": [
                list(environment.assumption_ids)
                for environment in self.nogoods.environments
            ],
            "node_statuses": {
                inspection.node_id: inspection.status.value
                for inspection in claim_inspections.values()
            },
            "support_quality": {
                claim_id: inspection.support_quality.value
                for claim_id, inspection in claim_inspections.items()
            },
            "essential_support": {
                claim_id: self._serialize_environment_key(inspection.essential_support) or []
                for claim_id, inspection in claim_inspections.items()
            },
            "status_reasons": {
                claim_id: inspection.reason
                for claim_id, inspection in claim_inspections.items()
            },
            "nogood_details": [
                self._serialize_nogood_detail(environment)
                for environment in self.nogoods.environments
            ],
        }
        normalized_queryables = self._coerce_queryables(queryables or ())
        if normalized_queryables:
            result["declared_queryables"] = [queryable.cel for queryable in normalized_queryables]
            result["future_statuses"] = {
                claim_id: self._serialize_future_report(
                    self.claim_future_statuses(
                        claim_id,
                        normalized_queryables,
                        limit=future_limit,
                    )
                )
                for claim_id in sorted(claim_inspections)
            }
            result["stability"] = {
                claim_id: self._serialize_stability_report(
                    self.claim_stability(
                        claim_id,
                        normalized_queryables,
                        limit=future_limit,
                    )
                )
                for claim_id in sorted(claim_inspections)
            }
            result["relevance"] = {
                claim_id: self._serialize_relevance_report(
                    self.claim_relevance(
                        claim_id,
                        normalized_queryables,
                        limit=future_limit,
                    )
                )
                for claim_id in sorted(claim_inspections)
            }
            result["witness_futures"] = {
                claim_id: [
                    self._serialize_future_entry(witness)
                    for witness in self.status_flip_witnesses(
                        self._claim_node_ids[claim_id],
                        normalized_queryables,
                        limit=future_limit,
                    )
                ]
                for claim_id in sorted(claim_inspections)
            }
            why_out = {
                claim_id: self._serialize_why_out(
                    self.why_out(
                        self._claim_node_ids[claim_id],
                        queryables=normalized_queryables,
                        limit=future_limit,
                    )
                )
                for claim_id, inspection in sorted(claim_inspections.items())
                if inspection.status == ATMSNodeStatus.OUT
            }
            if why_out:
                result["why_out"] = why_out
        return result

    def _build(self) -> None:
        self._build_assumption_nodes()
        self._build_claim_nodes_and_justifications()

        while True:
            self._propagate_labels()
            added_justifications = self._materialize_parameterization_justifications()
            updated_nogoods = self._update_nogoods()
            if not added_justifications and not updated_nogoods:
                self._propagate_labels()
                break

    def _build_assumption_nodes(self) -> None:
        for assumption in sorted(
            self._runtime.environment.assumptions,
            key=lambda item: item.assumption_id,
        ):
            node_id = f"assumption:{assumption.assumption_id}"
            node = ATMSAssumptionNode(
                node_id=node_id,
                assumption=assumption,
                label=Label.singleton(assumption),
            )
            self._nodes[node_id] = node
            self._assumption_node_ids[assumption.assumption_id] = node_id

    def _build_claim_nodes_and_justifications(self) -> None:
        for claim in sorted(self._runtime.active_claims(), key=lambda row: str(row.claim_id)):
            claim_id = str(claim.claim_id)
            node_id = f"claim:{claim_id}"
            self._nodes[node_id] = ATMSClaimNode(
                node_id=node_id,
                claim=claim,
            )
            self._claim_node_ids[claim_id] = node_id

            for antecedents in self._exact_antecedent_sets(
                claim.conditions_cel_json,
                context_id=claim.context_id,
            ):
                self._add_justification(
                    antecedent_ids=antecedents,
                    consequent_id=node_id,
                    informant=f"claim:{claim_id}",
                )

    def _propagate_labels(self) -> None:
        seeded_nodes = {
            node_id: node.label
            for node_id, node in self._nodes.items()
            if node.kind == "assumption"
        }
        for node_id, node in list(self._nodes.items()):
            if node.kind != "assumption":
                self._nodes[node_id] = replace(node, label=Label(()))

        for node_id, label in seeded_nodes.items():
            self._nodes[node_id] = replace(self._nodes[node_id], label=label)

        changed = True
        while changed:
            changed = False
            for justification_id in sorted(self._justifications):
                justification = self._justifications[justification_id]
                antecedent_labels: list[Label] = []
                supported = True
                for antecedent_id in justification.antecedent_ids:
                    label = self._nodes[antecedent_id].label
                    if not label.environments:
                        supported = False
                        break
                    antecedent_labels.append(label)
                if not supported:
                    continue

                candidate = combine_labels(*antecedent_labels, nogoods=self.nogoods)
                for consequent_id in justification.consequent_ids:
                    current = self._nodes[consequent_id].label
                    merged = merge_labels([current, candidate], nogoods=self.nogoods)
                    if merged != current:
                        self._nodes[consequent_id] = replace(
                            self._nodes[consequent_id],
                            label=merged,
                        )
                        changed = True

    def _materialize_parameterization_justifications(self) -> bool:
        added = False
        provider_ids_by_concept = self._provider_node_ids_by_concept()

        for index, param_input in enumerate(self._all_parameterizations):
            param = coerce_parameterization_row(param_input)
            if not self._runtime.is_param_compatible(param.conditions_cel):
                continue

            condition_antecedents = self._exact_antecedent_sets(
                param.conditions_cel,
            )
            if not condition_antecedents:
                continue

            output_concept_id = str(param.output_concept_id)
            sympy_expr = param.sympy
            if not sympy_expr:
                continue

            input_ids = json.loads(param.concept_ids)
            effective_inputs = [concept_id for concept_id in input_ids if concept_id != output_concept_id]
            input_provider_sets = [provider_ids_by_concept.get(concept_id, ()) for concept_id in effective_inputs]
            if any(not provider_ids for provider_ids in input_provider_sets):
                continue

            for provider_combo in product(*input_provider_sets):
                input_values = {
                    concept_id: float(_node_value(self._nodes[node_id]))
                    for concept_id, node_id in zip(effective_inputs, provider_combo, strict=True)
                }
                derived_value = evaluate_parameterization(sympy_expr, input_values, output_concept_id)
                if derived_value is None:
                    continue

                derived_node_id = self._derived_node_id(output_concept_id, derived_value)
                if derived_node_id not in self._nodes:
                    self._nodes[derived_node_id] = ATMSDerivedNode(
                        node_id=derived_node_id,
                        concept_id=output_concept_id,
                        value=derived_value,
                        parameterization_index=index,
                        formula=param.formula,
                    )

                for condition_antecedent_ids in condition_antecedents:
                    antecedent_ids = tuple(condition_antecedent_ids + provider_combo)
                    added |= self._add_justification(
                        antecedent_ids=antecedent_ids,
                        consequent_id=derived_node_id,
                        informant=f"parameterization:{index}",
                    )

        return added

    def _update_nogoods(self) -> bool:
        environments: list[EnvironmentKey] = list(self.nogoods.environments)
        provenance: dict[EnvironmentKey, list[ATMSNogoodProvenanceDetail]] = defaultdict(list)
        for environment, details in self._nogood_provenance.items():
            provenance[environment].extend(details)
        for conflict_input in self._runtime.conflicts():
            conflict = coerce_conflict_row(conflict_input)
            claim_a = str(conflict.claim_a_id)
            claim_b = str(conflict.claim_b_id)

            label_a = self.claim_label(claim_a)
            label_b = self.claim_label(claim_b)
            if label_a is None or label_b is None:
                continue

            for env_a in label_a.environments:
                for env_b in label_b.environments:
                    nogood_environment = env_a.union(env_b)
                    environments.append(nogood_environment)
                    provenance[nogood_environment].append({
                        "claim_a_id": claim_a,
                        "claim_b_id": claim_b,
                        "concept_id": conflict.concept_id,
                        "warning_class": conflict.warning_class,
                        "environment_a": list(env_a.assumption_ids),
                        "environment_b": list(env_b.assumption_ids),
                    })

        updated = NogoodSet(tuple(environments))
        if updated == self.nogoods:
            return False
        self.nogoods = updated
        self._nogood_provenance = {
            environment: tuple(provenance.get(environment, ()))
            for environment in self.nogoods.environments
        }
        return True

    def _provider_node_ids_by_concept(self) -> dict[str, tuple[str, ...]]:
        providers: dict[str, list[str]] = defaultdict(list)
        for node_id, node in self._nodes.items():
            if node.kind not in {"claim", "derived"}:
                continue
            if not node.label.environments:
                continue
            concept_id = _node_concept_id(node)
            value = _node_value(node)
            if concept_id is None or value is None:
                continue
            providers[concept_id].append(node_id)
        return {
            concept_id: tuple(sorted(node_ids))
            for concept_id, node_ids in providers.items()
        }

    def _sorted_parameterizations(self) -> list[ParameterizationRowInput]:
        return sorted(
            self._runtime.all_parameterizations(),
            key=lambda row: (
                str(coerce_parameterization_row(row).output_concept_id),
                coerce_parameterization_row(row).formula or "",
                coerce_parameterization_row(row).sympy or "",
            ),
        )

    def _exact_antecedent_sets(
        self,
        conditions_cel: str | None,
        *,
        context_id: str | None = None,
    ) -> list[tuple[str, ...]]:
        if not conditions_cel:
            return [] if context_id is not None else [()]

        try:
            conditions = json.loads(conditions_cel)
        except (TypeError, json.JSONDecodeError):
            return []
        if not conditions:
            return [] if context_id is not None else [()]

        matching_node_groups: list[list[str]] = []
        for condition in conditions:
            matches = [
                node_id
                for node_id, node in self._nodes.items()
                if node.kind == "assumption"
                and (assumption := _node_assumption(node)) is not None
                and assumption.cel == condition
            ]
            if not matches:
                return []
            matching_node_groups.append(sorted(matches))

        return [
            tuple(sorted(node_ids))
            for node_ids in product(*matching_node_groups)
        ]

    def _add_justification(
        self,
        *,
        antecedent_ids: tuple[str, ...],
        consequent_id: str,
        informant: str,
    ) -> bool:
        justification_id = self._justification_id(
            antecedent_ids=antecedent_ids,
            consequent_id=consequent_id,
            informant=informant,
        )
        if justification_id in self._justifications:
            return False

        justification = ATMSJustification(
            justification_id=justification_id,
            antecedent_ids=tuple(sorted(antecedent_ids)),
            consequent_ids=(consequent_id,),
            informant=informant,
        )
        self._justifications[justification_id] = justification

        node = self._nodes[consequent_id]
        self._nodes[consequent_id] = replace(
            node,
            justification_ids=tuple(sorted(node.justification_ids + (justification_id,))),
        )
        return True

    @staticmethod
    def _justification_id(
        *,
        antecedent_ids: tuple[str, ...],
        consequent_id: str,
        informant: str,
    ) -> str:
        joined = ",".join(sorted(antecedent_ids))
        return f"{informant}->{consequent_id}[{joined}]"

    @staticmethod
    def _derived_node_id(concept_id: str, value: float | str) -> str:
        return f"derived:{concept_id}:{ATMSEngine._value_key(value)}"

    @staticmethod
    def _value_key(value: float | str | None) -> str:
        normalized = ATMSEngine._normalize_value(value)
        return json.dumps(normalized, sort_keys=True, separators=(",", ":"), default=str)

    @staticmethod
    def _normalize_value(value: float | str | None) -> float | str | None:
        if isinstance(value, int | float) and not isinstance(value, bool):
            return float(value)
        return value

    def _status_from_label(self, label: Label) -> ATMSNodeStatus:
        if not label.environments:
            return ATMSNodeStatus.OUT
        if EnvironmentKey(()) in label.environments:
            return ATMSNodeStatus.TRUE
        return ATMSNodeStatus.IN

    def _out_kind_for_node(
        self,
        node_id: str,
        status: ATMSNodeStatus,
    ) -> ATMSOutKind | None:
        if status != ATMSNodeStatus.OUT:
            return None
        if self._was_pruned_by_nogood(node_id):
            return ATMSOutKind.NOGOOD_PRUNED
        return ATMSOutKind.MISSING_SUPPORT

    def _support_quality_for_node(self, node: ATMSNode) -> SupportQuality:
        if node.kind != "claim":
            return SupportQuality.EXACT
        if node.label.environments:
            return SupportQuality.EXACT

        claim = _node_claim(node)
        if claim is not None:
            _label, quality = self._runtime.claim_support(claim)
            return quality
        return SupportQuality.SEMANTIC_COMPATIBLE

    def _reason_for_node(
        self,
        node: ATMSNode,
        status: ATMSNodeStatus,
        support_quality: SupportQuality,
    ) -> str:
        if status == ATMSNodeStatus.TRUE:
            return "label contains the empty environment"
        if status == ATMSNodeStatus.IN:
            return "label has surviving exact support under non-empty environments"
        if self._was_pruned_by_nogood(node.node_id):
            return "exact-support environments were pruned by nogoods"
        if node.kind != "claim":
            return "no surviving ATMS label environments"
        if support_quality == SupportQuality.CONTEXT_VISIBLE_ONLY:
            return "active only via context visibility; no exact ATMS label"
        if support_quality == SupportQuality.MIXED:
            return "active via mixed semantic/context activation; no exact ATMS label"
        if support_quality == SupportQuality.SEMANTIC_COMPATIBLE:
            return "active only via semantic compatibility; no exact ATMS label"
        if node.justification_ids:
            return "exact justifications exist but no surviving label environments"
        return "no exact ATMS justification produced a label"

    def _was_pruned_by_nogood(self, node_id: str, _visited: set[str] | None = None) -> bool:
        node = self._nodes[node_id]
        if node.label.environments:
            return False
        if _visited is None:
            _visited = set()
        if node_id in _visited:
            return False
        _visited.add(node_id)
        for justification_id in node.justification_ids:
            justification = self._justifications[justification_id]
            # Direct check: would the cross-product be non-empty without nogoods?
            raw = self._justification_candidate_label(justification, nogoods=None)
            pruned = self._justification_candidate_label(justification, nogoods=self.nogoods)
            if raw.environments and not pruned.environments:
                return True
            # Transitive check: is any empty-label antecedent itself nogood-pruned?
            for antecedent_id in justification.antecedent_ids:
                antecedent = self._nodes[antecedent_id]
                if not antecedent.label.environments:
                    if self._was_pruned_by_nogood(antecedent_id, _visited):
                        return True
        return False

    def _justification_candidate_label(
        self,
        justification: ATMSJustification,
        *,
        nogoods: NogoodSet | None,
    ) -> Label:
        antecedent_labels: list[Label] = []
        for antecedent_id in justification.antecedent_ids:
            antecedent = self._nodes[antecedent_id]
            if not antecedent.label.environments:
                return Label(())
            antecedent_labels.append(antecedent.label)
        return combine_labels(*antecedent_labels, nogoods=nogoods)

    def _expected_label_for_node(self, node_id: str) -> Label:
        node = self._nodes[node_id]
        if node.kind == "assumption":
            assumption = _node_assumption(node)
            if assumption is not None:
                return Label.singleton(assumption)
            return Label(())

        candidates = [
            self._justification_candidate_label(self._justifications[justification_id], nogoods=self.nogoods)
            for justification_id in node.justification_ids
        ]
        return merge_labels(candidates, nogoods=self.nogoods)

    def _bound_environment_key(self) -> EnvironmentKey:
        return EnvironmentKey(
            tuple(
                assumption.assumption_id
                for assumption in self._runtime.environment.assumptions
            )
        )

    def _coerce_queryables(
        self,
        queryables: Sequence[QueryableAssumption],
    ) -> tuple[QueryableAssumption, ...]:
        current_ids = {
            str(assumption.assumption_id)
            for assumption in self._runtime.environment.assumptions
        }
        current_cels = {
            assumption.cel
            for assumption in self._runtime.environment.assumptions
        }
        normalized: dict[tuple[str, QueryableId], QueryableAssumption] = {}
        for queryable in queryables:
            candidate = queryable
            if str(candidate.assumption_id) in current_ids or candidate.cel in current_cels:
                continue
            normalized[(candidate.cel, candidate.assumption_id)] = candidate
        return tuple(
            normalized[key]
            for key in sorted(normalized)
        )

    def _iter_future_queryable_sets(
        self,
        queryables: Sequence[QueryableAssumption],
        limit: int,
    ):
        if limit <= 0:
            return
        normalized = self._coerce_queryables(queryables)
        count = 0
        for width in range(1, len(normalized) + 1):
            for queryable_set in combinations(normalized, width):
                yield queryable_set
                count += 1
                if count >= limit:
                    return

    def _future_engine(
        self,
        queryable_set: tuple[QueryableAssumption, ...],
    ) -> ATMSEngine:
        return self.__class__(self._runtime.replay(queryable_set))

    def _future_entries(
        self,
        queryables: Sequence[QueryableAssumption],
        limit: int,
    ) -> list[_FutureReplay]:
        entries: list[_FutureReplay] = []
        for queryable_set in self._iter_future_queryable_sets(queryables, limit):
            future_engine = self._future_engine(queryable_set)
            environment_key = future_engine._bound_environment_key()
            entries.append(_FutureReplay(
                queryable_ids=tuple(queryable.assumption_id for queryable in queryable_set),
                queryable_cels=tuple(queryable.cel for queryable in queryable_set),
                environment_key=environment_key,
                consistent=not future_engine.nogoods.excludes(environment_key),
                future_engine=future_engine,
            ))
        return entries

    def _concept_future_entries(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int,
    ) -> list[ATMSConceptFutureStatusEntry]:
        futures: list[ATMSConceptFutureStatusEntry] = []
        for future in self._future_entries(queryables, limit):
            future_engine = future.future_engine
            futures.append({
                "queryable_ids": _queryable_id_list(future.queryable_ids),
                "queryable_cels": list(future.queryable_cels),
                "environment": _assumption_id_list(future.environment_key.assumption_ids),
                "consistent": future.consistent,
                "status": future_engine._runtime.concept_status(concept_id),
                "supported_claim_ids": _claim_id_list(future_engine.supported_claim_ids(concept_id)),
            })
        return futures

    @staticmethod
    def _minimal_future_entries(entries: list[_FutureEntryT]) -> list[_FutureEntryT]:
        ordered = sorted(
            entries,
            key=lambda entry: (
                len(entry["queryable_ids"]),
                tuple(entry["queryable_ids"]),
            ),
        )
        minimal: list[_FutureEntryT] = []
        minimal_sets: list[set[QueryableId]] = []
        for entry in ordered:
            queryable_set = set(entry["queryable_ids"])
            if any(existing.issubset(queryable_set) for existing in minimal_sets):
                continue
            minimal.append(entry)
            minimal_sets.append(queryable_set)
        return minimal

    def _node_relevance_states(
        self,
        node_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int,
    ) -> dict[tuple[QueryableId, ...], ATMSNodeRelevanceState]:
        current = self.node_status(node_id)
        states: dict[tuple[QueryableId, ...], ATMSNodeRelevanceState] = {
            (): {
                "queryable_ids": [],
                "queryable_cels": [],
                "environment": _assumption_id_list(self._bound_environment_key().assumption_ids),
                "consistent": not self.nogoods.excludes(self._bound_environment_key()),
                "status": current.status,
            }
        }
        for future in self.node_future_statuses(node_id, queryables, limit=limit)["futures"]:
            key = tuple(future["queryable_ids"])
            states[key] = {
                "queryable_ids": _queryable_id_list(future["queryable_ids"]),
                "queryable_cels": list(future["queryable_cels"]),
                "environment": _assumption_id_list(future["environment"]),
                "consistent": future["consistent"],
                "status": future["status"],
            }
        return states

    def _concept_relevance_states(
        self,
        concept_id: str,
        queryables: Sequence[QueryableAssumption],
        limit: int,
    ) -> dict[tuple[QueryableId, ...], ATMSConceptRelevanceState]:
        states: dict[tuple[QueryableId, ...], ATMSConceptRelevanceState] = {
            (): {
                "queryable_ids": [],
                "queryable_cels": [],
                "environment": _assumption_id_list(self._bound_environment_key().assumption_ids),
                "consistent": not self.nogoods.excludes(self._bound_environment_key()),
                "status": self._runtime.concept_status(concept_id),
            }
        }
        for future in self._concept_future_entries(concept_id, queryables, limit=limit):
            key = tuple(future["queryable_ids"])
            states[key] = {
                "queryable_ids": _queryable_id_list(future["queryable_ids"]),
                "queryable_cels": list(future["queryable_cels"]),
                "environment": _assumption_id_list(future["environment"]),
                "consistent": future["consistent"],
                "status": future["status"],
            }
        return states

    def _node_relevance_from_states(
        self,
        states: dict[tuple[QueryableId, ...], ATMSNodeRelevanceState],
        current_status: ATMSNodeStatus,
    ) -> tuple[list[str], list[str], dict[str, list[ATMSNodeWitnessPair]]]:
        known_queryables = sorted({
            (queryable_id, queryable_cel)
            for state in states.values()
            for queryable_id, queryable_cel in zip(
                state["queryable_ids"],
                state["queryable_cels"],
                strict=True,
            )
        })
        relevant_queryables: list[str] = []
        witness_pairs: dict[str, list[ATMSNodeWitnessPair]] = {}
        for queryable_id, queryable_cel in known_queryables:
            pairs: list[ATMSNodeWitnessPair] = []
            for key, without_state in states.items():
                if queryable_id in key or not without_state["consistent"]:
                    continue
                with_key = tuple(sorted(key + (queryable_id,)))
                with_state = states.get(with_key)
                if with_state is None or not with_state["consistent"]:
                    continue
                if without_state["status"] == with_state["status"]:
                    continue
                pairs.append({
                    "queryable_id": queryable_id,
                    "queryable_cel": queryable_cel,
                    "without": {
                        "queryable_ids": _queryable_id_list(without_state["queryable_ids"]),
                        "queryable_cels": list(without_state["queryable_cels"]),
                        "environment": _assumption_id_list(without_state["environment"]),
                        "consistent": without_state["consistent"],
                        "status": without_state["status"],
                    },
                    "with": {
                        "queryable_ids": _queryable_id_list(with_state["queryable_ids"]),
                        "queryable_cels": list(with_state["queryable_cels"]),
                        "environment": _assumption_id_list(with_state["environment"]),
                        "consistent": with_state["consistent"],
                        "status": with_state["status"],
                    },
                })
            if pairs:
                relevant_queryables.append(queryable_cel)
                witness_pairs[queryable_cel] = self._minimal_node_witness_pairs(pairs)
        relevant_set = set(relevant_queryables)
        return (
            relevant_queryables,
            [
                queryable_cel
                for _queryable_id, queryable_cel in known_queryables
                if queryable_cel not in relevant_set
            ],
            witness_pairs,
        )

    @staticmethod
    def _minimal_node_witness_pairs(
        pairs: list[ATMSNodeWitnessPair],
    ) -> list[ATMSNodeWitnessPair]:
        ordered = sorted(
            pairs,
            key=lambda pair: (
                len(pair["with"]["queryable_ids"]),
                tuple(pair["with"]["queryable_ids"]),
            ),
        )
        minimal: list[ATMSNodeWitnessPair] = []
        minimal_sets: list[set[QueryableId]] = []
        for pair in ordered:
            queryable_set = set(pair["with"]["queryable_ids"])
            if any(existing.issubset(queryable_set) for existing in minimal_sets):
                continue
            minimal.append(pair)
            minimal_sets.append(queryable_set)
        return minimal

    def _concept_relevance_from_states(
        self,
        states: dict[tuple[QueryableId, ...], ATMSConceptRelevanceState],
        current_status: ValueStatus,
    ) -> tuple[list[str], list[str], dict[str, list[ATMSConceptWitnessPair]]]:
        known_queryables = sorted({
            (queryable_id, queryable_cel)
            for state in states.values()
            for queryable_id, queryable_cel in zip(
                state["queryable_ids"],
                state["queryable_cels"],
                strict=True,
            )
        })
        relevant_queryables: list[str] = []
        witness_pairs: dict[str, list[ATMSConceptWitnessPair]] = {}
        for queryable_id, queryable_cel in known_queryables:
            pairs: list[ATMSConceptWitnessPair] = []
            for key, without_state in states.items():
                if queryable_id in key or not without_state["consistent"]:
                    continue
                with_key = tuple(sorted(key + (queryable_id,)))
                with_state = states.get(with_key)
                if with_state is None or not with_state["consistent"]:
                    continue
                if without_state["status"] == with_state["status"]:
                    continue
                pairs.append({
                    "queryable_id": queryable_id,
                    "queryable_cel": queryable_cel,
                    "without": {
                        "queryable_ids": _queryable_id_list(without_state["queryable_ids"]),
                        "queryable_cels": list(without_state["queryable_cels"]),
                        "environment": _assumption_id_list(without_state["environment"]),
                        "consistent": without_state["consistent"],
                        "status": without_state["status"],
                    },
                    "with": {
                        "queryable_ids": _queryable_id_list(with_state["queryable_ids"]),
                        "queryable_cels": list(with_state["queryable_cels"]),
                        "environment": _assumption_id_list(with_state["environment"]),
                        "consistent": with_state["consistent"],
                        "status": with_state["status"],
                    },
                })
            if pairs:
                relevant_queryables.append(queryable_cel)
                witness_pairs[queryable_cel] = self._minimal_concept_witness_pairs(pairs)
        relevant_set = set(relevant_queryables)
        return (
            relevant_queryables,
            [
                queryable_cel
                for _queryable_id, queryable_cel in known_queryables
                if queryable_cel not in relevant_set
            ],
            witness_pairs,
        )

    @staticmethod
    def _minimal_concept_witness_pairs(
        pairs: list[ATMSConceptWitnessPair],
    ) -> list[ATMSConceptWitnessPair]:
        ordered = sorted(
            pairs,
            key=lambda pair: (
                len(pair["with"]["queryable_ids"]),
                tuple(pair["with"]["queryable_ids"]),
            ),
        )
        minimal: list[ATMSConceptWitnessPair] = []
        minimal_sets: list[set[QueryableId]] = []
        for pair in ordered:
            queryable_set = set(pair["with"]["queryable_ids"])
            if any(existing.issubset(queryable_set) for existing in minimal_sets):
                continue
            minimal.append(pair)
            minimal_sets.append(queryable_set)
        return minimal

    @staticmethod
    def _coerce_node_target_status(target_status: ATMSNodeStatus | str) -> ATMSNodeStatus:
        if isinstance(target_status, ATMSNodeStatus):
            normalized = target_status
        else:
            normalized = ATMSNodeStatus(str(target_status))
        if normalized not in {ATMSNodeStatus.IN, ATMSNodeStatus.OUT}:
            raise ValueError("target_status must be IN or OUT for bounded ATMS interventions")
        return normalized

    @staticmethod
    def _coerce_concept_target_status(target_status: ValueStatus) -> ValueStatus:
        normalized = coerce_value_status(target_status)
        assert normalized is not None
        return normalized

    @staticmethod
    def _future_reaches_node_target(
        future: ATMSNodeFutureStatusEntry,
        target_status: ATMSNodeStatus,
    ) -> bool:
        if future["status"] != target_status:
            return False
        if target_status == ATMSNodeStatus.OUT:
            return future.get("out_kind") == ATMSOutKind.NOGOOD_PRUNED
        return True

    def _node_intervention_plan(
        self,
        node_id: str,
        *,
        current: ATMSInspection,
        target_status: ATMSNodeStatus,
        future: ATMSNodeFutureStatusEntry,
    ) -> ATMSNodeInterventionPlan:
        return {
            "target": node_id,
            "node_id": node_id,
            "claim_id": current.claim_id,
            "current_status": current.status,
            "target_status": target_status,
            "queryable_ids": list(future["queryable_ids"]),
            "queryable_cels": list(future["queryable_cels"]),
            "environment": list(future["environment"]),
            "consistent": future["consistent"],
            "result_status": future["status"],
            "result_out_kind": future.get("out_kind"),
            "minimality_basis": "set_inclusion_over_queryable_ids",
        }

    def _concept_intervention_plan(
        self,
        concept_id: str,
        *,
        current_status: ValueStatus,
        target_status: ValueStatus,
        future: ATMSConceptFutureStatusEntry,
    ) -> ATMSConceptInterventionPlan:
        return {
            "target": concept_id,
            "concept_id": concept_id,
            "current_status": current_status,
            "target_status": target_status,
            "queryable_ids": list(future["queryable_ids"]),
            "queryable_cels": list(future["queryable_cels"]),
            "environment": list(future["environment"]),
            "consistent": future["consistent"],
            "result_status": future["status"],
            "minimality_basis": "set_inclusion_over_queryable_ids",
        }

    @staticmethod
    def _next_queryables_from_plans(
        plans: list[ATMSNodeInterventionPlan] | list[ATMSConceptInterventionPlan],
        *,
        max_suggestions: int | None,
    ) -> list[ATMSNextQuerySuggestion]:
        grouped: dict[
            tuple[QueryableId, str],
            list[ATMSNodeInterventionPlan | ATMSConceptInterventionPlan],
        ] = defaultdict(list)
        for plan in plans:
            for queryable_id, queryable_cel in zip(
                plan["queryable_ids"],
                plan["queryable_cels"],
                strict=True,
            ):
                grouped[(queryable_id, queryable_cel)].append(plan)

        suggestions: list[ATMSNextQuerySuggestion] = []
        for (queryable_id, queryable_cel), containing_plans in grouped.items():
            suggestions.append({
                "queryable_id": queryable_id,
                "queryable_cel": queryable_cel,
                "plan_count": len(containing_plans),
                "smallest_plan_size": min(
                    len(plan["queryable_ids"])
                    for plan in containing_plans
                ),
                "plan_queryable_cels": [
                    list(plan["queryable_cels"])
                    for plan in containing_plans
                ],
                "example_plans": containing_plans[:2],
            })
        suggestions.sort(
            key=lambda suggestion: (
                suggestion["smallest_plan_size"],
                -suggestion["plan_count"],
                suggestion["queryable_cel"],
            )
        )
        if max_suggestions is not None:
            return suggestions[:max_suggestions]
        return suggestions

    def _future_node_inspection(
        self,
        node_id: str,
        *,
        fallback: ATMSNode | None,
    ) -> ATMSInspection:
        if node_id in self._nodes:
            return self.node_status(node_id)
        support_quality = (
            SupportQuality.EXACT
            if fallback is None or fallback.kind != "claim"
            else self._support_quality_for_node(fallback)
        )
        return ATMSInspection(
            node_id=node_id,
            claim_id=None if fallback is None else _node_claim_id(fallback),
            kind=None if fallback is None else fallback.kind,
            status=ATMSNodeStatus.OUT,
            support_quality=support_quality,
            label=None,
            essential_support=None,
            reason="node absent from future ATMS view",
            out_kind=ATMSOutKind.MISSING_SUPPORT,
        )

    @staticmethod
    def _coerce_environment_key(
        environment: EnvironmentKey | tuple[AssumptionId, ...] | list[AssumptionId] | tuple[str, ...] | list[str],
    ) -> EnvironmentKey:
        if isinstance(environment, EnvironmentKey):
            return environment
        return EnvironmentKey(to_assumption_ids(environment))

    def _explain_justification(
        self,
        justification_id: str,
        *,
        seen_nodes: set[str],
    ) -> ATMSJustificationExplanation | None:
        justification = self._justifications[justification_id]
        candidate = self._justification_candidate_label(justification, nogoods=self.nogoods)
        consequent = self._nodes[justification.consequent_ids[0]]
        if not candidate.environments:
            return None
        if consequent.label.environments and not any(
            environment in consequent.label.environments
            for environment in candidate.environments
        ):
            return None

        antecedents: list[ATMSExplanationAntecedent] = []
        for antecedent_id in justification.antecedent_ids:
            antecedent_node = self._nodes[antecedent_id]
            if antecedent_id in seen_nodes:
                cycle_antecedent: ATMSCycleAntecedent = {
                    "node_id": antecedent_id,
                    "kind": antecedent_node.kind,
                    "cycle": True,
                }
                antecedents.append(cycle_antecedent)
                continue
            if antecedent_node.kind == "assumption":
                assumption_antecedent: ATMSAssumptionAntecedent = {
                    "node_id": antecedent_id,
                    "kind": antecedent_node.kind,
                    "label": self._serialize_label(self._label_or_none(antecedent_node.label)),
                }
                antecedents.append(assumption_antecedent)
                continue

            nested_seen = set(seen_nodes)
            nested_seen.add(antecedent_id)
            nested_explanation: ATMSNestedNodeExplanation = {
                **self._explain_node(antecedent_id, seen_nodes=nested_seen),
                "antecedent_of": justification.consequent_ids[0],
            }
            antecedents.append(nested_explanation)

        return {
            "node_id": consequent.node_id,
            "justification_id": justification.justification_id,
            "antecedent_ids": list(justification.antecedent_ids),
            "consequent_id": justification.consequent_ids[0],
            "informant": justification.informant,
            "support": self._serialize_label(candidate),
            "antecedents": antecedents,
        }

    def _explain_node(
        self,
        node_id: str,
        *,
        seen_nodes: set[str],
    ) -> ATMSNodeExplanation:
        node = self._nodes.get(node_id)
        if node is None:
            raise KeyError(f"Unknown ATMS node: {node_id}")

        inspection = self.node_status(node_id)
        traces = [
            trace
            for justification_id in node.justification_ids
            if (trace := self._explain_justification(justification_id, seen_nodes=seen_nodes)) is not None
        ]
        return {
            "node_id": node_id,
            "claim_id": inspection.claim_id,
            "kind": node.kind,
            "status": inspection.status.value,
            "support_quality": inspection.support_quality.value,
            "label": self._serialize_label(inspection.label),
            "essential_support": self._serialize_environment_key(inspection.essential_support),
            "reason": inspection.reason,
            "traces": traces,
        }

    @staticmethod
    def _serialize_environment_key(environment: EnvironmentKey | None) -> list[str] | None:
        if environment is None:
            return None
        return list(environment.assumption_ids)

    @classmethod
    def _serialize_label(cls, label: Label | None) -> list[list[str]] | None:
        if label is None:
            return None
        return [
            cls._serialize_environment_key(environment) or []
            for environment in label.environments
        ]

    def _serialize_nogood_detail(self, environment: EnvironmentKey) -> ATMSNogoodDetail:
        return {
            "environment": list(environment.assumption_ids),
            "provenance": list(self._nogood_provenance.get(environment, ())),
        }

    @classmethod
    def _serialize_inspection(cls, inspection: ATMSInspection) -> dict[str, Any]:
        return {
            "node_id": inspection.node_id,
            "claim_id": inspection.claim_id,
            "kind": inspection.kind,
            "status": inspection.status.value,
            "support_quality": inspection.support_quality.value,
            "label": cls._serialize_label(inspection.label),
            "essential_support": cls._serialize_environment_key(inspection.essential_support),
            "reason": inspection.reason,
            "out_kind": None if inspection.out_kind is None else inspection.out_kind.value,
        }

    @classmethod
    def _serialize_future_report(cls, report: ATMSFutureStatusReport) -> dict[str, Any]:
        return {
            "node_id": report["node_id"],
            "claim_id": report["claim_id"],
            "current": cls._serialize_inspection(report["current"]),
            "could_become_in": report["could_become_in"],
            "could_become_out": report["could_become_out"],
            "futures": [
                {
                    "queryable_ids": list(future["queryable_ids"]),
                    "queryable_cels": list(future["queryable_cels"]),
                    "environment": list(future["environment"]),
                    "consistent": future["consistent"],
                    "status": future["status"].value,
                    "out_kind": None if future["out_kind"] is None else future["out_kind"].value,
                    "reason": future["reason"],
                    "support_quality": future["support_quality"].value,
                    "essential_support": list(future["essential_support"]),
                }
                for future in report["futures"]
            ],
            "future_in": [
                list(future["queryable_cels"])
                for future in report["futures"]
                if future["status"] != ATMSNodeStatus.OUT
            ],
            "future_out": [
                list(future["queryable_cels"])
                for future in report["futures"]
                if future["status"] == ATMSNodeStatus.OUT
            ],
        }

    @classmethod
    def _serialize_why_out(cls, report: ATMSWhyOutReport) -> dict[str, Any]:
        return {
            "node_id": report["node_id"],
            "claim_id": report["claim_id"],
            "status": report["status"].value,
            "out_kind": None if report["out_kind"] is None else report["out_kind"].value,
            "reason": report["reason"],
            "support_quality": report["support_quality"].value,
            "future_activatable": report["future_activatable"],
            "candidate_queryable_cels": [
                list(queryable_set)
                for queryable_set in report["candidate_queryable_cels"]
            ],
        }

    @classmethod
    def _serialize_future_entry(
        cls,
        future: ATMSNodeFutureStatusEntry | ATMSConceptFutureStatusEntry,
    ) -> dict[str, Any]:
        result = {
            "queryable_ids": list(future["queryable_ids"]),
            "queryable_cels": list(future["queryable_cels"]),
            "environment": list(future["environment"]),
            "consistent": future["consistent"],
            "status": (
                future["status"].value
                if isinstance(future["status"], (ATMSNodeStatus, ValueStatus))
                else future["status"]
            ),
        }
        if "out_kind" in future:
            result["out_kind"] = (
                None
                if future["out_kind"] is None
                else future["out_kind"].value
            )
        if "reason" in future:
            result["reason"] = future["reason"]
        if "support_quality" in future:
            result["support_quality"] = future["support_quality"].value
        if "essential_support" in future:
            result["essential_support"] = list(future["essential_support"])
        if "supported_claim_ids" in future:
            result["supported_claim_ids"] = list(future["supported_claim_ids"])
        return result

    @staticmethod
    def _serialize_relevance_state(
        state: ATMSNodeRelevanceState | ATMSConceptRelevanceState,
    ) -> dict[str, Any]:
        return {
            "queryable_ids": list(state["queryable_ids"]),
            "queryable_cels": list(state["queryable_cels"]),
            "environment": list(state["environment"]),
            "consistent": state["consistent"],
            "status": (
                state["status"].value
                if isinstance(state["status"], (ATMSNodeStatus, ValueStatus))
                else state["status"]
            ),
        }

    @classmethod
    def _serialize_stability_report(
        cls,
        report: ATMSNodeStabilityReport | ATMSConceptStabilityReport,
    ) -> dict[str, Any]:
        serialized = {
            "stable": report["stable"],
            "limit": report["limit"],
            "future_count": report["future_count"],
            "consistent_future_count": report["consistent_future_count"],
            "inconsistent_future_count": report["inconsistent_future_count"],
            "witnesses": [
                cls._serialize_future_entry(witness)
                for witness in report["witnesses"]
            ],
        }
        if "node_id" in report:
            serialized["node_id"] = report["node_id"]
            serialized["claim_id"] = report["claim_id"]
            serialized["current"] = cls._serialize_inspection(report["current"])
        if "concept_id" in report:
            serialized["concept_id"] = report["concept_id"]
            serialized["current_status"] = report["current_status"].value
        return serialized

    @classmethod
    def _serialize_relevance_report(
        cls,
        report: ATMSNodeRelevanceReport | ATMSConceptRelevanceReport,
    ) -> dict[str, Any]:
        serialized = {
            "relevant_queryables": list(report["relevant_queryables"]),
            "irrelevant_queryables": list(report["irrelevant_queryables"]),
            "witness_pairs": {
                queryable_cel: [
                    {
                        "queryable_id": pair["queryable_id"],
                        "queryable_cel": pair["queryable_cel"],
                        "without": cls._serialize_relevance_state(pair["without"]),
                        "with": cls._serialize_relevance_state(pair["with"]),
                    }
                    for pair in pairs
                ]
                for queryable_cel, pairs in report["witness_pairs"].items()
            },
        }
        if "node_id" in report:
            serialized["node_id"] = report["node_id"]
            serialized["claim_id"] = report["claim_id"]
            serialized["current"] = cls._serialize_inspection(report["current"])
            serialized["current_status"] = report["current_status"].value
        if "concept_id" in report:
            serialized["concept_id"] = report["concept_id"]
            serialized["current_status"] = report["current_status"].value
        return serialized

    @classmethod
    def _serialize_intervention_plan(
        cls,
        plan: ATMSNodeInterventionPlan | ATMSConceptInterventionPlan,
    ) -> dict[str, Any]:
        serialized = {
            "target": plan["target"],
            "queryable_ids": list(plan["queryable_ids"]),
            "queryable_cels": list(plan["queryable_cels"]),
            "environment": list(plan["environment"]),
            "consistent": plan["consistent"],
            "minimality_basis": plan["minimality_basis"],
        }
        if "node_id" in plan:
            serialized["node_id"] = plan["node_id"]
            serialized["claim_id"] = plan["claim_id"]
            serialized["current_status"] = plan["current_status"].value
            serialized["target_status"] = plan["target_status"].value
            serialized["result_status"] = plan["result_status"].value
            serialized["result_out_kind"] = (
                None
                if plan["result_out_kind"] is None
                else plan["result_out_kind"].value
            )
        if "concept_id" in plan:
            serialized["concept_id"] = plan["concept_id"]
            serialized["current_status"] = plan["current_status"].value
            serialized["target_status"] = plan["target_status"].value
            serialized["result_status"] = plan["result_status"].value
        return serialized

    @classmethod
    def _serialize_next_query_suggestion(
        cls,
        suggestion: ATMSNextQuerySuggestion,
    ) -> dict[str, Any]:
        return {
            "queryable_id": suggestion["queryable_id"],
            "queryable_cel": suggestion["queryable_cel"],
            "plan_count": suggestion["plan_count"],
            "smallest_plan_size": suggestion["smallest_plan_size"],
            "plan_queryable_cels": [
                list(plan_queryables)
                for plan_queryables in suggestion["plan_queryable_cels"]
            ],
            "example_plans": [
                cls._serialize_intervention_plan(plan)
                for plan in suggestion["example_plans"]
            ],
        }

    @staticmethod
    def _label_or_none(label: Label) -> Label | None:
        if not label.environments:
            return None
        return label
