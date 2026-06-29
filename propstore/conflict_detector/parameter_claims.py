"""Direct parameter-claim conflict detection.

Compares PARAMETER claims that bind the same output concept. Values are compared
unit-aware (``value_comparison`` normalizes through ``dimensions``); the Z3 solver
partitions claims into condition-equivalence classes so within-class value
disagreements are outright conflicts and cross-class ones are classified by
disjointness. Solver translation failures are re-raised with their cause text
intact — never swallowed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from condition_ir import (
    CelExpr,
    CheckedConditionSet,
    ConceptInfo,
    ConditionSolver,
    SolverUnknown,
    SolverUnsat,
    Z3TranslationError,
    check_condition_ir,
    checked_condition_set,
)

from propstore.families.forms import FormDefinition
from propstore.value_comparison import value_str, values_compatible

from .collectors import collect_parameter_claims
from .condition_classifier import classify_conditions
from .context import append_context_classified_record, claim_context
from .models import ConflictClass, ConflictClaim, ConflictRecord

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem


def detect_parameter_conflicts(
    claims: Sequence[ConflictClaim],
    cel_registry: Mapping[str, ConceptInfo],
    *,
    lifting_system: LiftingSystem | None = None,
    solver: ConditionSolver | None = None,
    forms: Mapping[str, FormDefinition] | None = None,
    concept_forms: Mapping[str, str] | None = None,
) -> tuple[list[ConflictRecord], dict[str, list[ConflictClaim]]]:
    records: list[ConflictRecord] = []
    by_concept = collect_parameter_claims(claims)
    z3_solver = solver if solver is not None else ConditionSolver(cel_registry)

    for concept_id, concept_claims in by_concept.items():
        if len(concept_claims) < 2:
            continue

        all_conditions = [sorted(claim.conditions) for claim in concept_claims]
        checked_conditions = [
            checked_condition_set(
                check_condition_ir(str(condition), cel_registry)
                for condition in conditions
            )
            for conditions in all_conditions
        ]

        eq_classes: list[list[int]] | None
        if len(concept_claims) > 2:
            try:
                eq_classes = z3_solver.partition_equivalence_classes(checked_conditions)
            except Z3TranslationError as exc:
                raise RuntimeError(
                    f"Z3 partitioning failed during parameter conflict detection: {exc}"
                ) from exc
        else:
            eq_classes = None

        if eq_classes is None:
            _detect_pairwise_parameter_conflicts(
                records,
                concept_id,
                concept_claims,
                all_conditions,
                cel_registry,
                lifting_system=lifting_system,
                solver=z3_solver,
                forms=forms,
                concept_forms=concept_forms,
            )
            continue

        _detect_equivalent_parameter_conflicts(
            records,
            concept_id,
            concept_claims,
            all_conditions,
            eq_classes,
            lifting_system=lifting_system,
            forms=forms,
            concept_forms=concept_forms,
        )
        _detect_cross_class_parameter_conflicts(
            records,
            concept_id,
            concept_claims,
            all_conditions,
            eq_classes,
            z3_solver,
            checked_conditions,
            lifting_system=lifting_system,
        )

    return records, by_concept


def _concept_form_for(
    concept_forms: Mapping[str, str] | None, concept_id: str
) -> str | None:
    return None if concept_forms is None else concept_forms.get(concept_id)


def _detect_pairwise_parameter_conflicts(
    records: list[ConflictRecord],
    concept_id: str,
    claims: Sequence[ConflictClaim],
    all_conditions: list[list[CelExpr]],
    cel_registry: Mapping[str, ConceptInfo],
    *,
    lifting_system: LiftingSystem | None,
    solver: ConditionSolver,
    forms: Mapping[str, FormDefinition] | None,
    concept_forms: Mapping[str, str] | None,
) -> None:
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            claim_a = claims[i]
            claim_b = claims[j]
            if values_compatible(
                claim_a.value,
                claim_b.value,
                claim_a=claim_a,
                claim_b=claim_b,
                forms=forms,
                concept_form=_concept_form_for(concept_forms, concept_id),
            ):
                continue
            if append_context_classified_record(
                records,
                concept_id=concept_id,
                claim_a_id=claim_a.claim_id,
                claim_b_id=claim_b.claim_id,
                conditions_a=all_conditions[i],
                conditions_b=all_conditions[j],
                value_a=value_str(claim_a.value, claim=claim_a),
                value_b=value_str(claim_b.value, claim=claim_b),
                context_a=claim_context(claim_a),
                context_b=claim_context(claim_b),
                lifting_system=lifting_system,
            ):
                continue
            records.append(
                ConflictRecord(
                    concept_id=concept_id,
                    claim_a_id=claim_a.claim_id,
                    claim_b_id=claim_b.claim_id,
                    warning_class=classify_conditions(
                        all_conditions[i],
                        all_conditions[j],
                        cel_registry,
                        solver=solver,
                    ),
                    conditions_a=all_conditions[i],
                    conditions_b=all_conditions[j],
                    value_a=value_str(claim_a.value, claim=claim_a),
                    value_b=value_str(claim_b.value, claim=claim_b),
                )
            )


def _detect_equivalent_parameter_conflicts(
    records: list[ConflictRecord],
    concept_id: str,
    claims: Sequence[ConflictClaim],
    all_conditions: list[list[CelExpr]],
    eq_classes: list[list[int]],
    *,
    lifting_system: LiftingSystem | None,
    forms: Mapping[str, FormDefinition] | None,
    concept_forms: Mapping[str, str] | None,
) -> None:
    for group in eq_classes:
        for ii in range(len(group)):
            for jj in range(ii + 1, len(group)):
                idx_a, idx_b = group[ii], group[jj]
                claim_a = claims[idx_a]
                claim_b = claims[idx_b]
                if values_compatible(
                    claim_a.value,
                    claim_b.value,
                    claim_a=claim_a,
                    claim_b=claim_b,
                    forms=forms,
                    concept_form=_concept_form_for(concept_forms, concept_id),
                ):
                    continue
                if append_context_classified_record(
                    records,
                    concept_id=concept_id,
                    claim_a_id=claim_a.claim_id,
                    claim_b_id=claim_b.claim_id,
                    conditions_a=all_conditions[idx_a],
                    conditions_b=all_conditions[idx_b],
                    value_a=value_str(claim_a.value, claim=claim_a),
                    value_b=value_str(claim_b.value, claim=claim_b),
                    context_a=claim_context(claim_a),
                    context_b=claim_context(claim_b),
                    lifting_system=lifting_system,
                ):
                    continue
                records.append(
                    ConflictRecord(
                        concept_id=concept_id,
                        claim_a_id=claim_a.claim_id,
                        claim_b_id=claim_b.claim_id,
                        warning_class=ConflictClass.CONFLICT,
                        conditions_a=all_conditions[idx_a],
                        conditions_b=all_conditions[idx_b],
                        value_a=value_str(claim_a.value, claim=claim_a),
                        value_b=value_str(claim_b.value, claim=claim_b),
                    )
                )


def _detect_cross_class_parameter_conflicts(
    records: list[ConflictRecord],
    concept_id: str,
    claims: Sequence[ConflictClaim],
    all_conditions: list[list[CelExpr]],
    eq_classes: list[list[int]],
    z3_solver: ConditionSolver,
    checked_conditions: list[CheckedConditionSet],
    *,
    lifting_system: LiftingSystem | None,
) -> None:
    for left_index in range(len(eq_classes)):
        for right_index in range(left_index + 1, len(eq_classes)):
            group_i = eq_classes[left_index]
            group_j = eq_classes[right_index]
            rep_i = checked_conditions[group_i[0]]
            rep_j = checked_conditions[group_j[0]]
            try:
                disjointness = z3_solver.are_disjoint_result(rep_i, rep_j)
            except Z3TranslationError as exc:
                raise RuntimeError(
                    f"Z3 disjointness check failed during parameter conflict detection: {exc}"
                ) from exc
            if isinstance(disjointness, SolverUnknown):
                cross_class = ConflictClass.UNKNOWN
            elif isinstance(disjointness, SolverUnsat):
                cross_class = ConflictClass.PHI_NODE
            else:
                cross_class = ConflictClass.OVERLAP

            for idx_a in group_i:
                for idx_b in group_j:
                    claim_a = claims[idx_a]
                    claim_b = claims[idx_b]
                    if values_compatible(
                        claim_a.value,
                        claim_b.value,
                        claim_a=claim_a,
                        claim_b=claim_b,
                    ):
                        continue
                    if append_context_classified_record(
                        records,
                        concept_id=concept_id,
                        claim_a_id=claim_a.claim_id,
                        claim_b_id=claim_b.claim_id,
                        conditions_a=all_conditions[idx_a],
                        conditions_b=all_conditions[idx_b],
                        value_a=value_str(claim_a.value, claim=claim_a),
                        value_b=value_str(claim_b.value, claim=claim_b),
                        context_a=claim_context(claim_a),
                        context_b=claim_context(claim_b),
                        lifting_system=lifting_system,
                    ):
                        continue
                    records.append(
                        ConflictRecord(
                            concept_id=concept_id,
                            claim_a_id=claim_a.claim_id,
                            claim_b_id=claim_b.claim_id,
                            warning_class=cross_class,
                            conditions_a=all_conditions[idx_a],
                            conditions_b=all_conditions[idx_b],
                            value_a=value_str(claim_a.value, claim=claim_a),
                            value_b=value_str(claim_b.value, claim=claim_b),
                        )
                    )
