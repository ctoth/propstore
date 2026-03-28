"""Structured arguments built from canonical claim justifications."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from itertools import product

from propstore.argumentation import (
    _ATTACK_TYPES,
    _PREFERENCE_TYPES,
    _SUPPORT_TYPES,
    _UNCONDITIONAL_TYPES,
)
from propstore.core.graph_types import ActiveWorldGraph
from propstore.core.justifications import (
    CanonicalJustification,
    claim_justifications_from_active_graph,
)
from propstore.dung import (
    ArgumentationFramework,
    grounded_extension,
    hybrid_grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from propstore.preference import claim_strength, defeat_holds
from propstore.world.labelled import Label, SupportQuality, combine_labels
from propstore.world.types import ArtifactStore


@dataclass(frozen=True)
class StructuredArgument:
    arg_id: str
    claim_id: str
    conclusion_concept_id: str | None
    premise_claim_ids: tuple[str, ...]
    label: Label | None
    strength: float
    top_rule_kind: str
    attackable_kind: str
    subargument_ids: tuple[str, ...]
    support_quality: SupportQuality
    justification_id: str
    dependency_claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class StructuredProjection:
    arguments: tuple[StructuredArgument, ...]
    framework: ArgumentationFramework
    claim_to_argument_ids: dict[str, tuple[str, ...]]
    argument_to_claim_id: dict[str, str]


def build_structured_projection(
    store: ArtifactStore,
    active_claims: list[dict],
    *,
    support_metadata: dict[str, tuple[Label | None, SupportQuality]] | None = None,
    comparison: str = "elitist",
    active_graph: ActiveWorldGraph | None = None,
) -> StructuredProjection:
    """Build real structured arguments from canonical justifications.

    Delegates to the ASPIC+ bridge for full recursive argument construction.
    """
    from propstore.aspic_bridge import build_aspic_projection

    return build_aspic_projection(
        store,
        active_claims,
        support_metadata=support_metadata,
        comparison=comparison,
        active_graph=active_graph,
    )


def compute_structured_justified_arguments(
    projection: StructuredProjection,
    *,
    semantics: str = "grounded",
) -> frozenset[str] | list[frozenset[str]]:
    """Compute justified structured arguments using existing Dung semantics."""
    if semantics == "grounded":
        # Use hybrid when framework has attacks (ASPIC+ bridge produces both)
        if projection.framework.attacks is not None:
            return hybrid_grounded_extension(projection.framework)
        return grounded_extension(projection.framework)
    if semantics == "preferred":
        return [frozenset(ext) for ext in preferred_extensions(projection.framework)]
    if semantics == "stable":
        return [frozenset(ext) for ext in stable_extensions(projection.framework)]
    raise ValueError(f"Unknown semantics: {semantics}")


def _stance_rows(
    store: ArtifactStore,
    active_by_id: dict[str, dict],
    *,
    active_graph: ActiveWorldGraph | None,
) -> list[dict]:
    if active_graph is not None:
        active_ids = set(active_graph.active_claim_ids)
        rows: list[dict] = []
        for relation in active_graph.compiled.relations:
            if relation.source_id not in active_ids or relation.target_id not in active_ids:
                continue
            if relation.relation_type not in _ATTACK_TYPES and relation.relation_type not in _SUPPORT_TYPES:
                continue
            row = {
                "claim_id": relation.source_id,
                "target_claim_id": relation.target_id,
                "stance_type": relation.relation_type,
            }
            row.update(dict(relation.attributes))
            rows.append(row)
        return rows
    return list(store.stances_between(set(active_by_id)))


def _canonical_justifications(
    active_by_id: dict[str, dict],
    stance_rows: list[dict],
    *,
    active_graph: ActiveWorldGraph | None,
) -> tuple[CanonicalJustification, ...]:
    if active_graph is not None:
        return claim_justifications_from_active_graph(active_graph)

    justifications = [
        CanonicalJustification(
            justification_id=f"reported:{claim_id}",
            conclusion_claim_id=claim_id,
            rule_kind="reported_claim",
        )
        for claim_id in sorted(active_by_id)
    ]
    for row in stance_rows:
        if row["stance_type"] not in {"supports", "explains"}:
            continue
        justifications.append(
            CanonicalJustification(
                justification_id=f"{row['stance_type']}:{row['claim_id']}->{row['target_claim_id']}",
                conclusion_claim_id=row["target_claim_id"],
                premise_claim_ids=(row["claim_id"],),
                rule_kind=row["stance_type"],
                attributes={
                    str(key): value
                    for key, value in row.items()
                    if key not in {"claim_id", "target_claim_id", "stance_type"} and value is not None
                },
            )
        )
    return tuple(sorted(justifications))


def _derived_argument_id(
    claim_id: str,
    justification_id: str,
    subargument_ids: tuple[str, ...],
) -> str:
    digest = hashlib.sha1(
        f"{claim_id}\0{justification_id}\0{'|'.join(subargument_ids)}".encode("utf-8")
    ).hexdigest()[:12]
    return f"arg:{claim_id}:{justification_id}:{digest}"


def _dependency_claim_ids(
    subarguments: list[StructuredArgument],
    justification: CanonicalJustification,
) -> tuple[str, ...]:
    dependency_claim_ids = set(justification.premise_claim_ids)
    for argument in subarguments:
        dependency_claim_ids.add(argument.claim_id)
        dependency_claim_ids.update(argument.dependency_claim_ids)
    return tuple(sorted(dependency_claim_ids))


def _closure_subargument_ids(subarguments: list[StructuredArgument]) -> tuple[str, ...]:
    closure = {argument.arg_id for argument in subarguments}
    for argument in subarguments:
        closure.update(argument.subargument_ids)
    return tuple(sorted(closure))


def _combine_argument_labels(subarguments: list[StructuredArgument]) -> Label | None:
    if any(argument.label is None for argument in subarguments):
        return None
    labels = [argument.label for argument in subarguments if argument.label is not None]
    if not labels:
        return None
    return combine_labels(*labels)


def _combine_support_quality(subarguments: list[StructuredArgument]) -> SupportQuality:
    if all(argument.label is not None for argument in subarguments):
        return SupportQuality.EXACT
    qualities = {argument.support_quality for argument in subarguments}
    if SupportQuality.MIXED in qualities or len(qualities) > 1:
        return SupportQuality.MIXED
    if SupportQuality.CONTEXT_VISIBLE_ONLY in qualities:
        return SupportQuality.CONTEXT_VISIBLE_ONLY
    return SupportQuality.SEMANTIC_COMPATIBLE


def _build_structured_framework(
    active_by_id: dict[str, dict],
    arguments: tuple[StructuredArgument, ...],
    claim_to_argument_ids: dict[str, tuple[str, ...]],
    stance_rows: list[dict],
    *,
    comparison: str,
) -> ArgumentationFramework:
    attacks: set[tuple[str, str]] = set()
    defeats: set[tuple[str, str]] = set()
    arguments_by_id = {argument.arg_id: argument for argument in arguments}
    superarguments_by_subargument: dict[str, set[str]] = defaultdict(set)
    for argument in arguments:
        for subargument_id in argument.subargument_ids:
            superarguments_by_subargument[subargument_id].add(argument.arg_id)

    for stance in stance_rows:
        stance_type = stance["stance_type"]
        if stance_type not in _ATTACK_TYPES:
            continue
        source_claim_id = stance["claim_id"]
        target_claim_id = stance["target_claim_id"]
        if source_claim_id not in claim_to_argument_ids or target_claim_id not in active_by_id:
            continue

        source_args = claim_to_argument_ids[source_claim_id]
        target_args = _target_argument_ids(
            stance_type,
            target_claim_id,
            arguments,
            claim_to_argument_ids,
        )
        expanded_targets = _expand_to_superarguments(target_args, superarguments_by_subargument)
        for source_arg in source_args:
            for target_arg in expanded_targets:
                if source_arg == target_arg:
                    continue
                attacks.add((source_arg, target_arg))
                if stance_type in _UNCONDITIONAL_TYPES:
                    defeats.add((source_arg, target_arg))
                    continue
                if stance_type in _PREFERENCE_TYPES and defeat_holds(
                    stance_type,
                    claim_strength(active_by_id[source_claim_id]),
                    claim_strength(active_by_id[target_claim_id]),
                    comparison,
                ):
                    defeats.add((source_arg, target_arg))

    argument_ids = frozenset(argument.arg_id for argument in arguments)
    return ArgumentationFramework(
        arguments=argument_ids,
        defeats=frozenset(defeats),
        attacks=frozenset(attacks),
    )


def _target_argument_ids(
    stance_type: str,
    target_claim_id: str,
    arguments: tuple[StructuredArgument, ...],
    claim_to_argument_ids: dict[str, tuple[str, ...]],
) -> set[str]:
    if stance_type in {"rebuts", "supersedes"}:
        return set(claim_to_argument_ids.get(target_claim_id, ()))
    if stance_type == "undercuts":
        return {
            argument.arg_id
            for argument in arguments
            if argument.claim_id == target_claim_id and argument.attackable_kind == "inference_rule"
        }
    if stance_type == "undermines":
        return {
            argument.arg_id
            for argument in arguments
            if target_claim_id in argument.dependency_claim_ids
        }
    return set()


def _expand_to_superarguments(
    target_argument_ids: set[str],
    superarguments_by_subargument: dict[str, set[str]],
) -> set[str]:
    expanded = set(target_argument_ids)
    pending = list(target_argument_ids)
    while pending:
        current = pending.pop()
        for parent in superarguments_by_subargument.get(current, ()):
            if parent in expanded:
                continue
            expanded.add(parent)
            pending.append(parent)
    return expanded


def _default_support_metadata(claim: dict) -> tuple[Label | None, SupportQuality]:
    has_context = claim.get("context_id") is not None
    has_conditions = False
    conds_json = claim.get("conditions_cel")
    if conds_json:
        try:
            has_conditions = bool(json.loads(conds_json))
        except Exception:
            has_conditions = True
    if has_context and has_conditions:
        return None, SupportQuality.MIXED
    if has_context:
        return None, SupportQuality.CONTEXT_VISIBLE_ONLY
    if has_conditions:
        return None, SupportQuality.SEMANTIC_COMPATIBLE
    return Label.empty(), SupportQuality.EXACT


def _scalar_strength(claim: dict) -> float:
    strength = claim_strength(claim)
    return sum(strength) / len(strength)
