"""Projection helpers and caller-facing ASPIC bridge entrypoint."""

from __future__ import annotations

import hashlib
import json
import statistics
from collections.abc import Mapping, Sequence

from argumentation.aspic import CSAF, Literal, PremiseArg, conc, prem, sub, top_rule
from argumentation.dung import ArgumentationFramework
from propstore.core.active_claims import ActiveClaim, ActiveClaimInput, coerce_active_claims
from propstore.core.environment import StanceStore
from propstore.core.graph_types import ActiveWorldGraph
from propstore.core.labels import Label, SupportMetadata, SupportQuality
from propstore.core.literal_keys import IstLiteralKey
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.preference import claim_strength
from propstore.provenance.records import ProjectionFrameProvenanceRecord
from propstore.structured_projection import (
    ProjectionAtom,
    ProjectionLossWitness,
    StructuredArgument,
    StructuredProjection,
)

from .build import build_bridge_csaf
from .extract import _extract_justifications, _extract_stance_rows
from .grounding import _typed_scalar_key
from .translate import claims_to_literals

_STRICT_RULE_STRENGTH = 1.0
_DEFEASIBLE_RULE_STRENGTH = 0.7


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


def _projection_backend_atom_id(literal: Literal) -> str:
    """Return the ASPIC backend-local atom id for one projected literal."""

    return json.dumps(
        {
            "predicate": literal.atom.predicate,
            "arguments": [_typed_scalar_key(value) for value in literal.atom.arguments],
            "negated": literal.negated,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _source_assertion_ids_for_claim(claim: ActiveClaim | None) -> tuple[str, ...]:
    if claim is None:
        return ()
    raw = claim.attributes.get("source_assertion_ids")
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, Sequence) and not isinstance(raw, str | bytes):
        return tuple(str(value) for value in raw)
    return ()


def _projection_atom_for_literal(
    literal: Literal,
    *,
    claim: ActiveClaim | None,
) -> ProjectionAtom:
    backend_atom_id = _projection_backend_atom_id(literal)
    source_assertion_ids = _source_assertion_ids_for_claim(claim)
    loss = None
    if not source_assertion_ids:
        loss = ProjectionLossWitness(
            backend="aspic",
            kind="missing_source_assertion",
            reason=(
                "ASPIC literal projection has no source situated assertion id "
                "to attribute the backend atom"
            ),
            backend_atom_id=backend_atom_id,
        )
    provenance = None
    if source_assertion_ids:
        frame_digest = hashlib.sha256(backend_atom_id.encode("utf-8")).hexdigest()
        provenance = ProjectionFrameProvenanceRecord(
            frame_id=f"urn:propstore:projection:aspic:{frame_digest}",
            backend="aspic",
            projected_at="projection-boundary-v2",
            source_assertion_ids=source_assertion_ids,
        )
    return ProjectionAtom(
        backend="aspic",
        backend_atom=literal.atom,
        backend_atom_id=backend_atom_id,
        negated=literal.negated,
        source_assertion_ids=source_assertion_ids,
        provenance=provenance,
        loss=loss,
    )


def _claim_ids_for_literals(
    literals: Sequence[Literal],
    claim_literal_ids: Mapping[Literal, str],
) -> tuple[str, ...]:
    claim_ids: list[str] = []
    for literal in literals:
        claim_id = claim_literal_ids.get(literal)
        if claim_id is not None and claim_id not in claim_ids:
            claim_ids.append(claim_id)
    return tuple(claim_ids)


def _direct_premise_literals(argument) -> tuple[Literal, ...]:
    if isinstance(argument, PremiseArg):
        return (conc(argument),)
    rule = top_rule(argument)
    if rule is None:
        return ()
    return tuple(rule.antecedents)


def _rule_strength(argument) -> float:
    top = top_rule(argument)
    if top is None:
        return _STRICT_RULE_STRENGTH
    if top.kind == "strict":
        return _STRICT_RULE_STRENGTH
    return _DEFEASIBLE_RULE_STRENGTH


def _grounded_argument_strength(argument) -> float:
    if isinstance(argument, PremiseArg):
        return _STRICT_RULE_STRENGTH
    strengths = [_rule_strength(argument)]
    strengths.extend(
        _grounded_argument_strength(sub_argument)
        for sub_argument in sub(argument)
        if sub_argument != argument
    )
    return min(strengths)


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
    claim_by_id = {str(claim.claim_id): claim for claim in normalized_claims}
    claim_literal_ids = {
        literal: str(key.proposition_id)
        for key, literal in claims_to_literals(normalized_claims).items()
        if isinstance(key, IstLiteralKey)
    }

    projected_args: list[StructuredArgument] = []
    projected_arg_ids: set[str] = set()
    claim_to_args: dict[str, list[str]] = {}
    arg_to_claim: dict[str, str] = {}

    for argument in csaf.arguments:
        conclusion = conc(argument)
        arg_id = csaf.arg_to_id[argument]
        claim_id = claim_literal_ids.get(conclusion)
        claim = None if claim_id is None else claim_by_id[claim_id]

        top = top_rule(argument)
        if isinstance(argument, PremiseArg):
            top_rule_kind = "reported_claim"
        elif top is not None:
            top_rule_kind = top.kind
        else:
            top_rule_kind = "reported_claim"

        attackable_kind = "base_claim" if isinstance(argument, PremiseArg) else "inference_rule"
        premise_claim_ids = _claim_ids_for_literals(
            _direct_premise_literals(argument),
            claim_literal_ids,
        )
        subargument_ids = tuple(
            csaf.arg_to_id[sub_argument]
            for sub_argument in sub(argument)
            if sub_argument != argument and sub_argument in csaf.arg_to_id
        )

        if claim is None:
            strength = _grounded_argument_strength(argument)
        else:
            vector = claim_strength(claim)
            strength = 0.0 if vector.is_vacuous else statistics.mean(vector.dimensions)

        if isinstance(argument, PremiseArg):
            justification_id = (
                f"reported:{claim_id}"
                if claim_id is not None
                else f"premise:{_projection_backend_atom_id(conclusion)}"
            )
        elif top is not None and top.name is not None:
            justification_id = top.name
        else:
            justification_id = (
                f"reported:{claim_id}"
                if claim_id is not None
                else f"premise:{_projection_backend_atom_id(conclusion)}"
            )

        dependency_claim_ids = _claim_ids_for_literals(
            tuple(sorted(prem(argument), key=_projection_backend_atom_id)),
            claim_literal_ids,
        )

        if claim_id is not None and claim_id in metadata:
            label, support_quality = metadata[claim_id]
        elif claim is not None:
            label, support_quality = _default_support_metadata(claim)
        else:
            label, support_quality = None, SupportQuality.EXACT

        projected = StructuredArgument(
            arg_id=arg_id,
            projection=_projection_atom_for_literal(conclusion, claim=claim),
            claim_id=claim_id,
            conclusion_concept_id=(
                None if claim is None or claim.value_concept_id is None else str(claim.value_concept_id)
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

    def require_projected_argument_id(argument, relation: str) -> str:
        if argument not in csaf.arg_to_id:
            raise ValueError(
                f"{relation} references argument outside projected argument domain: "
                f"{argument!r}"
            )
        arg_id = csaf.arg_to_id[argument]
        if arg_id not in projected_arg_ids:
            raise ValueError(
                f"{relation} references filtered argument outside projected argument domain: "
                f"{arg_id}"
            )
        return arg_id

    projected_attacks = frozenset(
        (
            require_projected_argument_id(attack.attacker, "attack"),
            require_projected_argument_id(attack.target, "attack"),
        )
        for attack in csaf.attacks
    )
    projected_defeats = frozenset(
        (
            require_projected_argument_id(attacker, "defeat"),
            require_projected_argument_id(target, "defeat"),
        )
        for attacker, target in csaf.defeats
    )

    proj_framework = ArgumentationFramework(
        arguments=frozenset(projected_arg_ids),
        defeats=projected_defeats,
        attacks=projected_attacks,
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
        store,
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
