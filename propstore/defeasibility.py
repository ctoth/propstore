"""CKR-style defeasibility support contracts."""

from __future__ import annotations

import warnings
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Protocol, TypeAlias

from propstore.cel_checker import (
    ASTNode,
    BinaryOpNode,
    InNode,
    NameNode,
    TernaryNode,
    UnaryOpNode,
    parse_cel,
)
from propstore.cel_types import CelExpr, to_cel_expr
from argumentation.aspic import Argument, CSAF, conc
from argumentation.dung import ArgumentationFramework
from propstore.provenance import (
    NogoodWitness,
    ProvenanceNogood,
    ProvenancePolynomial,
    SupportEvidence,
    SupportQuality,
    live,
    why_provenance,
)
from propstore.z3_conditions import (
    SolverResult,
    SolverSat,
    SolverUnknown,
    SolverUnsat,
    Z3TranslationError,
)

CelScalar: TypeAlias = str | int | float | bool


class DecidabilityStatus(StrEnum):
    DECIDABLE = "decidable"
    INCOMPLETE_SOUND = "incomplete_sound"
    AUTHORING_UNBOUND = "authoring_unbound"


class ClaimApplicability(StrEnum):
    HOLDS = "holds"
    EXCEPTED = "excepted"
    UNKNOWN = "unknown"


class ExceptionPolicyIssueKind(StrEnum):
    MULTIPLE_APPLICABLE_EXCEPTIONS = "multiple_applicable_exceptions"


class PatternSelectionStatus(StrEnum):
    INCOMPLETE_SOUND = "incomplete_sound"
    AUTHORING_UNBOUND = "authoring_unbound"


class ExceptionPatternSolver(Protocol):
    def is_condition_satisfied_result(
        self,
        condition: CelExpr,
        bindings: Mapping[str, CelScalar],
    ) -> SolverResult: ...


@dataclass(frozen=True, order=True)
class CelBinding:
    name: str
    value: CelScalar

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        value = self.value
        if not isinstance(value, str | int | float | bool):
            raise TypeError("CEL binding value must be a scalar")


@dataclass(frozen=True)
class ContextualClaimUse:
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


@dataclass(frozen=True)
class ExceptionPolicyIssue:
    kind: ExceptionPolicyIssueKind
    exceptions: tuple[JustifiableException, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", ExceptionPolicyIssueKind(self.kind))
        object.__setattr__(self, "exceptions", tuple(self.exceptions))


@dataclass(frozen=True)
class ContextualClaimResult:
    use: ContextualClaimUse
    applicability: ClaimApplicability
    applied_exceptions: tuple[JustifiableException, ...]
    defeats: tuple[ExceptionDefeat, ...]
    policy_issues: tuple[ExceptionPolicyIssue, ...]
    decidability_status: DecidabilityStatus

    def __post_init__(self) -> None:
        if not isinstance(self.use, ContextualClaimUse):
            raise TypeError("ContextualClaimResult use must be ContextualClaimUse")
        object.__setattr__(self, "applicability", ClaimApplicability(self.applicability))
        object.__setattr__(self, "applied_exceptions", tuple(self.applied_exceptions))
        object.__setattr__(self, "defeats", tuple(self.defeats))
        object.__setattr__(self, "policy_issues", tuple(self.policy_issues))
        object.__setattr__(self, "decidability_status", DecidabilityStatus(self.decidability_status))


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


def evaluate_contextual_claim(
    use: ContextualClaimUse,
    exceptions: Iterable[JustifiableException],
    *,
    lifting_rules: Iterable[LiftingRuleSupport] = (),
    nogoods: tuple[ProvenanceNogood, ...] = (),
    solver: ExceptionPatternSolver | None = None,
) -> ContextualClaimResult:
    """Decide whether a contextual claim use is excepted.

    Local exceptions are considered in their own context. Non-local
    exceptions become candidates only when an explicit lifting rule licenses
    that source/target context pair. Solver ``UNKNOWN`` and CEL translation
    failures are reported as incomplete soundness and never converted into a
    positive exception.
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
            build_exception_defeat(
                use.defeated_use_id,
                exception,
                nogoods=nogoods,
            )
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


def apply_exception_defeats_to_csaf(
    csaf: CSAF,
    results: Iterable[ContextualClaimResult],
) -> CSAF:
    """Return a CSAF whose Dung layer includes CKR exception defeats.

    ASPIC+ remains responsible for structural argument construction. CKR
    contributes only extra defeat edges: justification-claim arguments attack
    arguments concluding the excepted contextual claim.
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
                attacker_arguments.update(
                    _arguments_concluding(csaf, justification_claim)
                )
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


def _arguments_concluding(csaf: CSAF, claim_id: str) -> set[Argument]:
    return {
        argument
        for argument in csaf.arguments
        if conc(argument).atom.predicate == claim_id
    }


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
    names = _cel_names(pattern)
    if names is None:
        return PatternSelectionStatus.AUTHORING_UNBOUND
    if not names <= set(bindings):
        return PatternSelectionStatus.AUTHORING_UNBOUND
    if solver is None:
        return PatternSelectionStatus.INCOMPLETE_SOUND

    try:
        result = solver.is_condition_satisfied_result(pattern, bindings)
    except Z3TranslationError:
        return PatternSelectionStatus.AUTHORING_UNBOUND
    if isinstance(result, SolverSat):
        return True
    if isinstance(result, SolverUnsat):
        return False
    if isinstance(result, SolverUnknown):
        return PatternSelectionStatus.INCOMPLETE_SOUND
    return PatternSelectionStatus.INCOMPLETE_SOUND


def _cel_names(pattern: CelExpr) -> frozenset[str] | None:
    try:
        ast = parse_cel(pattern)
    except ValueError:
        return None
    names: set[str] = set()
    _collect_cel_names(ast, names)
    return frozenset(names)


def _collect_cel_names(node: ASTNode, names: set[str]) -> None:
    if isinstance(node, NameNode):
        names.add(node.name)
        return
    if isinstance(node, BinaryOpNode):
        _collect_cel_names(node.left, names)
        _collect_cel_names(node.right, names)
        return
    if isinstance(node, UnaryOpNode):
        _collect_cel_names(node.operand, names)
        return
    if isinstance(node, InNode):
        _collect_cel_names(node.expr, names)
        for value in node.values:
            _collect_cel_names(value, names)
        return
    if isinstance(node, TernaryNode):
        _collect_cel_names(node.condition, names)
        _collect_cel_names(node.true_branch, names)
        _collect_cel_names(node.false_branch, names)


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
