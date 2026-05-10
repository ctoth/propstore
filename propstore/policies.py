"""Inspectable policy profiles for epistemic workflows."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from quire.hashing import canonical_json_bytes

from propstore.core.assertions.refs import ConditionRef, ContextReference, ProvenanceGraphRef
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet
from propstore.core.assertions.situated import SituatedAssertion
from propstore.support_revision.belief_set_adapter import DEFAULT_ITERATED_OPERATOR
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


def _plain(value: Any) -> Any:
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


def _hash(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(_plain(value))).hexdigest()


@dataclass(frozen=True, order=True)
class RevisionPolicy:
    operator: str = DEFAULT_ITERATED_OPERATOR
    selection: str = "minimal_incision"
    entrenchment: str = "support_sensitive"
    allow_reintroduction: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> RevisionPolicy:
        payload = {} if data is None else data
        return cls(
            operator=str(payload.get("operator", DEFAULT_ITERATED_OPERATOR)),
            selection=str(payload.get("selection", "minimal_incision")),
            entrenchment=str(payload.get("entrenchment", "support_sensitive")),
            allow_reintroduction=bool(payload.get("allow_reintroduction", False)),
        )

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
            object.__setattr__(self, "branch_filter", tuple(str(item) for item in self.branch_filter))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> MergePolicy:
        payload = {} if data is None else data
        branch_filter = payload.get("branch_filter")
        return cls(
            operator=payload.get("operator", MergeOperator.SIGMA),
            conflict_strategy=str(payload.get("conflict_strategy", "surface_conflicts")),
            branch_filter=None if branch_filter is None else tuple(str(item) for item in branch_filter),
            require_witnesses=bool(payload.get("require_witnesses", True)),
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

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> AdmissibilityProfile:
        payload = {} if data is None else data
        return cls(
            reasoning_backend=payload.get("reasoning_backend", ReasoningBackend.CLAIM_GRAPH),
            semantics=payload.get("semantics", ArgumentationSemantics.GROUNDED),
            conflict_free_basis=str(payload.get("conflict_free_basis", "attack")),
            comparison=str(payload.get("comparison", "elitist")),
            link=str(payload.get("link", "last")),
            decision_criterion=str(payload.get("decision_criterion", "pignistic")),
            pessimism_index=float(payload.get("pessimism_index", 0.5)),
        )

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

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> SourceTrustProfile:
        payload = {} if data is None else data
        return cls(
            accepted_authorities=tuple(str(item) for item in payload.get("accepted_authorities", ())),
            required_attitude=str(payload.get("required_attitude", "asserted")),
            unsigned_graph_policy=str(payload.get("unsigned_graph_policy", "quote_only")),
            require_digest=bool(payload.get("require_digest", False)),
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

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> EscalationPolicy:
        payload = {} if data is None else data
        return cls(
            unresolved_conflict=str(payload.get("unresolved_conflict", "queue_investigation")),
            missing_warrant=str(payload.get("missing_warrant", "mark_untrusted")),
            low_trust=str(payload.get("low_trust", "require_review")),
        )

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
            raise ValueError(f"unsupported policy profile version: {self.schema_version}")
        if not isinstance(self.revision, RevisionPolicy):
            object.__setattr__(self, "revision", RevisionPolicy.from_dict(_as_mapping(self.revision, "revision")))
        if not isinstance(self.merge, MergePolicy):
            object.__setattr__(self, "merge", MergePolicy.from_dict(_as_mapping(self.merge, "merge")))
        if not isinstance(self.admissibility, AdmissibilityProfile):
            object.__setattr__(
                self,
                "admissibility",
                AdmissibilityProfile.from_dict(_as_mapping(self.admissibility, "admissibility")),
            )
        if not isinstance(self.source_trust, SourceTrustProfile):
            object.__setattr__(
                self,
                "source_trust",
                SourceTrustProfile.from_dict(_as_mapping(self.source_trust, "source_trust")),
            )
        if not isinstance(self.escalation, EscalationPolicy):
            object.__setattr__(
                self,
                "escalation",
                EscalationPolicy.from_dict(_as_mapping(self.escalation, "escalation")),
            )
        object.__setattr__(self, "profile_id", self._derived_profile_id())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PolicyProfile:
        schema_version = str(data.get("schema_version", _PROFILE_VERSION))
        recorded_profile_id = str(data.get("profile_id", ""))
        profile = cls(
            revision=RevisionPolicy.from_dict(_optional_mapping(data.get("revision"), "revision")),
            merge=MergePolicy.from_dict(_optional_mapping(data.get("merge"), "merge")),
            admissibility=AdmissibilityProfile.from_dict(
                _optional_mapping(data.get("admissibility"), "admissibility")
            ),
            source_trust=SourceTrustProfile.from_dict(
                _optional_mapping(data.get("source_trust"), "source_trust")
            ),
            escalation=EscalationPolicy.from_dict(_optional_mapping(data.get("escalation"), "escalation")),
            label=str(data.get("label", "default")),
            schema_version=schema_version,
        )
        if recorded_profile_id and recorded_profile_id != profile.profile_id:
            raise ValueError("policy profile_id does not match policy content")
        recorded_hash = data.get("content_hash")
        if recorded_hash is not None and str(recorded_hash) != profile.content_hash:
            raise ValueError("policy profile content_hash does not match payload")
        return profile

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
                "unsigned_graph_policy": profile.source_trust.unsigned_graph_policy,
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
            tuple(RoleBinding(role, value) for role, value in roles.items())
        ),
        context=context,
        condition=condition,
        provenance_ref=provenance,
    )


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any] | None:
    if value is None:
        return None
    return _as_mapping(value, field_name)


def _as_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"policy field '{field_name}' must be a mapping")
    return value
