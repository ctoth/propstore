from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import rfc8785
from propstore.core.assertions.refs import ConditionRef, ContextReference, ProvenanceGraphRef
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import AssumptionId, to_claim_id
from propstore.core.labels import SupportQuality
from propstore.core.relations import ClaimConceptLinkRole, RelationConceptRef, RoleBinding, RoleBindingSet
from propstore.families.claims.declaration import Claim
from propstore.json_types import JsonValue

from propstore.support_revision.state import AssertionAtom, BeliefBase, RevisionScope

if TYPE_CHECKING:
    from propstore.support_revision.history import EpistemicSnapshot


def snapshot_to_claim_ids(snapshot: "EpistemicSnapshot") -> set[str]:
    """Project an ``EpistemicSnapshot`` to the set of source-claim ids it accepts.

    For each ``AssertionAtom`` in the snapshot's belief base whose
    ``atom_id`` is in ``snapshot.state.accepted_atom_ids``, collect every
    typed source claim id. Many-to-one is honored: an accepted atom with N
    source claim ids contributes all N ids.

    The reverse map (atom -> claim_ids) is recoverable from the snapshot
    itself because every ``AssertionAtom`` carries ``source_claim_ids``.
    This is the read-direction inverse of
    ``project_belief_base``.
    """
    state = snapshot.state
    accepted = set(state.accepted_atom_ids)
    return {
        str(claim_id)
        for atom in state.base.atoms
        if isinstance(atom, AssertionAtom) and atom.atom_id in accepted
        for claim_id in atom.source_claim_ids
    }


def _claim_support_lookup_id(claim: Claim) -> str:
    return to_claim_id(claim.id)


def situated_assertion_from_claim(
    claim: Claim,
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
    for claim in sorted(bound.active_claims(None), key=lambda row: str(row.id)):
        label, quality = bound.claim_support(claim)
        if quality is not SupportQuality.EXACT:
            continue
        assertion = situated_assertion_from_claim(
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

    scope = _revision_scope_from_bound(bound)
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


def _revision_scope_from_bound(bound) -> RevisionScope:
    branch: str | None = None
    commit: str | None = None
    merge_parent_commits: tuple[str, ...] = ()
    repo = getattr(getattr(bound, "_store", None), "_repo", None)
    git = getattr(repo, "git", None)
    if git is not None:
        branch = git.current_branch_name() or git.primary_branch_name()
        commit = None if branch is None else git.branch_sha(branch)
        if commit is not None:
            merge_parent_commits = tuple(git.commit_parent_shas(commit))

    return RevisionScope(
        bindings=dict(bound._environment.bindings),
        context_id=bound._environment.context_id,
        branch=branch,
        commit=commit,
        merge_parent_commits=merge_parent_commits,
    )


def _relation_ref(claim: Claim) -> RelationConceptRef:
    claim_type = "unknown" if claim.type is None else claim.type.value
    return RelationConceptRef(f"ps:relation:claim:{claim_type}")


def _role_bindings(claim: Claim) -> RoleBindingSet:
    bindings = [
        RoleBinding("subject", _claim_subject(claim)),
    ]
    return RoleBindingSet(tuple(bindings))


def _claim_subject(claim: Claim) -> str:
    for role in (ClaimConceptLinkRole.OUTPUT, ClaimConceptLinkRole.TARGET):
        for link in claim.concept_links:
            if link.role is role:
                return str(link.concept_id)
    if claim.target_concept is not None:
        return str(claim.target_concept)
    return "ps:concept:unscoped"


def _context_ref(
    claim: Claim,
    *,
    context_id: object | None,
) -> ContextReference:
    if claim.context_id is not None:
        return ContextReference(str(claim.context_id))
    if context_id is not None:
        return ContextReference(str(context_id))
    return ContextReference("ps:context:global")


def _condition_ref(claim: Claim) -> ConditionRef:
    return ConditionRef.unconditional()


def _provenance_ref(claim: Claim) -> ProvenanceGraphRef:
    payload: JsonValue = [
        str(claim.id),
        claim.source_slug,
        claim.provenance_json,
    ]
    return ProvenanceGraphRef(f"urn:propstore:claim-provenance:{_digest(payload)}")


def _stable_value(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: JsonValue) -> str:
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()
