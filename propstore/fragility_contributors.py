"""Typed fragility contributors by intervention family."""

from __future__ import annotations

import json
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from argumentation.aspic import Rule, top_rule
from argumentation.datalog_grounding import GroundRuleOrigin
from propstore.aspic_bridge.build import build_bridge_csaf, compile_bridge_context
from propstore.aspic_bridge.extract import _extract_justifications, _extract_stance_rows
from propstore.aspic_bridge.grounding import (
    _decode_grounded_predicate,
    project_grounded_rules,
)
from propstore.fragility_scoring import (
    FragilityWarning,
    score_conflict,
    support_derivative_fragility,
)
from propstore.fragility_types import (
    AssumptionTarget,
    BridgeUndercutTarget,
    ConflictTarget,
    FragilityWorld,
    GroundFactTarget,
    GroundedRuleTarget,
    InterventionFamily,
    InterventionKind,
    InterventionProvenance,
    InterventionTarget,
    MissingMeasurementTarget,
    RankedIntervention,
    RankingPolicy,
)
from propstore.grounding.gunray_complement import GUNRAY_COMPLEMENT_ENCODER
from propstore.provenance import (
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
    derivation_count,
    partial_derivative,
)
from propstore.world.types import QueryableAssumption, ValueStatus


_ASSUMPTION_VAR_PREFIX = "ps:source:assumption:"


@dataclass
class _AssumptionContribution:
    queryable: QueryableAssumption
    concepts: set[str]
    witness_count: int
    consistent_future_count: int
    max_score: float
    support: SupportEvidence


@dataclass
class _ConflictContribution:
    concepts: set[str]
    max_score: float


def _queryable_source_variable(queryable: QueryableAssumption) -> SourceVariableId:
    return SourceVariableId(f"{_ASSUMPTION_VAR_PREFIX}{queryable.assumption_id}")


def _witness_support_polynomial(
    witnesses: Sequence[object],
    queryables: Sequence[QueryableAssumption],
) -> ProvenancePolynomial:
    queryable_by_cel = {str(queryable.cel): queryable for queryable in queryables}
    support = ProvenancePolynomial.zero()
    for witness in witnesses:
        q_cels = getattr(witness, "queryable_cels", ())
        monomial = ProvenancePolynomial.one()
        for qcel in q_cels:
            queryable = queryable_by_cel.get(
                str(qcel), QueryableAssumption.from_cel(str(qcel))
            )
            monomial = monomial * ProvenancePolynomial.variable(
                _queryable_source_variable(queryable)
            )
        support = support + monomial
    return support


def _support_queryables(
    witnesses: Sequence[object],
    queryables: Sequence[QueryableAssumption],
) -> tuple[QueryableAssumption, ...]:
    queryable_by_cel = {str(queryable.cel): queryable for queryable in queryables}
    for witness in witnesses:
        for qcel in getattr(witness, "queryable_cels", ()):
            queryable_by_cel.setdefault(
                str(qcel), QueryableAssumption.from_cel(str(qcel))
            )
    return tuple(
        sorted(queryable_by_cel.values(), key=lambda item: str(item.assumption_id))
    )


def _typed_scalar_key(value: object) -> dict[str, object]:
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": value}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    return {"type": "str", "value": str(value)}


def _typed_row_key(row: Sequence[object]) -> str:
    return json.dumps(
        [_typed_scalar_key(item) for item in row],
        sort_keys=True,
        separators=(",", ":"),
    )


def _typed_substitution_key(substitution: Sequence[tuple[str, object]]) -> str:
    return json.dumps(
        {
            name: _typed_scalar_key(value)
            for name, value in sorted(substitution, key=lambda item: item[0])
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _in_extension(current_status: object) -> bool:
    try:
        normalized = ValueStatus(str(current_status))
    except ValueError as exc:
        raise ValueError(
            f"Unknown value status for extension membership: {current_status!r}"
        ) from exc
    return normalized in {
        ValueStatus.DETERMINED,
        ValueStatus.DERIVED,
        ValueStatus.RESOLVED,
    }


def _parameterizations_to_queryables(
    bound: FragilityWorld,
) -> tuple[QueryableAssumption, ...]:
    queryables: set[QueryableAssumption] = set()
    for parameterization in bound._store.all_parameterizations():
        if not parameterization.conditions_cel:
            continue
        decoded = json.loads(parameterization.conditions_cel)
        if isinstance(decoded, str):
            queryables.add(QueryableAssumption.from_cel(decoded))
            continue
        for item in decoded:
            if isinstance(item, str):
                queryables.add(QueryableAssumption.from_cel(item))
    return tuple(sorted(queryables))


def derive_scored_concepts(bound: FragilityWorld) -> list[str]:
    try:
        concepts: set[str] = {
            str(row.output_concept_id) for row in bound._store.all_parameterizations()
        }
        for claim in bound.active_claims():
            if hasattr(claim, "value_concept_id"):
                concept_id = getattr(claim, "value_concept_id")
                if concept_id is not None:
                    concepts.add(str(concept_id))
            elif isinstance(claim, Mapping):
                concept_id = claim.get(
                    "value_concept_id", claim.get("output_concept_id")
                )
                if concept_id is not None:
                    concepts.add(str(concept_id))
        return sorted(concepts)
    except Exception as exc:
        warnings.warn(
            f"Fragility concept discovery failed: {exc}",
            FragilityWarning,
            stacklevel=2,
        )
        return []


_SECTION_FRAGILITY = {
    "yes": 0.75,
    "no": 0.5,
    "undecided": 1.0,
    "unknown": 1.0,
}


def _coefficient_provenance_notes(*, formula: str, citation: str) -> tuple[str, ...]:
    return (
        "status=vacuous; "
        f"fragility coefficient heuristic; formula={formula}; citation={citation}",
    )


def build_bound_bridge_inputs(bound: FragilityWorld):
    active_claims = tuple(bound.active_claims())
    active_by_id = {str(claim.id): claim for claim in active_claims}
    active_graph = getattr(bound, "_active_graph", None)
    stance_rows = _extract_stance_rows(
        bound._store, active_by_id, active_graph=active_graph
    )
    justifications = _extract_justifications(
        bound._store,
        active_by_id,
        stance_rows,
        active_graph=active_graph,
    )
    return active_claims, justifications, stance_rows
