"""CKR-style defeasibility — satisfaction semantics and the support contract.

This is the Phase 4 *non-ASPIC* half of contextual defeasibility (CLAUDE.md
``propstore.defeasibility``): it decides whether a contextual claim use
``ist(c, p)`` is *excepted* by an authored CKR-style justifiable exception, and
it owns the provenance-semiring *support contract* that keeps an exception's
liveness honest. The CKR-exception -> Dung-defeat injection at the ASPIC+
boundary (``apply_exception_defeats_to_csaf``) lands in Phase 5 once the CSAF
surface exists; it is deliberately absent here.

Substrate boundary (CLAUDE.md):

* CEL is condition-ir's. Pattern gating calls ``check_condition_ir`` and the
  package ``ConditionSolver`` directly; there is no propstore CEL re-spelling and
  the free-variable walk reads condition-ir's own IR node types.
* Support is provenance-semiring's. ``SupportEvidence`` / ``ProvenancePolynomial``
  / ``live`` / ``why_provenance`` are imported and used directly — propstore adds
  no parallel polynomial type and no ``to_X`` / ``from_X`` conversion.
* Non-commitment: an exception whose support is killed by a nogood is *not*
  deleted; it simply stops being live (``exception_live_support`` returns the
  zero polynomial). A solver ``UNKNOWN`` or an unbound pattern variable is
  reported as incomplete soundness, never silently turned into a positive
  exception.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Protocol, TypeAlias

from argumentation.core.dung import ArgumentationFramework
from argumentation.structured.aspic.aspic import CSAF, Argument, Literal, conc
from condition_ir import (
    CelExpr,
    CheckedCondition,
    ConceptInfo,
    ConditionBinary,
    ConditionIR,
    ConditionLiteral,
    ConditionMembership,
    ConditionReference,
    ConditionUnary,
    SolverResult,
    SolverSat,
    SolverUnsat,
    Z3TranslationError,
    check_condition_ir,
    to_cel_expr,
)
from provenance_semiring import (
    NogoodWitness,
    ProvenanceNogood,
    ProvenancePolynomial,
    SupportEvidence,
    SupportQuality,
    live,
    why_provenance,
)

CelScalar: TypeAlias = str | int | float | bool


class DecidabilityStatus(StrEnum):
    """How sound the satisfaction verdict is, given the authored material.

    ``DECIDABLE`` means the solver settled every relevant pattern.
    ``INCOMPLETE_SOUND`` means a solver returned ``UNKNOWN`` (honest ignorance —
    the verdict is sound but not complete). ``AUTHORING_UNBOUND`` means a pattern
    could not be evaluated against the use's bindings (a free variable was left
    unbound, or the pattern did not translate).
    """

    DECIDABLE = "decidable"
    INCOMPLETE_SOUND = "incomplete_sound"
    AUTHORING_UNBOUND = "authoring_unbound"


class ClaimApplicability(StrEnum):
    """Whether a contextual claim use holds, is excepted, or is unknown."""

    HOLDS = "holds"
    EXCEPTED = "excepted"
    UNKNOWN = "unknown"


class ExceptionPolicyIssueKind(StrEnum):
    """A non-fatal authoring policy signal raised during evaluation."""

    MULTIPLE_APPLICABLE_EXCEPTIONS = "multiple_applicable_exceptions"


class PatternSelectionStatus(StrEnum):
    """Internal outcome of trying to select a use with an exception pattern."""

    INCOMPLETE_SOUND = "incomplete_sound"
    AUTHORING_UNBOUND = "authoring_unbound"


class ExceptionPatternSolver(Protocol):
    """The condition-ir solver surface used to gate exception patterns.

    condition-ir's ``ConditionSolver`` satisfies this structurally; the protocol
    keeps the dependency to exactly the two members the gate needs.
    """

    @property
    def registry(self) -> Mapping[str, ConceptInfo]: ...

    def is_condition_satisfied_result(
        self,
        condition: CheckedCondition,
        bindings: Mapping[str, CelScalar],
    ) -> SolverResult: ...


@dataclass(frozen=True, order=True)
class CelBinding:
    """One name -> scalar binding supplied with a contextual claim use."""

    name: str
    value: CelScalar

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))


@dataclass(frozen=True)
class ContextualClaimUse:
    """A use of claim ``claim`` in context ``context`` with bound parameters."""

    context: str
    claim: str
    bindings: tuple[CelBinding, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "context", str(self.context))
        object.__setattr__(self, "claim", str(self.claim))
        bindings = tuple(self.bindings)
        names = [binding.name for binding in bindings]
        if len(names) != len(set(names)):
            raise ValueError("ContextualClaimUse bindings must have unique names")
        object.__setattr__(self, "bindings", bindings)

    @property
    def defeated_use_id(self) -> str:
        return f"ist({self.context}, {self.claim})"

    def binding_map(self) -> Mapping[str, CelScalar]:
        return {binding.name: binding.value for binding in self.bindings}


@dataclass(frozen=True)
class JustifiableException:
    """A CKR justifiable exception authored against a claim in a context."""

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
        object.__setattr__(
            self, "decidability_status", DecidabilityStatus(self.decidability_status)
        )


@dataclass(frozen=True)
class LiftingRuleSupport:
    """A lifting rule's licensing support for carrying an exception across contexts."""

    source_context: str
    target_context: str
    support: SupportEvidence

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_context", str(self.source_context))
        object.__setattr__(self, "target_context", str(self.target_context))


