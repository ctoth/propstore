"""Assertion-scoped base-rate resolution for opinion construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping

from propstore.core.id_types import AssertionId
from propstore.opinion import Opinion
from propstore.provenance import Provenance, ProvenanceStatus


def _assertion_id(value: AssertionId, field_name: str) -> AssertionId:
    rendered = str(value)
    if not rendered.startswith("ps:assertion:"):
        raise ValueError(f"{field_name} must be a propstore assertion id")
    return AssertionId(rendered)


def _assertion_ids(values: tuple[AssertionId, ...], field_name: str) -> tuple[AssertionId, ...]:
    return tuple(_assertion_id(value, field_name) for value in values)


@dataclass(frozen=True)
class BaseRateProfile:
    """A sourced base-rate assertion for a target assertion."""

    profile_assertion_id: AssertionId
    target_assertion_id: AssertionId
    value: float
    provenance: Provenance
    evidence_assertion_ids: tuple[AssertionId, ...] = ()
    dependency_assertion_ids: tuple[AssertionId, ...] = ()
    stratum: int = 0

    def __post_init__(self) -> None:
        if self.value <= 0.0 or self.value >= 1.0:
            raise ValueError("BaseRateProfile.value must be in the open interval (0, 1)")
        if self.stratum < 0:
            raise ValueError("BaseRateProfile.stratum must be non-negative")
        object.__setattr__(
            self,
            "profile_assertion_id",
            _assertion_id(self.profile_assertion_id, "profile_assertion_id"),
        )
        object.__setattr__(
            self,
            "target_assertion_id",
            _assertion_id(self.target_assertion_id, "target_assertion_id"),
        )
        object.__setattr__(
            self,
            "evidence_assertion_ids",
            _assertion_ids(self.evidence_assertion_ids, "evidence_assertion_ids"),
        )
        object.__setattr__(
            self,
            "dependency_assertion_ids",
            _assertion_ids(self.dependency_assertion_ids, "dependency_assertion_ids"),
        )


@dataclass(frozen=True)
class BaseRateAssertionRecord:
    """Authored parameter assertion that can serve as a base-rate profile."""

    source_key: str
    claim_id: str
    concept: str
    value: float
    unit: str

    def __post_init__(self) -> None:
        if not self.source_key:
            raise ValueError("source_key is required")
        if not self.claim_id:
            raise ValueError("claim_id is required")
        if not self.concept:
            raise ValueError("concept is required")
        if self.value <= 0.0 or self.value >= 1.0:
            raise ValueError("BaseRateAssertionRecord.value must be in the open interval (0, 1)")
        if self.unit != "proportion":
            raise ValueError("base-rate assertion unit must be 'proportion'")

    @property
    def assertion_id(self) -> AssertionId:
        return AssertionId(f"ps:assertion:{self.source_key}:{self.claim_id}")

    @classmethod
    def from_parameter_claim(
        cls,
        *,
        source_key: str,
        claim_payload: Mapping[str, object],
    ) -> BaseRateAssertionRecord:
        if claim_payload.get("type") != "parameter":
            raise ValueError("base-rate source claim must be a parameter claim")

        claim_id = claim_payload.get("id")
        concept = claim_payload.get("concept")
        value = claim_payload.get("value")
        unit = claim_payload.get("unit")
        if not isinstance(claim_id, str):
            raise ValueError("base-rate source claim requires string id")
        if not isinstance(concept, str):
            raise ValueError("base-rate source claim requires string concept")
        if not isinstance(value, int | float):
            raise ValueError("base-rate source claim requires numeric value")
        if not isinstance(unit, str):
            raise ValueError("base-rate source claim requires string unit")

        return cls(
            source_key=source_key,
            claim_id=claim_id,
            concept=concept,
            value=float(value),
            unit=unit,
        )

    def to_profile(self, *, target_assertion_id: AssertionId) -> BaseRateProfile:
        return BaseRateProfile(
            profile_assertion_id=self.assertion_id,
            target_assertion_id=target_assertion_id,
            value=self.value,
            provenance=Provenance(
                status=ProvenanceStatus.STATED,
                witnesses=(),
                operations=(f"base_rate_assertion:{self.source_key}:{self.claim_id}",),
            ),
            evidence_assertion_ids=(self.assertion_id,),
        )


@dataclass(frozen=True)
class BaseRateResolved:
    assertion_id: AssertionId
    value: float
    profile_assertion_id: AssertionId
    evidence_assertion_ids: tuple[AssertionId, ...]
    provenance: Provenance


@dataclass(frozen=True)
class BaseRateUnresolved:
    assertion_id: AssertionId
    reason: str
    missing_fields: tuple[str, ...] = ("base_rate_profile",)


@dataclass(frozen=True)
class AssertionOpinion:
    assertion_id: AssertionId
    opinion: Opinion
    base_rate_assertion_id: AssertionId
    evidence_assertion_ids: tuple[AssertionId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "assertion_id",
            _assertion_id(self.assertion_id, "assertion_id"),
        )
        object.__setattr__(
            self,
            "base_rate_assertion_id",
            _assertion_id(self.base_rate_assertion_id, "base_rate_assertion_id"),
        )
        object.__setattr__(
            self,
            "evidence_assertion_ids",
            _assertion_ids(self.evidence_assertion_ids, "evidence_assertion_ids"),
        )


@dataclass(frozen=True)
class BaseRateResolver:
    profiles: tuple[BaseRateProfile, ...]
    _by_target: dict[AssertionId, BaseRateProfile] = field(init=False, repr=False)

    def __init__(self, profiles: tuple[BaseRateProfile, ...]) -> None:
        by_target: dict[AssertionId, BaseRateProfile] = {}
        for profile in profiles:
            if profile.target_assertion_id in by_target:
                raise ValueError(f"duplicate base-rate profile for {profile.target_assertion_id}")
            by_target[profile.target_assertion_id] = profile
        object.__setattr__(self, "profiles", tuple(profiles))
        object.__setattr__(self, "_by_target", by_target)

    def resolve(self, assertion_id: AssertionId) -> BaseRateResolved | BaseRateUnresolved:
        assertion = _assertion_id(assertion_id, "assertion_id")
        return self._resolve(assertion, seen=frozenset())

    def _resolve(
        self,
        assertion_id: AssertionId,
        *,
        seen: frozenset[AssertionId],
    ) -> BaseRateResolved | BaseRateUnresolved:
        if assertion_id in seen:
            return BaseRateUnresolved(assertion_id, "recursive_base_rate")

        profile = self._by_target.get(assertion_id)
        if profile is None:
            return BaseRateUnresolved(assertion_id, "missing_base_rate")

        next_seen = seen | frozenset((assertion_id,))
        for dependency_id in profile.dependency_assertion_ids:
            dependency = self._by_target.get(dependency_id)
            if dependency is None:
                return BaseRateUnresolved(assertion_id, "missing_base_rate")
            if dependency.stratum >= profile.stratum:
                return BaseRateUnresolved(assertion_id, "recursive_base_rate")
            resolved = self._resolve(dependency_id, seen=next_seen)
            if isinstance(resolved, BaseRateUnresolved):
                return BaseRateUnresolved(assertion_id, resolved.reason)

        return BaseRateResolved(
            assertion_id=assertion_id,
            value=profile.value,
            profile_assertion_id=profile.profile_assertion_id,
            evidence_assertion_ids=profile.evidence_assertion_ids,
            provenance=profile.provenance,
        )


def construct_assertion_opinion(
    *,
    assertion_id: AssertionId,
    belief: float,
    disbelief: float,
    uncertainty: float,
    resolver: BaseRateResolver,
    provenance: Provenance | None = None,
) -> AssertionOpinion | BaseRateUnresolved:
    assertion = _assertion_id(assertion_id, "assertion_id")
    resolved = resolver.resolve(assertion)
    if isinstance(resolved, BaseRateUnresolved):
        return resolved

    return AssertionOpinion(
        assertion_id=assertion,
        opinion=Opinion(
            belief,
            disbelief,
            uncertainty,
            resolved.value,
            provenance if provenance is not None else resolved.provenance,
        ),
        base_rate_assertion_id=resolved.profile_assertion_id,
        evidence_assertion_ids=resolved.evidence_assertion_ids,
    )
