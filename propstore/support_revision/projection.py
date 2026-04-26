from __future__ import annotations

import hashlib
import json

from propstore.core.active_claims import ActiveClaim
from propstore.core.assertions.refs import ConditionRef, ContextReference, ProvenanceGraphRef
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import AssumptionId, to_claim_id
from propstore.core.labels import SupportQuality
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet

from propstore.support_revision.state import AssertionAtom, BeliefBase, RevisionScope


def _claim_support_lookup_id(claim: ActiveClaim) -> str:
    return to_claim_id(claim.claim_id)


def situated_assertion_from_active_claim(
    claim: ActiveClaim,
    *,
    context_id: object | None,
) -> SituatedAssertion:
    return SituatedAssertion(
        relation=_relation_ref(claim),
        role_bindings=_role_bindings(claim),
        context=_context_ref(claim, context_id=context_id),
        condition=_condition_ref(claim),
        provenance_ref=_provenance_ref(claim),
    )


def project_belief_base(bound, *, include_assumptions: bool = True) -> BeliefBase:
    """Project a scoped BoundWorld into a minimal revision-facing belief base.

    V1 includes only claims with exact ATMS-reconstructible support.
    """
    atoms_by_id: dict[str, AssertionAtom] = {}
    supporting_assumption_ids: set[AssumptionId] = set()
    support_sets: dict[str, set[tuple[AssumptionId, ...]]] = {}
    essential_support: dict[str, set[AssumptionId]] = {}
    for claim in sorted(bound.active_claims(None), key=lambda row: str(row.claim_id)):
        label, quality = bound.claim_support(claim)
        if quality is not SupportQuality.EXACT:
            continue
        assertion = situated_assertion_from_active_claim(
            claim,
            context_id=bound._environment.context_id,
        )
        atom_id = str(assertion.assertion_id)
        if label is not None:
            for environment in label.environments:
                supporting_assumption_ids.update(environment.assumption_ids)
            support_sets.setdefault(atom_id, set()).update(
                tuple(environment.assumption_ids)
                for environment in label.environments
            )
        else:
            support_sets.setdefault(atom_id, set())
        support_lookup_id = _claim_support_lookup_id(claim)
        if support_lookup_id is None:
            continue
        essential = bound.claim_essential_support(support_lookup_id)
        essential_support.setdefault(atom_id, set()).update(
            essential.assumption_ids if essential is not None else ()
        )
        existing = atoms_by_id.get(atom_id)
        atoms_by_id[atom_id] = AssertionAtom(
            atom_id=atom_id,
            assertion=assertion,
            source_claims=((claim,) if existing is None else existing.source_claims + (claim,)),
            label=label if existing is None else existing.label,
        )

    scope = RevisionScope(
        bindings=dict(bound._environment.bindings),
        context_id=bound._environment.context_id,
    )
    assumptions = (
        tuple(
            assumption
            for assumption in bound._environment.assumptions
            if assumption.assumption_id in supporting_assumption_ids
        )
        if include_assumptions
        else ()
    )
    return BeliefBase(
        scope=scope,
        atoms=tuple(atoms_by_id[atom_id] for atom_id in sorted(atoms_by_id)),
        assumptions=assumptions,
        support_sets={
            atom_id: tuple(sorted(support))
            for atom_id, support in support_sets.items()
        },
        essential_support={
            atom_id: tuple(sorted(support))
            for atom_id, support in essential_support.items()
        },
    )


def _relation_ref(claim: ActiveClaim) -> RelationConceptRef:
    claim_type = "unknown" if claim.claim_type is None else claim.claim_type.value
    return RelationConceptRef(f"ps:relation:claim:{claim_type}")


def _role_bindings(claim: ActiveClaim) -> RoleBindingSet:
    bindings = [
        RoleBinding("subject", _claim_subject(claim)),
        RoleBinding("value", _stable_value(claim.value)),
    ]
    if claim.unit is not None:
        bindings.append(RoleBinding("unit", claim.unit))
    if claim.measure is not None:
        bindings.append(RoleBinding("measure", claim.measure))
    return RoleBindingSet(tuple(bindings))


def _claim_subject(claim: ActiveClaim) -> str:
    for value in (
        claim.value_concept_id,
        claim.target_concept,
        claim.attributes.get("concept_id"),
    ):
        if value is not None:
            return str(value)
    return "ps:concept:unscoped"


def _context_ref(
    claim: ActiveClaim,
    *,
    context_id: object | None,
) -> ContextReference:
    if claim.context_id is not None:
        return ContextReference(str(claim.context_id))
    if context_id is not None:
        return ContextReference(str(context_id))
    return ContextReference("ps:context:global")


def _condition_ref(claim: ActiveClaim) -> ConditionRef:
    if not claim.conditions:
        return ConditionRef.unconditional()
    payload = tuple(str(condition) for condition in claim.conditions)
    digest = _digest(payload)
    return ConditionRef(
        id=f"ps:condition:{digest}",
        registry_fingerprint=f"claim-condition-source:{digest}",
    )


def _provenance_ref(claim: ActiveClaim) -> ProvenanceGraphRef:
    payload = (
        str(claim.artifact_id),
        None if claim.source is None else claim.source.to_dict(),
        None if claim.provenance is None else claim.provenance.to_dict(),
    )
    return ProvenanceGraphRef(f"urn:propstore:claim-provenance:{_digest(payload)}")


def _stable_value(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: object) -> str:
    rendered = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:32]