@dataclass(frozen=True)
class ExceptionDefeat:
    """The defeat an applied exception contributes against a contextual use."""

    defeated_use: str
    exception: JustifiableException
    support: SupportEvidence
    solver_witness: NogoodWitness | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "defeated_use", str(self.defeated_use))


@dataclass(frozen=True)
class ExceptionPolicyIssue:
    """A non-fatal policy signal (e.g. more than one exception applied)."""

    kind: ExceptionPolicyIssueKind
    exceptions: tuple[JustifiableException, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", ExceptionPolicyIssueKind(self.kind))
        object.__setattr__(self, "exceptions", tuple(self.exceptions))


@dataclass(frozen=True)
class ContextualClaimResult:
    """The verdict of evaluating one contextual claim use against exceptions."""

    use: ContextualClaimUse
    applicability: ClaimApplicability
    applied_exceptions: tuple[JustifiableException, ...]
    defeats: tuple[ExceptionDefeat, ...]
    policy_issues: tuple[ExceptionPolicyIssue, ...]
    decidability_status: DecidabilityStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "applicability", ClaimApplicability(self.applicability))
        object.__setattr__(self, "applied_exceptions", tuple(self.applied_exceptions))
        object.__setattr__(self, "defeats", tuple(self.defeats))
        object.__setattr__(self, "policy_issues", tuple(self.policy_issues))
        object.__setattr__(
            self, "decidability_status", DecidabilityStatus(self.decidability_status)
        )


def exception_live_support(
    exception: JustifiableException,
    nogoods: tuple[ProvenanceNogood, ...] = (),
) -> SupportEvidence:
    """The exception's support after applying nogoods.

    An exception with no justification claims has zero support (it cannot be
    applied). Otherwise the support polynomial is reduced by the nogoods via
    provenance-semiring's ``live`` — the exception object is never deleted, only
    its liveness changes (non-commitment).
    """

    if not exception.justification_claims:
        return SupportEvidence(ProvenancePolynomial.zero(), exception.support.quality)
    return SupportEvidence(
        live(exception.support.polynomial, nogoods), exception.support.quality
    )


def exception_is_applied(
    exception: JustifiableException,
    nogoods: tuple[ProvenanceNogood, ...] = (),
) -> bool:
    """Whether the exception still has live support under ``nogoods``."""

    return bool(exception_live_support(exception, nogoods).polynomial.terms)


