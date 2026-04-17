"""CKR-style defeasibility support contracts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from propstore.cel_types import CelExpr, to_cel_expr
from propstore.provenance import (
    NogoodWitness,
    ProvenanceNogood,
    ProvenancePolynomial,
    SupportEvidence,
    SupportQuality,
    live,
    why_provenance,
)


class DecidabilityStatus(StrEnum):
    DECIDABLE = "decidable"
    INCOMPLETE_SOUND = "incomplete_sound"


@dataclass(frozen=True)
class JustifiableException:
    target_claim: str
    exception_pattern: CelExpr | str
    justification_claims: tuple[str, ...]
    context: str
    support: SupportEvidence
    decidability_status: DecidabilityStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_claim", str(self.target_claim))
        object.__setattr__(self, "exception_pattern", to_cel_expr(self.exception_pattern))
        object.__setattr__(
            self,
            "justification_claims",
            tuple(str(claim) for claim in self.justification_claims),
        )
        object.__setattr__(self, "context", str(self.context))
        object.__setattr__(self, "decidability_status", DecidabilityStatus(self.decidability_status))
        if not isinstance(self.support, SupportEvidence):
            raise TypeError("JustifiableException support must be SupportEvidence")


@dataclass(frozen=True)
class LiftingRuleSupport:
    source_context: str
    target_context: str
    support: SupportEvidence

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_context", str(self.source_context))
        object.__setattr__(self, "target_context", str(self.target_context))
        if not isinstance(self.support, SupportEvidence):
            raise TypeError("LiftingRuleSupport support must be SupportEvidence")


@dataclass(frozen=True)
class ExceptionDefeat:
    defeated_use: str
    exception: JustifiableException
    support: SupportEvidence
    solver_witness: NogoodWitness | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "defeated_use", str(self.defeated_use))
        if not isinstance(self.exception, JustifiableException):
            raise TypeError("ExceptionDefeat exception must be JustifiableException")
        if not isinstance(self.support, SupportEvidence):
            raise TypeError("ExceptionDefeat support must be SupportEvidence")


def exception_live_support(
    exception: JustifiableException,
    nogoods: tuple[ProvenanceNogood, ...] = (),
) -> SupportEvidence:
    if not exception.justification_claims:
        return SupportEvidence(ProvenancePolynomial.zero(), exception.support.quality)
    return SupportEvidence(live(exception.support.polynomial, nogoods), exception.support.quality)


def exception_is_applied(
    exception: JustifiableException,
    nogoods: tuple[ProvenanceNogood, ...] = (),
) -> bool:
    return bool(exception_live_support(exception, nogoods).polynomial.terms)


def lift_exception(
    exception: JustifiableException,
    lifting_rule: LiftingRuleSupport,
) -> JustifiableException:
    if lifting_rule.source_context != exception.context:
        raise ValueError("Lifting rule source context must match the exception context")
    return replace(
        exception,
        context=lifting_rule.target_context,
        support=SupportEvidence(
            exception.support.polynomial * lifting_rule.support.polynomial,
            _compose_support_quality(exception.support.quality, lifting_rule.support.quality),
        ),
    )


def build_exception_defeat(
    defeated_use: str,
    exception: JustifiableException,
    *,
    solver_witness: NogoodWitness | None = None,
    solver_support: SupportEvidence | None = None,
    nogoods: tuple[ProvenanceNogood, ...] = (),
) -> ExceptionDefeat:
    support = exception_live_support(exception, nogoods)
    if solver_support is not None:
        support = SupportEvidence(
            support.polynomial * solver_support.polynomial,
            _compose_support_quality(support.quality, solver_support.quality),
        )
    return ExceptionDefeat(
        defeated_use=defeated_use,
        exception=exception,
        support=support,
        solver_witness=solver_witness,
    )


def exception_defeat_is_live(
    defeat: ExceptionDefeat,
    nogoods: tuple[ProvenanceNogood, ...] = (),
) -> bool:
    live_support = live(defeat.support.polynomial, nogoods)
    return bool(why_provenance(live_support))


def _compose_support_quality(left: SupportQuality, right: SupportQuality) -> SupportQuality:
    left = SupportQuality(left)
    right = SupportQuality(right)
    if left is right:
        return left
    if left is SupportQuality.EXACT:
        return right
    if right is SupportQuality.EXACT:
        return left
    return SupportQuality.MIXED


__all__ = [
    "DecidabilityStatus",
    "ExceptionDefeat",
    "JustifiableException",
    "LiftingRuleSupport",
    "build_exception_defeat",
    "exception_defeat_is_live",
    "exception_is_applied",
    "exception_live_support",
    "lift_exception",
]
