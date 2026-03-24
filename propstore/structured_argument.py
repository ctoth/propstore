"""Structured argument projection over active claims and exact support labels.

This is a first structured projection backend, not full ASPIC+ execution.
Each active claim projects to one base argument, reusing the current Dung
machinery for extension computation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from propstore.argumentation import (
    _ATTACK_TYPES,
    _PREFERENCE_TYPES,
    _SUPPORT_TYPES,
    _UNCONDITIONAL_TYPES,
    _cayrol_derived_defeats,
    _transitive_support_targets,
)
from propstore.dung import (
    ArgumentationFramework,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from propstore.preference import claim_strength, defeat_holds
from propstore.world.labelled import Label, SupportQuality
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
    confidence_threshold: float = 0.5,
) -> StructuredProjection:
    """Project active claims into base structured arguments plus an AF."""
    active_by_id = {claim["id"]: claim for claim in active_claims if claim.get("id")}
    metadata = support_metadata or {}

    arguments: list[StructuredArgument] = []
    claim_to_argument_ids: dict[str, tuple[str, ...]] = {}
    argument_to_claim_id: dict[str, str] = {}

    for claim_id in sorted(active_by_id):
        claim = active_by_id[claim_id]
        arg_id = f"arg:{claim_id}"
        label, support_quality = metadata.get(
            claim_id,
            _default_support_metadata(claim),
        )
        arguments.append(
            StructuredArgument(
                arg_id=arg_id,
                claim_id=claim_id,
                conclusion_concept_id=(
                    claim.get("concept_id")
                    or claim.get("concept")
                    or claim.get("target_concept")
                ),
                premise_claim_ids=(),
                label=label,
                strength=sum(s := claim_strength(claim)) / len(s),  # scalar for serialization
                top_rule_kind="claim",
                attackable_kind="base_claim",
                subargument_ids=(),
                support_quality=support_quality,
            )
        )
        claim_to_argument_ids[claim_id] = (arg_id,)
        argument_to_claim_id[arg_id] = claim_id

    framework = _build_projected_framework(
        store,
        active_by_id,
        claim_to_argument_ids,
        comparison=comparison,
        confidence_threshold=confidence_threshold,
    )
    return StructuredProjection(
        arguments=tuple(arguments),
        framework=framework,
        claim_to_argument_ids=claim_to_argument_ids,
        argument_to_claim_id=argument_to_claim_id,
    )


def compute_structured_justified_arguments(
    projection: StructuredProjection,
    *,
    semantics: str = "grounded",
) -> frozenset[str] | list[frozenset[str]]:
    """Reuse existing Dung semantics over projected argument IDs."""
    if semantics == "grounded":
        return grounded_extension(projection.framework)
    if semantics == "preferred":
        return [frozenset(ext) for ext in preferred_extensions(projection.framework)]
    if semantics == "stable":
        return [frozenset(ext) for ext in stable_extensions(projection.framework)]
    raise ValueError(f"Unknown semantics: {semantics}")


def _build_projected_framework(
    store: ArtifactStore,
    active_by_id: dict[str, dict],
    claim_to_argument_ids: dict[str, tuple[str, ...]],
    *,
    comparison: str,
    confidence_threshold: float,
) -> ArgumentationFramework:
    attacks: set[tuple[str, str]] = set()
    defeats: set[tuple[str, str]] = set()
    supports: set[tuple[str, str]] = set()

    stances = store.stances_between(set(active_by_id))
    for stance in stances:
        claim_id = stance["claim_id"]
        target_claim_id = stance["target_claim_id"]
        if claim_id not in active_by_id or target_claim_id not in active_by_id:
            continue

        confidence = stance.get("confidence")
        if confidence is not None and confidence < confidence_threshold:
            continue

        source_args = claim_to_argument_ids[claim_id]
        target_args = claim_to_argument_ids[target_claim_id]
        stance_type = stance["stance_type"]

        if stance_type in _SUPPORT_TYPES:
            for source_arg in source_args:
                for target_arg in target_args:
                    supports.add((source_arg, target_arg))
            continue

        if stance_type not in _ATTACK_TYPES:
            continue

        for source_arg in source_args:
            for target_arg in target_args:
                attacks.add((source_arg, target_arg))
                if stance_type in _UNCONDITIONAL_TYPES:
                    defeats.add((source_arg, target_arg))
                    continue
                if stance_type in _PREFERENCE_TYPES:
                    attacker_claim = active_by_id[claim_id]
                    target_claim = active_by_id[target_claim_id]
                    if defeat_holds(
                        stance_type,
                        claim_strength(attacker_claim),  # already returns list[float]
                        claim_strength(target_claim),
                        comparison,
                    ):
                        defeats.add((source_arg, target_arg))

    if supports:
        defeats |= _cayrol_derived_defeats(defeats, supports)

    argument_ids = frozenset(
        argument_id
        for ids in claim_to_argument_ids.values()
        for argument_id in ids
    )
    return ArgumentationFramework(
        arguments=argument_ids,
        defeats=frozenset(defeats),
        attacks=frozenset(attacks),
    )


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