def lift_exception(
    exception: JustifiableException,
    lifting_rule: LiftingRuleSupport,
) -> JustifiableException:
    """Carry an exception from its context to the lifting rule's target context.

    The lifted exception's support is the product of the exception's own support
    and the lifting rule's support (both must hold), composing their qualities.
    """

    if lifting_rule.source_context != exception.context:
        raise ValueError("Lifting rule source context must match the exception context")
    return replace(
        exception,
        context=lifting_rule.target_context,
        support=SupportEvidence(
            exception.support.polynomial * lifting_rule.support.polynomial,
            _compose_support_quality(
                exception.support.quality, lifting_rule.support.quality
            ),
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
    """Construct the defeat an applied exception contributes against a use."""

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
    """Whether a defeat's support survives ``nogoods`` (has a why-provenance)."""

    live_support = live(defeat.support.polynomial, nogoods)
    return bool(why_provenance(live_support))


def evaluate_contextual_claim(
    use: ContextualClaimUse,
    exceptions: Iterable[JustifiableException],
    *,
    lifting_rules: Iterable[LiftingRuleSupport] = (),
    nogoods: tuple[ProvenanceNogood, ...] = (),
    solver: ExceptionPatternSolver | None = None,
) -> ContextualClaimResult:
    """Decide whether a contextual claim use is excepted.

    Local exceptions are considered in their own context. Non-local exceptions
    become candidates only when an explicit lifting rule licenses that
    source/target context pair. Solver ``UNKNOWN`` and CEL translation failures
    are reported as incomplete soundness and never converted into a positive
    exception.
    """

    applied: list[JustifiableException] = []
    defeats: list[ExceptionDefeat] = []
    saw_incomplete = False
    saw_authoring_unbound = False

    for exception in _candidate_exceptions(use, exceptions, lifting_rules):
        if exception.target_claim != use.claim:
            continue
        if not exception_is_applied(exception, nogoods):
            continue
        pattern_result = _pattern_selects_use(
            to_cel_expr(exception.exception_pattern),
            use,
            solver,
        )
        if pattern_result is PatternSelectionStatus.AUTHORING_UNBOUND:
            saw_authoring_unbound = True
            continue
        if pattern_result is PatternSelectionStatus.INCOMPLETE_SOUND:
            saw_incomplete = True
            continue
        if not pattern_result:
            continue
        applied.append(exception)
        defeats.append(
            build_exception_defeat(use.defeated_use_id, exception, nogoods=nogoods)
        )

    policy_issues: tuple[ExceptionPolicyIssue, ...] = ()
    if len(applied) > 1:
        policy_issues = (
            ExceptionPolicyIssue(
                ExceptionPolicyIssueKind.MULTIPLE_APPLICABLE_EXCEPTIONS,
                tuple(applied),
            ),
        )

    if applied:
        applicability = ClaimApplicability.EXCEPTED
    elif saw_incomplete or saw_authoring_unbound:
        applicability = ClaimApplicability.UNKNOWN
    else:
        applicability = ClaimApplicability.HOLDS

    decidability_status = DecidabilityStatus.DECIDABLE
    if saw_authoring_unbound:
        decidability_status = DecidabilityStatus.AUTHORING_UNBOUND
    elif saw_incomplete or any(
        exception.decidability_status is DecidabilityStatus.INCOMPLETE_SOUND
        for exception in applied
    ):
        decidability_status = DecidabilityStatus.INCOMPLETE_SOUND

    return ContextualClaimResult(
        use=use,
        applicability=applicability,
        applied_exceptions=tuple(applied),
        defeats=tuple(defeats),
        policy_issues=policy_issues,
        decidability_status=decidability_status,
    )


def _candidate_exceptions(
    use: ContextualClaimUse,
    exceptions: Iterable[JustifiableException],
    lifting_rules: Iterable[LiftingRuleSupport],
) -> tuple[JustifiableException, ...]:
    candidates: list[JustifiableException] = []
    rules = tuple(lifting_rules)
    for exception in exceptions:
        if exception.context == use.context:
            candidates.append(exception)
            continue
        for lifting_rule in rules:
            if (
                lifting_rule.source_context == exception.context
                and lifting_rule.target_context == use.context
            ):
                candidates.append(lift_exception(exception, lifting_rule))
    return tuple(candidates)


def _pattern_selects_use(
    pattern: CelExpr,
    use: ContextualClaimUse,
    solver: ExceptionPatternSolver | None,
) -> bool | PatternSelectionStatus:
    source = str(pattern).strip()
    lowered = source.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    bindings = use.binding_map()
    if solver is None:
        return PatternSelectionStatus.INCOMPLETE_SOUND
    registry = solver.registry

    try:
        condition = check_condition_ir(str(pattern), registry)
    except (ValueError, Z3TranslationError):
        return PatternSelectionStatus.AUTHORING_UNBOUND
    names = _condition_ir_names(condition.ir)
    if not names <= set(bindings):
        return PatternSelectionStatus.AUTHORING_UNBOUND

    try:
        result = solver.is_condition_satisfied_result(condition, bindings)
    except Z3TranslationError:
        return PatternSelectionStatus.AUTHORING_UNBOUND
    if isinstance(result, SolverSat):
        return True
    if isinstance(result, SolverUnsat):
        return False
    # SolverUnknown — honest ignorance, not a positive exception.
    return PatternSelectionStatus.INCOMPLETE_SOUND


def _condition_ir_names(condition: ConditionIR) -> frozenset[str]:
    names: set[str] = set()
    _collect_condition_ir_names(condition, names)
    return frozenset(names)


def _collect_condition_ir_names(condition: ConditionIR, names: set[str]) -> None:
    if isinstance(condition, ConditionReference):
        names.add(condition.source_name)
        return
    if isinstance(condition, ConditionLiteral):
        return
    if isinstance(condition, ConditionUnary):
        _collect_condition_ir_names(condition.operand, names)
        return
    if isinstance(condition, ConditionBinary):
        _collect_condition_ir_names(condition.left, names)
        _collect_condition_ir_names(condition.right, names)
        return
    if isinstance(condition, ConditionMembership):
        _collect_condition_ir_names(condition.element, names)
        for option in condition.options:
            _collect_condition_ir_names(option, names)
        return
    # ConditionChoice — the remaining IR node kind.
    _collect_condition_ir_names(condition.condition, names)
    _collect_condition_ir_names(condition.when_true, names)
    _collect_condition_ir_names(condition.when_false, names)


def apply_exception_defeats_to_csaf(
    csaf: CSAF,
    results: Iterable[ContextualClaimResult],
) -> CSAF:
    """Return a CSAF whose Dung layer includes CKR exception defeats.

    ASPIC+ remains responsible for structural argument construction; CKR
    contributes only extra defeat edges (CLAUDE.md: ASPIC+ does not own contextual
    exception semantics — propstore decides applicability and injects the
    defeats). For each ``EXCEPTED`` use, every argument concluding a justification
    claim defeats every argument concluding the excepted contextual claim. A use
    whose claim has no ASPIC argument is an authoring error (``ValueError``); an
    exception whose justification claims have no argument is skipped with a warning
    rather than silently fabricating a defeat.
    """

    extra_defeats: set[tuple[Argument, Argument]] = set()
    for result in results:
        if result.applicability is not ClaimApplicability.EXCEPTED:
            continue
        target_arguments = _arguments_concluding(csaf, result.use.claim)
        if not target_arguments:
            raise ValueError(
                "CKR exception result targets a claim with no ASPIC argument: "
                f"{result.use.claim!r}"
            )
        for exception in result.applied_exceptions:
            attacker_arguments: set[Argument] = set()
            for justification_claim in exception.justification_claims:
                attacker_arguments.update(_arguments_concluding(csaf, justification_claim))
            if not attacker_arguments:
                warnings.warn(
                    "CKR exception has no ASPIC argument for its justification claims; "
                    "skipping that exception",
                    UserWarning,
                    stacklevel=2,
                )
                continue
            for attacker in attacker_arguments:
                for target in target_arguments:
                    if attacker != target:
                        extra_defeats.add((attacker, target))

    if not extra_defeats:
        return csaf

    defeat_ids = frozenset(
        (csaf.arg_to_id[attacker], csaf.arg_to_id[target])
        for attacker, target in extra_defeats
    )
    framework = ArgumentationFramework(
        arguments=csaf.framework.arguments,
        defeats=csaf.framework.defeats | defeat_ids,
        attacks=csaf.framework.attacks,
    )
    return replace(
        csaf,
        defeats=csaf.defeats | frozenset(extra_defeats),
        framework=framework,
    )


def _arguments_concluding(csaf: CSAF, claim_id: str) -> set[Argument]:
    return {
        argument
        for argument in csaf.arguments
        if _literal_concludes_claim(conc(argument), claim_id)
    }


def _literal_concludes_claim(literal: Literal, claim_id: str) -> bool:
    atom = literal.atom
    if atom.predicate == claim_id:
        return True
    return atom.predicate == "ist" and atom.arguments[-1:] == (claim_id,)


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
    "CelBinding",
    "CelScalar",
    "ClaimApplicability",
    "ContextualClaimResult",
    "ContextualClaimUse",
    "DecidabilityStatus",
    "ExceptionDefeat",
    "ExceptionPatternSolver",
    "ExceptionPolicyIssue",
    "ExceptionPolicyIssueKind",
    "JustifiableException",
    "LiftingRuleSupport",
    "apply_exception_defeats_to_csaf",
    "build_exception_defeat",
    "evaluate_contextual_claim",
    "exception_defeat_is_live",
    "exception_is_applied",
    "exception_live_support",
    "lift_exception",
]
