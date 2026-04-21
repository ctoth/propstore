"""Projection helpers and caller-facing ASPIC bridge entrypoint."""

from __future__ import annotations

import json
import statistics
from collections.abc import Mapping, Sequence

from argumentation.aspic import CSAF, Literal, PremiseArg, conc, prem, sub, top_rule
from propstore.core.active_claims import ActiveClaim, ActiveClaimInput, coerce_active_claims
from propstore.core.environment import StanceStore
from propstore.core.graph_types import ActiveWorldGraph
from propstore.core.labels import Label, SupportQuality
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.preference import claim_strength
from propstore.structured_projection import StructuredArgument, StructuredProjection
from propstore.world.types import SupportMetadata

from .build import build_bridge_csaf
from .extract import _extract_justifications, _extract_stance_rows
from .grounding import _typed_scalar_key


def _default_support_metadata(claim: ActiveClaim) -> tuple[Label | None, SupportQuality]:
    """Compute default projected support metadata for a claim-backed argument."""

    has_context = claim.context_id is not None
    has_conditions = bool(claim.conditions)
    if has_context and has_conditions:
        return None, SupportQuality.MIXED
    if has_context:
        return None, SupportQuality.CONTEXT_VISIBLE_ONLY
    if has_conditions:
        return None, SupportQuality.SEMANTIC_COMPATIBLE
    return Label.empty(), SupportQuality.EXACT


def _projection_conclusion_key(literal: Literal) -> str:
    """Return a stable string identity for one projected conclusion literal."""

    return json.dumps(
        {
            "predicate": literal.atom.predicate,
            "arguments": [_typed_scalar_key(value) for value in literal.atom.arguments],
            "negated": literal.negated,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def csaf_to_projection(
    csaf: CSAF,
    active_claims: Sequence[ActiveClaimInput],
    *,
    support_metadata: SupportMetadata | None = None,
) -> StructuredProjection:
    """Map a CSAF onto the public ``StructuredProjection`` facade."""

    metadata: SupportMetadata = {}
    if support_metadata is not None:
        metadata = support_metadata
    normalized_claims = coerce_active_claims(active_claims)
    claim_id_set = {str(claim.claim_id) for claim in normalized_claims}
    claim_by_id = {str(claim.claim_id): claim for claim in normalized_claims}

    projected_args: list[StructuredArgument] = []
    projected_arg_ids: set[str] = set()
    claim_to_args: dict[str, list[str]] = {}
    arg_to_claim: dict[str, str] = {}

    for argument in csaf.arguments:
        conclusion = conc(argument)
        arg_id = csaf.arg_to_id[argument]
        claim_id = (
            conclusion.atom.predicate
            if conclusion.atom.predicate in claim_id_set and not conclusion.negated
            else None
        )
        claim = None if claim_id is None else claim_by_id[claim_id]

        top = top_rule(argument)
        if isinstance(argument, PremiseArg):
            top_rule_kind = "reported_claim"
        elif top is not None:
            top_rule_kind = top.kind
        else:
            top_rule_kind = "reported_claim"

        attackable_kind = "base_claim" if isinstance(argument, PremiseArg) else "inference_rule"
        premise_claim_ids = tuple(
            premise_literal.atom.predicate
            for premise_literal in prem(argument)
            if premise_literal.atom.predicate in claim_id_set
        )
        subargument_ids = tuple(
            csaf.arg_to_id[sub_argument]
            for sub_argument in sub(argument)
            if sub_argument != argument and sub_argument in csaf.arg_to_id
        )

        if claim is None:
            strength = 0.0
        else:
            vector = claim_strength(claim)
            strength = 0.0 if vector.is_vacuous else statistics.mean(vector.dimensions)

        if isinstance(argument, PremiseArg):
            justification_id = (
                f"reported:{claim_id}"
                if claim_id is not None
                else f"premise:{_projection_conclusion_key(conclusion)}"
            )
        elif top is not None and top.name is not None:
            justification_id = top.name
        else:
            justification_id = (
                f"reported:{claim_id}"
                if claim_id is not None
                else f"premise:{_projection_conclusion_key(conclusion)}"
            )

        dependency_claim_ids = tuple(
            premise_literal.atom.predicate
            for premise_literal in prem(argument)
            if premise_literal.atom.predicate in claim_id_set
        )

        if claim_id is not None and claim_id in metadata:
            label, support_quality = metadata[claim_id]
        elif claim is not None:
            label, support_quality = _default_support_metadata(claim)
        else:
            label, support_quality = None, SupportQuality.EXACT

        projected = StructuredArgument(
            arg_id=arg_id,
            conclusion_key=_projection_conclusion_key(conclusion),
            claim_id=claim_id,
            conclusion_concept_id=(
                None if claim is None or claim.concept_id is None else str(claim.concept_id)
            ),
            premise_claim_ids=premise_claim_ids,
            label=label,
            strength=strength,
            top_rule_kind=top_rule_kind,
            attackable_kind=attackable_kind,
            subargument_ids=subargument_ids,
            support_quality=support_quality,
            justification_id=justification_id,
            dependency_claim_ids=dependency_claim_ids,
        )
        projected_args.append(projected)
        projected_arg_ids.add(arg_id)
        if claim_id is not None:
            claim_to_args.setdefault(claim_id, []).append(arg_id)
            arg_to_claim[arg_id] = claim_id

    proj_framework = type(csaf.framework)(
        arguments=frozenset(projected_arg_ids),
        defeats=frozenset(
            (attacker, target)
            for attacker, target in csaf.framework.defeats
            if attacker in projected_arg_ids and target in projected_arg_ids
        ),
        attacks=frozenset(
            (csaf.arg_to_id[attack.attacker], csaf.arg_to_id[attack.target])
            for attack in csaf.attacks
            if attack.attacker in csaf.arg_to_id
            and attack.target in csaf.arg_to_id
            and csaf.arg_to_id[attack.attacker] in projected_arg_ids
            and csaf.arg_to_id[attack.target] in projected_arg_ids
        ),
    )

    return StructuredProjection(
        arguments=tuple(sorted(projected_args, key=lambda argument: argument.arg_id)),
        framework=proj_framework,
        claim_to_argument_ids={claim_id: tuple(arg_ids) for claim_id, arg_ids in claim_to_args.items()},
        argument_to_claim_id=arg_to_claim,
    )


def build_aspic_projection(
    store: StanceStore,
    active_claims: Sequence[ActiveClaimInput],
    *,
    bundle: GroundedRulesBundle,
    support_metadata: SupportMetadata | None = None,
    comparison: str = "elitist",
    link: str = "last",
    active_graph: ActiveWorldGraph | None = None,
) -> StructuredProjection:
    """Build a ``StructuredProjection`` via the ASPIC bridge."""

    normalized_claims = tuple(coerce_active_claims(active_claims))
    active_by_id = {str(claim.claim_id): claim for claim in normalized_claims}

    stance_rows = _extract_stance_rows(store, active_by_id, active_graph=active_graph)
    justifications = _extract_justifications(
        active_by_id,
        stance_rows,
        active_graph=active_graph,
    )
    csaf = build_bridge_csaf(
        normalized_claims,
        justifications,
        stance_rows,
        bundle=bundle,
        comparison=comparison,
        link=link,
    )
    return csaf_to_projection(csaf, normalized_claims, support_metadata=support_metadata)


__all__ = [
    "build_aspic_projection",
    "csaf_to_projection",
]
