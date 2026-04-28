"""Top-level conflict detection orchestration."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from propstore.cel_checker import (
    ConceptInfo,
    synthetic_category_concept,
    with_synthetic_concepts,
)
from propstore.core.id_types import to_context_id

from .algorithms import detect_algorithm_conflicts
from .equations import detect_equation_conflicts
from .measurements import detect_measurement_conflicts
from .models import ConflictClaim, ConflictRecord
from .parameter_claims import detect_parameter_conflicts
from .parameterization_conflicts import _detect_parameterization_conflicts

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingRule, LiftingSystem


class SyntheticConceptCollision(ValueError):
    """Raised when a synthetic CEL concept would shadow an authored concept."""


@dataclass
class LiftingDecisionCache:
    decisions: dict[tuple[str, str, str | None], bool] = field(default_factory=dict)


def detect_conflicts(
    claims: Sequence[ConflictClaim],
    concept_registry: dict[str, dict],
    cel_registry: Mapping[str, ConceptInfo],
    lifting_system: LiftingSystem | None = None,
) -> list[ConflictRecord]:
    """Detect conflicts between claims binding to the same concept."""
    records: list[ConflictRecord] = []
    _validate_conflict_concept_registry(concept_registry)
    # Inject a synthetic 'source' category so Z3 treats source conditions
    # as enum comparisons and recognizes different papers as disjoint.
    source_name_set: set[str] = set()
    for claim in claims:
        if claim.source_paper:
            source_name_set.add(claim.source_paper)
    source_names = sorted(source_name_set)
    synthetic_concepts = [
        synthetic_category_concept(
            concept_id="ps:concept:__source__",
            canonical_name="source",
            values=source_names,
            extensible=False,
        ),
    ]
    for synthetic_name in ("domain", "source_kind", "origin_type", "name"):
        if synthetic_name in cel_registry:
            continue
        synthetic_concepts.append(
            synthetic_category_concept(
                concept_id=f"ps:concept:__{synthetic_name}__",
                canonical_name=synthetic_name,
                values=(),
                extensible=True,
            )
        )
    _raise_on_synthetic_collisions(cel_registry, synthetic_concepts)
    cel_registry = with_synthetic_concepts(
        cel_registry,
        synthetic_concepts,
    )
    condition_solver = _build_condition_solver(cel_registry)
    claims = _expand_lifted_conflict_claims(
        claims,
        lifting_system=lifting_system,
        solver=condition_solver,
    )

    parameter_records, by_concept = detect_parameter_conflicts(
        claims,
        cel_registry,
        lifting_system=lifting_system,
        solver=condition_solver,
    )
    records.extend(parameter_records)
    records.extend(
        detect_measurement_conflicts(
            claims,
            cel_registry,
            lifting_system=lifting_system,
            solver=condition_solver,
        )
    )
    records.extend(
        detect_equation_conflicts(
            claims,
            cel_registry,
            lifting_system=lifting_system,
            solver=condition_solver,
        )
    )
    records.extend(
        detect_algorithm_conflicts(
            claims,
            cel_registry,
            lifting_system=lifting_system,
            solver=condition_solver,
        )
    )

    records.extend(_detect_parameterization_conflicts(
        by_concept,
        concept_registry,
        claims,
        lifting_system=lifting_system,
    ))
    return records


def _raise_on_synthetic_collisions(
    cel_registry: Mapping[str, ConceptInfo],
    synthetic_concepts: Sequence[ConceptInfo],
) -> None:
    for concept in synthetic_concepts:
        existing = cel_registry.get(concept.canonical_name)
        if existing is None:
            continue
        if existing.id != concept.id:
            raise SyntheticConceptCollision(
                f"synthetic CEL concept '{concept.canonical_name}' would shadow {existing.id}"
            )


def _build_condition_solver(cel_registry):
    try:
        from propstore.z3_conditions import Z3ConditionSolver
    except ImportError:
        return None
    return Z3ConditionSolver(cel_registry)


def _expand_lifted_conflict_claims(
    claims: Sequence[ConflictClaim],
    *,
    lifting_system: LiftingSystem | None,
    solver,
) -> list[ConflictClaim]:
    if lifting_system is None or not claims:
        return list(claims)

    rules_by_source: dict[str, list[LiftingRule]] = defaultdict(list)
    for rule in lifting_system.lifting_rules:
        rules_by_source[str(rule.source.id)].append(rule)
    if not rules_by_source:
        return list(claims)

    expanded = list(claims)
    seen = {
        (
            claim.claim_id,
            claim.context_id,
            tuple(claim.conditions),
            _claim_derivation_chain(claim),
        )
        for claim in claims
    }

    cache = LiftingDecisionCache()
    for claim in claims:
        if claim.context_id is None:
            continue
        for rule in rules_by_source.get(str(claim.context_id), ()):
            decision_key = (claim.claim_id, str(rule.source.id), str(rule.target.id))
            applies = cache.decisions.get(decision_key)
            if applies is None:
                applies = _lifting_rule_applies(claim, rule, solver)
                cache.decisions[decision_key] = applies
            if not applies:
                continue
            target_id = to_context_id(rule.target.id)
            target_conditions = tuple(
                lifting_system.context_assumptions.get(target_id, ())
            )
            if not target_conditions and rule.conditions:
                target_conditions = tuple(rule.conditions)
            if not target_conditions:
                continue
            key = (
                claim.claim_id,
                str(target_id),
                target_conditions,
                _claim_derivation_chain(claim),
            )
            if key in seen:
                continue
            seen.add(key)
            expanded.append(
                replace(
                    claim,
                    context_id=str(target_id),
                    conditions=target_conditions,
                )
            )
    return expanded


def _claim_derivation_chain(claim: ConflictClaim) -> tuple[str, ...]:
    chain = getattr(claim, "derivation_chain", ())
    return tuple(str(item) for item in chain)


def _lifting_rule_applies(claim: ConflictClaim, rule: LiftingRule, solver) -> bool:
    if not rule.conditions:
        return True
    if solver is None:
        return all(condition in claim.conditions for condition in rule.conditions)
    return bool(solver.implies(claim.conditions, rule.conditions))


def _validate_conflict_concept_registry(concept_registry: dict[str, dict]) -> None:
    entries_by_id: dict[str, dict[str, object]] = {}
    for key, value in concept_registry.items():
        if not isinstance(value, dict):
            raise TypeError(
                "conflict detector CEL projection expects concept_registry values to be mappings"
            )
        concept_id = value.get("artifact_id", value.get("id"))
        if not isinstance(concept_id, str) or not concept_id:
            raise ValueError(
                f"invalid concept registry entry for key '{key}': missing artifact_id/id"
            )
        normalized = {
            str(field): field_value
            for field, field_value in value.items()
            if not str(field).startswith("_")
        }
        normalized.setdefault("artifact_id", concept_id)
        existing = entries_by_id.get(concept_id)
        if existing is not None:
            if existing != normalized:
                raise ValueError(
                    f"conflicting concept registry entries for concept id '{concept_id}'"
                )
            continue
        entries_by_id[concept_id] = normalized
