"""Parameter-claim conflict detection."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from propstore.claim_documents import LoadedClaimFile
from propstore.condition_classifier import classify_conditions as _classify_conditions
from propstore.value_comparison import (
    value_str as _value_str,
    values_compatible as _values_compatible,
)

from .collectors import _collect_parameter_claims
from .context import _append_context_classified_record, _claim_context
from .models import ConflictClass, ConflictClaim, ConflictRecord

if TYPE_CHECKING:
    from propstore.cel_checker import ConceptInfo
    from propstore.context_hierarchy import ContextHierarchy


def _build_z3_solver(cel_registry: dict[str, ConceptInfo]):
    try:
        from propstore.z3_conditions import Z3ConditionSolver
    except ImportError as exc:
        raise RuntimeError("Z3 condition reasoning is required but unavailable") from exc
    return Z3ConditionSolver(cel_registry)


def detect_parameter_conflicts(
    claim_files: Sequence[LoadedClaimFile],
    cel_registry: dict[str, ConceptInfo],
    *,
    context_hierarchy: ContextHierarchy | None = None,
    solver=None,
) -> tuple[list[ConflictRecord], dict[str, list[ConflictClaim]]]:
    records: list[ConflictRecord] = []
    by_concept = _collect_parameter_claims(claim_files)
    z3_solver = solver if solver is not None else _build_z3_solver(cel_registry)

    for concept_id, claims in by_concept.items():
        if len(claims) < 2:
            continue

        all_conditions = [sorted(claim.conditions) for claim in claims]

        if len(claims) > 2:
            from propstore.z3_conditions import Z3TranslationError
            import z3
            try:
                eq_classes = z3_solver.partition_equivalence_classes(all_conditions)
            except (Z3TranslationError, z3.Z3Exception) as exc:
                raise RuntimeError("Z3 partitioning failed during parameter conflict detection") from exc
        else:
            eq_classes = None

        if eq_classes is None:
            _detect_pairwise_parameter_conflicts(
                records,
                concept_id,
                claims,
                all_conditions,
                cel_registry,
                context_hierarchy=context_hierarchy,
                solver=z3_solver,
            )
            continue

        _detect_equivalent_parameter_conflicts(
            records,
            concept_id,
            claims,
            all_conditions,
            eq_classes,
            context_hierarchy=context_hierarchy,
        )
        _detect_cross_class_parameter_conflicts(
            records,
            concept_id,
            claims,
            all_conditions,
            eq_classes,
            cel_registry,
            z3_solver,
            context_hierarchy=context_hierarchy,
        )

    return records, by_concept


def _detect_pairwise_parameter_conflicts(
    records: list[ConflictRecord],
    concept_id: str,
    claims: list[ConflictClaim],
    all_conditions: list[list[str]],
    cel_registry: dict[str, ConceptInfo],
    *,
    context_hierarchy: ContextHierarchy | None,
    solver=None,
) -> None:
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            claim_a = claims[i]
            claim_b = claims[j]
            value_a = claim_a.value
            value_b = claim_b.value

            if _values_compatible(value_a, value_b, claim_a=claim_a, claim_b=claim_b):
                continue
            if _append_context_classified_record(
                records,
                concept_id=concept_id,
                claim_a_id=claim_a.claim_id,
                claim_b_id=claim_b.claim_id,
                conditions_a=all_conditions[i],
                conditions_b=all_conditions[j],
                value_a=_value_str(value_a, claim=claim_a),
                value_b=_value_str(value_b, claim=claim_b),
                context_a=_claim_context(claim_a),
                context_b=_claim_context(claim_b),
                context_hierarchy=context_hierarchy,
            ):
                continue
            records.append(ConflictRecord(
                concept_id=concept_id,
                claim_a_id=claim_a.claim_id,
                claim_b_id=claim_b.claim_id,
                warning_class=_classify_conditions(
                    all_conditions[i],
                    all_conditions[j],
                    cel_registry,
                    solver=solver,
                ),
                conditions_a=all_conditions[i],
                conditions_b=all_conditions[j],
                value_a=_value_str(value_a, claim=claim_a),
                value_b=_value_str(value_b, claim=claim_b),
            ))


def _detect_equivalent_parameter_conflicts(
    records: list[ConflictRecord],
    concept_id: str,
    claims: list[ConflictClaim],
    all_conditions: list[list[str]],
    eq_classes: list[list[int]],
    *,
    context_hierarchy: ContextHierarchy | None,
) -> None:
    for group in eq_classes:
        for ii in range(len(group)):
            for jj in range(ii + 1, len(group)):
                idx_a, idx_b = group[ii], group[jj]
                claim_a = claims[idx_a]
                claim_b = claims[idx_b]
                value_a = claim_a.value
                value_b = claim_b.value
                if _values_compatible(value_a, value_b, claim_a=claim_a, claim_b=claim_b):
                    continue
                if _append_context_classified_record(
                    records,
                    concept_id=concept_id,
                    claim_a_id=claim_a.claim_id,
                    claim_b_id=claim_b.claim_id,
                    conditions_a=all_conditions[idx_a],
                    conditions_b=all_conditions[idx_b],
                    value_a=_value_str(value_a, claim=claim_a),
                    value_b=_value_str(value_b, claim=claim_b),
                    context_a=_claim_context(claim_a),
                    context_b=_claim_context(claim_b),
                    context_hierarchy=context_hierarchy,
                ):
                    continue
                records.append(ConflictRecord(
                    concept_id=concept_id,
                    claim_a_id=claim_a.claim_id,
                    claim_b_id=claim_b.claim_id,
                    warning_class=ConflictClass.CONFLICT,
                    conditions_a=all_conditions[idx_a],
                    conditions_b=all_conditions[idx_b],
                    value_a=_value_str(value_a, claim=claim_a),
                    value_b=_value_str(value_b, claim=claim_b),
                ))


def _detect_cross_class_parameter_conflicts(
    records: list[ConflictRecord],
    concept_id: str,
    claims: list[ConflictClaim],
    all_conditions: list[list[str]],
    eq_classes: list[list[int]],
    cel_registry: dict[str, ConceptInfo],
    z3_solver,
    *,
    context_hierarchy: ContextHierarchy | None,
) -> None:
    from propstore.z3_conditions import Z3TranslationError
    import z3

    for left_index in range(len(eq_classes)):
        for right_index in range(left_index + 1, len(eq_classes)):
            group_i = eq_classes[left_index]
            group_j = eq_classes[right_index]
            rep_i = all_conditions[group_i[0]]
            rep_j = all_conditions[group_j[0]]
            try:
                cross_class = (
                    ConflictClass.PHI_NODE
                    if z3_solver.are_disjoint(rep_i, rep_j)
                    else ConflictClass.OVERLAP
                )
            except (Z3TranslationError, z3.Z3Exception) as exc:
                raise RuntimeError("Z3 disjointness check failed during parameter conflict detection") from exc

            for idx_a in group_i:
                for idx_b in group_j:
                    claim_a = claims[idx_a]
                    claim_b = claims[idx_b]
                    value_a = claim_a.value
                    value_b = claim_b.value
                    if _values_compatible(value_a, value_b, claim_a=claim_a, claim_b=claim_b):
                        continue
                    if _append_context_classified_record(
                        records,
                        concept_id=concept_id,
                        claim_a_id=claim_a.claim_id,
                        claim_b_id=claim_b.claim_id,
                        conditions_a=all_conditions[idx_a],
                        conditions_b=all_conditions[idx_b],
                        value_a=_value_str(value_a, claim=claim_a),
                        value_b=_value_str(value_b, claim=claim_b),
                        context_a=_claim_context(claim_a),
                        context_b=_claim_context(claim_b),
                        context_hierarchy=context_hierarchy,
                    ):
                        continue
                    records.append(ConflictRecord(
                        concept_id=concept_id,
                        claim_a_id=claim_a.claim_id,
                        claim_b_id=claim_b.claim_id,
                        warning_class=cross_class,
                        conditions_a=all_conditions[idx_a],
                        conditions_b=all_conditions[idx_b],
                        value_a=_value_str(value_a, claim=claim_a),
                        value_b=_value_str(value_b, claim=claim_b),
                    ))
