"""Inspectable policy profiles for epistemic workflows.

A :class:`PolicyProfile` is the stable, content-addressed bundle of the policy
choices an epistemic workflow runs under: how revision selects incisions, how
merge aggregates, which argumentation semantics decide admissibility, what source
trust is required, and how unresolved situations escalate. The profile hashes to
a deterministic ``profile_id`` so two runs under identical policy collapse to one
identity (CLAUDE.md: the system is lazy until rendering; render policy is data,
not a hidden global).

The ``from_dict`` constructors accept a decoded JSON payload (``Mapping[str,
Any]``) at the serialization boundary, matching the rest of the storage layer's
``from_dict``/``from_mapping`` codecs.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from quire.canonical import canonical_json_bytes

from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet
from propstore.world.types import (
    ArgumentationSemantics,
    MergeOperator,
    ReasoningBackend,
    RenderPolicy,
    normalize_argumentation_semantics,
    normalize_merge_operator,
    normalize_reasoning_backend,
)

_PROFILE_VERSION = "propstore.policy_profile.v1"

# The default iterated-revision operator. The belief-set adapter (7b-1) owns the
# operator routing; this is the policy-level default name and the single spelling
# the adapter imports from here when it lands. "restrained" is Booth & Meyer's
# restrained revision (a conservative iterated operator).
DEFAULT_ITERATED_OPERATOR = "restrained"


def _hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


@dataclass(frozen=True, order=True)
class RevisionPolicy:
    operator: str = DEFAULT_ITERATED_OPERATOR
    selection: str = "minimal_incision"
    entrenchment: str = "support_sensitive"
    allow_reintroduction: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator": self.operator,
            "selection": self.selection,
            "entrenchment": self.entrenchment,
            "allow_reintroduction": self.allow_reintroduction,
        }


@dataclass(frozen=True, order=True)
class MergePolicy:
    operator: MergeOperator = MergeOperator.SIGMA
    conflict_strategy: str = "surface_conflicts"
    branch_filter: tuple[str, ...] | None = None
    require_witnesses: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "operator", normalize_merge_operator(self.operator))
        if self.branch_filter is not None:
            object.__setattr__(
                self,
                "branch_filter",
                tuple(str(item) for item in self.branch_filter),
            )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "operator": self.operator.value,
            "conflict_strategy": self.conflict_strategy,
            "require_witnesses": self.require_witnesses,
        }
        if self.branch_filter is not None:
            data["branch_filter"] = list(self.branch_filter)
        return data


@dataclass(frozen=True, order=True)
class AdmissibilityProfile:
    reasoning_backend: ReasoningBackend = ReasoningBackend.CLAIM_GRAPH
    semantics: ArgumentationSemantics = ArgumentationSemantics.GROUNDED
    conflict_free_basis: str = "attack"
    comparison: str = "elitist"
    link: str = "last"
    decision_criterion: str = "pignistic"
    pessimism_index: float = 0.5

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reasoning_backend",
            normalize_reasoning_backend(self.reasoning_backend),
        )
        object.__setattr__(
            self,
            "semantics",
            normalize_argumentation_semantics(self.semantics),
        )
        object.__setattr__(self, "pessimism_index", float(self.pessimism_index))

    def to_dict(self) -> dict[str, Any]:
        return {
            "reasoning_backend": self.reasoning_backend.value,
            "semantics": self.semantics.value,
            "conflict_free_basis": self.conflict_free_basis,
            "comparison": self.comparison,
            "link": self.link,
            "decision_criterion": self.decision_criterion,
            "pessimism_index": self.pessimism_index,
        }


@dataclass(frozen=True, order=True)
class SourceTrustProfile:
    accepted_authorities: tuple[str, ...] = ()
    required_attitude: str = "asserted"
    unsigned_graph_policy: str = "quote_only"
    require_digest: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "accepted_authorities",
            tuple(sorted(str(item) for item in self.accepted_authorities)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted_authorities": list(self.accepted_authorities),
            "required_attitude": self.required_attitude,
            "unsigned_graph_policy": self.unsigned_graph_policy,
            "require_digest": self.require_digest,
        }


@dataclass(frozen=True, order=True)
class EscalationPolicy:
    unresolved_conflict: str = "queue_investigation"
    missing_warrant: str = "mark_untrusted"
    low_trust: str = "require_review"

    def to_dict(self) -> dict[str, Any]:
        return {
            "unresolved_conflict": self.unresolved_conflict,
            "missing_warrant": self.missing_warrant,
            "low_trust": self.low_trust,
        }


@dataclass(frozen=True)
class PolicyProfile:
    revision: RevisionPolicy = field(default_factory=RevisionPolicy)
    merge: MergePolicy = field(default_factory=MergePolicy)
    admissibility: AdmissibilityProfile = field(default_factory=AdmissibilityProfile)
    source_trust: SourceTrustProfile = field(default_factory=SourceTrustProfile)
    escalation: EscalationPolicy = field(default_factory=EscalationPolicy)
    label: str = "default"
    schema_version: str = _PROFILE_VERSION
    profile_id: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != _PROFILE_VERSION:
            raise ValueError(
                f"unsupported policy profile version: {self.schema_version}"
            )
        object.__setattr__(self, "profile_id", self._derived_profile_id())

    @property
    def content_hash(self) -> str:
        return _hash(self._content_payload())

    def to_dict(self) -> dict[str, Any]:
        data = self._content_payload()
        data["profile_id"] = self.profile_id
        data["content_hash"] = self.content_hash
        return data

    def _derived_profile_id(self) -> str:
        return f"urn:propstore:policy-profile:{self.content_hash}"

    def _content_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "label": self.label,
            "revision": self.revision.to_dict(),
            "merge": self.merge.to_dict(),
            "admissibility": self.admissibility.to_dict(),
            "source_trust": self.source_trust.to_dict(),
            "escalation": self.escalation.to_dict(),
        }


def default_policy_profile() -> PolicyProfile:
    return PolicyProfile()


def policy_profile_from_render_policy(
    policy: RenderPolicy,
    *,
    revision: RevisionPolicy | None = None,
    source_trust: SourceTrustProfile | None = None,
    escalation: EscalationPolicy | None = None,
) -> PolicyProfile:
    """Lower a render-time :class:`RenderPolicy` into a stable policy profile.

    The render policy's merge operator, branch filter, and argumentation choices
    become the corresponding profile sections; revision/source-trust/escalation
    default unless the caller supplies them.
    """

    return PolicyProfile(
        revision=revision or RevisionPolicy(),
        merge=MergePolicy(
            operator=policy.merge_operator,
            branch_filter=policy.branch_filter,
        ),
        admissibility=AdmissibilityProfile(
            reasoning_backend=policy.reasoning_backend,
            semantics=policy.semantics,
            comparison=policy.comparison,
            link=policy.link,
            decision_criterion=policy.decision_criterion,
            pessimism_index=policy.pessimism_index,
        ),
        source_trust=source_trust or SourceTrustProfile(),
        escalation=escalation or EscalationPolicy(),
    )


def policy_assertions(
    profile: PolicyProfile,
    *,
    context_id: str,
) -> tuple[SituatedAssertion, ...]:
    """Materialize a profile as situated assertions for the assertion substrate."""

    context = ContextReference(context_id)
    condition = ConditionRef.unconditional()
    provenance = ProvenanceGraphRef(
        f"urn:propstore:policy-provenance:{profile.content_hash}"
    )
    return (
        _policy_assertion(
            relation_id="ps:concept:policy-profile",
            context=context,
            condition=condition,
            provenance=provenance,
            roles={
                "profile": profile.profile_id,
                "content_hash": profile.content_hash,
            },
        ),
        _policy_assertion(
            relation_id="ps:concept:policy-revision",
            context=context,
            condition=condition,
            provenance=provenance,
            roles={
                "profile": profile.profile_id,
                "operator": profile.revision.operator,
                "selection": profile.revision.selection,
            },
        ),
        _policy_assertion(
            relation_id="ps:concept:policy-merge",
            context=context,
            condition=condition,
            provenance=provenance,
            roles={
                "profile": profile.profile_id,
                "operator": profile.merge.operator.value,
                "conflict_strategy": profile.merge.conflict_strategy,
            },
        ),
        _policy_assertion(
            relation_id="ps:concept:policy-admissibility",
            context=context,
            condition=condition,
            provenance=provenance,
            roles={
                "profile": profile.profile_id,
                "conflict_free_basis": profile.admissibility.conflict_free_basis,
                "semantics": profile.admissibility.semantics.value,
            },
        ),
        _policy_assertion(
            relation_id="ps:concept:policy-source-trust",
            context=context,
            condition=condition,
            provenance=provenance,
            roles={
                "profile": profile.profile_id,
                "required_attitude": profile.source_trust.required_attitude,
                "unsigned_graph_policy": (
                    profile.source_trust.unsigned_graph_policy
                ),
            },
        ),
        _policy_assertion(
            relation_id="ps:concept:policy-escalation",
            context=context,
            condition=condition,
            provenance=provenance,
            roles={
                "profile": profile.profile_id,
                "unresolved_conflict": profile.escalation.unresolved_conflict,
                "missing_warrant": profile.escalation.missing_warrant,
            },
        ),
    )


def _policy_assertion(
    *,
    relation_id: str,
    context: ContextReference,
    condition: ConditionRef,
    provenance: ProvenanceGraphRef,
    roles: Mapping[str, object],
) -> SituatedAssertion:
    return SituatedAssertion(
        relation=RelationConceptRef(relation_id),
        role_bindings=RoleBindingSet(
            tuple(RoleBinding(role, str(value)) for role, value in roles.items())
        ),
        context=context,
        condition=condition,
        provenance_ref=provenance,
    )
