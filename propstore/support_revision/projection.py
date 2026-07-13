"""Project a scoped :class:`BoundWorld` into a revision-facing belief base.

This is the read-side bridge from the world layer into the support-incision
package: it reads a :class:`~propstore.world.bound.BoundWorld`'s active claims,
their exact ATMS support, and the bound environment, and lowers each
exact-supported claim into a :class:`~propstore.core.assertions.situated.SituatedAssertion`
keyed :class:`AssertionAtom`. The situated-assertion identity (relation + role
bindings + context + condition) is what collapses many source claims that say the
same thing into one belief atom, while keeping rival values distinct (Darwiche &
Pearl iterated revision needs a sentence identity finer than the target concept).

The thin :class:`~propstore.core.active_claims.ActiveClaim` the world layer hands
us carries its scalar ``value`` and ``claim_type`` in ``attributes`` and its
subject concept in ``concept_id``; the assertion is built from those. Conditions
are not carried on the thin claim view — their effect on belief is already
captured in the support sets / essential support (the assumption ids the ATMS
attaches), so the projected assertion is unconditional. The provenance graph
reference is recorded for audit but never enters assertion identity (CLAUDE.md:
the provenance carrier never contaminates claim identity).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from propstore.core.active_claims import ActiveClaim
from propstore.core.assertions.refs import ConditionRef, ContextReference, ProvenanceGraphRef
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import AssumptionId
from propstore.core.labels import SupportQuality, environment_assumption_ids
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet
from propstore.support_revision.state import AssertionAtom, BeliefBase, RevisionScope

if TYPE_CHECKING:
    from propstore.support_revision.history import EpistemicSnapshot
    from propstore.world.bound import BoundWorld


def snapshot_to_claim_ids(snapshot: EpistemicSnapshot) -> set[str]:
    """Project an ``EpistemicSnapshot`` to the set of source-claim ids it accepts.

    For each ``AssertionAtom`` in the snapshot's belief base whose ``atom_id`` is
    in ``snapshot.state.accepted_atom_ids``, collect the string-form ``claim_id``
    of every ``ActiveClaim`` in ``atom.source_claims``. Many-to-one is honored: an
    accepted atom with N source claims contributes all N ids. This is the
    read-direction inverse of :func:`project_belief_base`.
    """

    state = snapshot.state
    accepted = set(state.accepted_atom_ids)
    return {
        str(claim.claim_id)
        for atom in state.base.atoms
        if isinstance(atom, AssertionAtom) and atom.atom_id in accepted
        for claim in atom.source_claims
    }


def situated_assertion_from_active_claim(
    claim: ActiveClaim,
    *,
    context_id: object | None,
) -> SituatedAssertion:
    """Lower one thin active claim into its situated-assertion identity."""

    return SituatedAssertion(
        relation=_relation_ref(claim),
        role_bindings=_role_bindings(claim),
        context=_context_ref(claim, context_id=context_id),
        condition=ConditionRef.unconditional(),
        provenance_ref=_provenance_ref(claim),
    )


def project_belief_base(bound: BoundWorld, *, include_assumptions: bool = True) -> BeliefBase:
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
            context_id=bound.environment.context_id,
        )
        atom_id = str(assertion.assertion_id)
        if label is not None:
            for environment in label.environments:
                supporting_assumption_ids.update(environment_assumption_ids(environment))
            support_sets.setdefault(atom_id, set()).update(
                environment_assumption_ids(environment) for environment in label.environments
            )
        else:
            support_sets.setdefault(atom_id, set())
        essential = bound.claim_essential_support(str(claim.claim_id))
        essential_support.setdefault(atom_id, set()).update(
            environment_assumption_ids(essential) if essential is not None else ()
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
            for assumption in bound.environment.assumptions
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
            atom_id: tuple(sorted(support)) for atom_id, support in support_sets.items()
        },
        essential_support={
            atom_id: tuple(sorted(support)) for atom_id, support in essential_support.items()
        },
    )


def _revision_scope_from_bound(bound: BoundWorld) -> RevisionScope:
    branch: str | None = None
    commit: str | None = None
    merge_parent_commits: tuple[str, ...] = ()
    repo = getattr(getattr(bound, "_store", None), "_repo", None)
    git = getattr(repo, "git", None)
    if git is not None:
        branch = git.current_branch_name() or git.primary_branch_name()
        commit = None if branch is None else git.branch_sha(branch)
        if commit is not None:
            merge_parent_commits = tuple(git.iter_commit_parent_shas(commit))

    return RevisionScope(
        bindings=dict(bound.environment.bindings),
        context_id=bound.environment.context_id,
        branch=branch,
        commit=commit,
        merge_parent_commits=merge_parent_commits,
    )


def _relation_ref(claim: ActiveClaim) -> RelationConceptRef:
    claim_type = claim.claim_type
    claim_type_text = "unknown" if claim_type is None else claim_type.value
    return RelationConceptRef(f"ps:relation:claim:{claim_type_text}")


def _role_bindings(claim: ActiveClaim) -> RoleBindingSet:
    return RoleBindingSet(
        (
            RoleBinding("subject", _claim_subject(claim)),
            RoleBinding("value", _stable_value(claim.value)),
        )
    )


def _claim_subject(claim: ActiveClaim) -> str:
    if claim.concept_id is not None:
        return str(claim.concept_id)
    return "ps:concept:unscoped"


def _context_ref(claim: ActiveClaim, *, context_id: object | None) -> ContextReference:
    if claim.context_id is not None:
        return ContextReference(str(claim.context_id))
    if context_id is not None:
        return ContextReference(str(context_id))
    return ContextReference("ps:context:global")


def _provenance_ref(claim: ActiveClaim) -> ProvenanceGraphRef:
    return ProvenanceGraphRef(f"urn:propstore:claim-provenance:{claim.claim_id}")


def _stable_value(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
