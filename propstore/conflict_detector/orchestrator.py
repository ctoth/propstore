"""Top-level conflict detection orchestration.

Builds a condition-ir registry augmented with synthetic runtime bindings (so the
solver treats different source papers as disjoint enum values), then fans out to
the parameter, measurement, equation, and algorithm detectors. Every detected
relationship becomes a :class:`ConflictRecord` with provenance; nothing is
dropped or aborted.

The single-hop parameterization-derivation detector is wired in here over the
``by_concept`` partition the direct parameter detector already builds. Its SymPy
numeric evaluation is delegated to the ``human-to-sympy`` substrate, so propstore
never imports SymPy. The multi-hop :func:`detect_transitive_conflicts` is a
standalone public entry (it walks parameterization components), not run as part of
this orchestration.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from condition_ir import (
    ConceptInfo,
    ConditionSolver,
    check_condition_ir,
    checked_condition_set,
    synthetic_category_concept,
    to_cel_expr,
    to_cel_exprs,
    with_synthetic_concepts,
)

from propstore.core.graph_types import ParameterizationEdge
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition

from .algorithms import detect_algorithm_conflicts
from .equations import detect_equation_conflicts
from .measurements import detect_measurement_conflicts
from .models import ConflictClaim, ConflictRecord
from .parameter_claims import detect_parameter_conflicts
from .parameterization_conflicts import detect_parameterization_conflicts

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem
    from propstore.families.contexts import LiftingRule


# The synthetic runtime binding vocabulary is propstore-owned: these names are
# part of the runtime environment contract, not of CEL parsing/type-checking.
STANDARD_SYNTHETIC_BINDING_NAMES: tuple[str, ...] = (
    "source",
    "domain",
    "source_kind",
    "origin_type",
    "name",
    "framework",
    "mode",
    "variant",
)


class SyntheticConceptCollision(ValueError):
    """Raised when a synthetic CEL concept would shadow an authored concept."""


def _empty_decisions() -> dict[tuple[str, str, str, tuple[str, ...]], bool]:
    return {}


@dataclass
class LiftingDecisionCache:
    decisions: dict[tuple[str, str, str, tuple[str, ...]], bool] = field(
        default_factory=_empty_decisions
    )


def detect_conflicts(
    claims: Sequence[ConflictClaim],
    concepts: Mapping[str, Concept],
    cel_registry: Mapping[str, ConceptInfo],
    lifting_system: LiftingSystem | None = None,
    *,
    forms: Mapping[str, FormDefinition] | None = None,
    parameterizations: Mapping[str, Sequence[ParameterizationEdge]] | None = None,
) -> list[ConflictRecord]:
    """Detect conflicts between claims binding to the same concept.

    ``concepts`` / ``forms`` / ``parameterizations`` are the canonical typed
    inputs (charter documents and graph edges); unit-aware comparison and
    parameterization derivation run exactly when the caller supplies them.
    """

    records: list[ConflictRecord] = []

    source_names = sorted(
        {claim.source_paper for claim in claims if claim.source_paper}
    )
    synthetic_concepts: list[ConceptInfo] = [
        synthetic_category_concept(
            concept_id="ps:concept:__source__",
            canonical_name="source",
            values=source_names,
            extensible=False,
        )
    ]
    for synthetic_name in STANDARD_SYNTHETIC_BINDING_NAMES:
        if synthetic_name == "source":
            continue
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
    registry = with_synthetic_concepts(cel_registry, synthetic_concepts)
    condition_solver = ConditionSolver(registry)

    expanded_claims = _expand_lifted_conflict_claims(
        claims,
        cel_registry=registry,
        lifting_system=lifting_system,
        solver=condition_solver,
    )

    parameter_records, by_concept = detect_parameter_conflicts(
        expanded_claims,
        registry,
        lifting_system=lifting_system,
        solver=condition_solver,
        forms=forms,
        concept_forms=_concept_form_names(concepts),
    )
    records.extend(parameter_records)
    records.extend(
        detect_measurement_conflicts(
            expanded_claims,
            registry,
            lifting_system=lifting_system,
            solver=condition_solver,
        )
    )
    records.extend(
        detect_equation_conflicts(
            expanded_claims,
            registry,
            lifting_system=lifting_system,
            solver=condition_solver,
        )
    )
    records.extend(
        detect_algorithm_conflicts(
            expanded_claims,
            registry,
            lifting_system=lifting_system,
            solver=condition_solver,
        )
    )
    records.extend(
        detect_parameterization_conflicts(
            by_concept,
            concepts,
            parameterizations if parameterizations is not None else {},
            expanded_claims,
            lifting_system=lifting_system,
            forms=forms,
        )
    )
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
                f"synthetic CEL concept '{concept.canonical_name}' would shadow "
                f"{existing.id}"
            )


def _expand_lifted_conflict_claims(
    claims: Sequence[ConflictClaim],
    *,
    cel_registry: Mapping[str, ConceptInfo],
    lifting_system: LiftingSystem | None,
    solver: ConditionSolver | None,
) -> list[ConflictClaim]:
    if lifting_system is None or not claims:
        return list(claims)

    rules_by_source: dict[str, list[LiftingRule]] = defaultdict(list)
    for rule in lifting_system.lifting_rules:
        rules_by_source[rule.source_context].append(rule)
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
    queue = list(claims)
    while queue:
        claim = queue.pop(0)
        if claim.context_id is None:
            continue
        for rule in rules_by_source.get(claim.context_id, ()):
            decision_key = (
                claim.claim_id,
                rule.source_context,
                rule.target_context,
                tuple(str(condition) for condition in claim.conditions),
            )
            applies = cache.decisions.get(decision_key)
            if applies is None:
                applies = _lifting_rule_applies(claim, rule, solver, cel_registry)
                cache.decisions[decision_key] = applies
            if not applies:
                continue
            target_id = rule.target_context
            target_conditions = to_cel_exprs(
                lifting_system.effective_assumptions(target_id)
            )
            if not target_conditions and rule.conditions:
                target_conditions = to_cel_exprs(rule.conditions)
            if not target_conditions:
                continue
            key = (
                claim.claim_id,
                target_id,
                target_conditions,
                _claim_derivation_chain(claim),
            )
            if key in seen:
                continue
            seen.add(key)
            lifted_claim = replace(
                claim,
                context_id=target_id,
                conditions=target_conditions,
            )
            expanded.append(lifted_claim)
            queue.append(lifted_claim)
    return expanded


def _claim_derivation_chain(claim: ConflictClaim) -> tuple[str, ...]:
    # Plain conflict claims carry no derivation chain; only the deferred
    # parameterization-derived detector produces one. The key slot is kept so
    # lifted-claim deduplication stays stable when that detector lands.
    _ = claim
    return ()


def _lifting_rule_applies(
    claim: ConflictClaim,
    rule: LiftingRule,
    solver: ConditionSolver | None,
    cel_registry: Mapping[str, ConceptInfo],
) -> bool:
    if not rule.conditions:
        return True
    if solver is None:
        return all(
            to_cel_expr(condition) in claim.conditions for condition in rule.conditions
        )
    return solver.implies(
        checked_condition_set(
            check_condition_ir(str(condition), cel_registry)
            for condition in claim.conditions
        ),
        checked_condition_set(
            check_condition_ir(str(condition), cel_registry)
            for condition in rule.conditions
        ),
    )


def _concept_form_names(concepts: Mapping[str, Concept]) -> dict[str, str]:
    """Concept id → physical-dimension form name, read off the charter."""

    concept_forms: dict[str, str] = {}
    for concept_id, concept in concepts.items():
        entry = concept.lexical_entry
        if entry is None or entry.physical_dimension_form is None:
            continue
        concept_forms.setdefault(concept_id, entry.physical_dimension_form)
        concept_forms.setdefault(concept.concept_id, entry.physical_dimension_form)
    return concept_forms
