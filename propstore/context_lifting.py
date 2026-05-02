"""First-class context references and explicit lifting rules.

This is the McCarthy/Guha Phase 4 context surface: contexts are logical
objects, and cross-context visibility exists only through authored lifting
rules. There is no ancestry-based default visibility.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.core import assertions as _assertions
from propstore.core.id_types import ContextId, to_context_id
from propstore.defeasibility import (
    DecidabilityStatus,
    ExceptionDefeat,
    ExceptionPatternSolver,
    JustifiableException,
    CelScalar,
    build_exception_defeat,
)
from propstore.provenance import (
    NogoodWitness,
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
)
from propstore.z3_conditions import (
    SolverSat,
    SolverUnknown,
    SolverUnsat,
    Z3TranslationError,
)


@dataclass(frozen=True)
class IstProposition:
    context: _assertions.ContextReference
    proposition_id: str


class LiftingMode(StrEnum):
    BRIDGE = "bridge"
    SPECIALIZATION = "specialization"
    DECONTEXTUALIZATION = "decontextualization"


class LiftingDecisionStatus(StrEnum):
    LIFTED = "lifted"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LiftingRule:
    id: str
    source: _assertions.ContextReference
    target: _assertions.ContextReference
    conditions: tuple[CelExpr, ...] = ()
    mode: LiftingMode = LiftingMode.BRIDGE
    justification: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "conditions", to_cel_exprs(self.conditions))


@dataclass(frozen=True)
class LiftingException:
    id: str
    rule_id: str
    target: _assertions.ContextReference
    proposition_id: str
    clashing_set: tuple[str, ...] = ()
    justification: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("lifting exception id must be non-empty")
        if not self.rule_id:
            raise ValueError("lifting exception rule_id must be non-empty")
        if not self.proposition_id:
            raise ValueError("lifting exception proposition_id must be non-empty")
        object.__setattr__(
            self,
            "clashing_set",
            tuple(str(item) for item in self.clashing_set),
        )


@dataclass(frozen=True)
class LiftingDecisionProvenance:
    rule_id: str
    source_context_id: ContextId
    target_context_id: ContextId
    source_proposition_id: str
    status: LiftingDecisionStatus
    justification: str | None = None
    exception_id: str | None = None
    clashing_set: tuple[str, ...] = ()
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", str(self.rule_id))
        object.__setattr__(self, "source_context_id", to_context_id(self.source_context_id))
        object.__setattr__(self, "target_context_id", to_context_id(self.target_context_id))
        object.__setattr__(self, "source_proposition_id", str(self.source_proposition_id))
        object.__setattr__(self, "status", LiftingDecisionStatus(self.status))
        if self.justification is not None:
            object.__setattr__(self, "justification", str(self.justification))
        if self.exception_id is not None:
            object.__setattr__(self, "exception_id", str(self.exception_id))
        if self.diagnostic is not None:
            object.__setattr__(self, "diagnostic", str(self.diagnostic))
        object.__setattr__(
            self,
            "clashing_set",
            tuple(str(item) for item in self.clashing_set),
        )

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "rule_id": self.rule_id,
            "source_context_id": str(self.source_context_id),
            "target_context_id": str(self.target_context_id),
            "source_proposition_id": self.source_proposition_id,
            "status": self.status.value,
        }
        if self.exception_id is not None:
            payload["exception_id"] = self.exception_id
        if self.justification is not None:
            payload["justification"] = self.justification
        if self.clashing_set:
            payload["clashing_set"] = list(self.clashing_set)
        if self.diagnostic is not None:
            payload["diagnostic"] = self.diagnostic
        return payload


@dataclass(frozen=True)
class LiftingDecision:
    source_context: _assertions.ContextReference
    target_context: _assertions.ContextReference
    proposition_id: str
    status: LiftingDecisionStatus
    mode: LiftingMode
    rule_id: str
    rule_conditions: tuple[CelExpr, ...]
    support: SupportEvidence
    provenance: LiftingDecisionProvenance
    exception: ExceptionDefeat | None = None
    solver_witness: NogoodWitness | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposition_id", str(self.proposition_id))
        object.__setattr__(self, "status", LiftingDecisionStatus(self.status))
        object.__setattr__(self, "mode", LiftingMode(self.mode))
        object.__setattr__(self, "rule_conditions", to_cel_exprs(self.rule_conditions))
        if not isinstance(self.support, SupportEvidence):
            raise TypeError("LiftingDecision support must be SupportEvidence")
        if not isinstance(self.provenance, LiftingDecisionProvenance):
            raise TypeError("LiftingDecision provenance must be LiftingDecisionProvenance")
        if self.exception is not None and not isinstance(self.exception, ExceptionDefeat):
            raise TypeError("LiftingDecision exception must be ExceptionDefeat")


@dataclass(frozen=True)
class LiftedAssertion:
    assertion: IstProposition
    source_assertion: IstProposition
    rule_id: str
    mode: LiftingMode
    status: LiftingDecisionStatus
    decision: LiftingDecision
    exception_id: str | None = None
    justification: str | None = None
    clashing_set: tuple[str, ...] = ()

    @property
    def source_context(self) -> _assertions.ContextReference:
        return self.source_assertion.context

    @property
    def target_context(self) -> _assertions.ContextReference:
        return self.assertion.context

    @property
    def proposition_id(self) -> str:
        return self.assertion.proposition_id

    @property
    def provenance(self) -> dict[str, object]:
        payload = self.decision.provenance.to_payload()
        if self.decision.exception is not None:
            payload["defeated_use"] = self.decision.exception.defeated_use
        return payload


@dataclass(frozen=True)
class LiftingSystem:
    contexts: tuple[_assertions.ContextReference, ...] = ()
    lifting_rules: tuple[LiftingRule, ...] = ()
    lifting_exceptions: tuple[LiftingException, ...] = ()
    context_assumptions: Mapping[ContextId, tuple[CelExpr, ...]] = field(
        default_factory=dict
    )
    _context_ids: frozenset[ContextId] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        contexts = tuple(self.contexts)
        rules = tuple(self.lifting_rules)
        exceptions = tuple(self.lifting_exceptions)
        assumptions = {
            to_context_id(context_id): to_cel_exprs(values)
            for context_id, values in self.context_assumptions.items()
        }
        context_ids = frozenset(context.id for context in contexts)
        for rule in rules:
            if rule.source.id not in context_ids:
                raise ValueError(f"lifting rule '{rule.id}' has unknown source context")
            if rule.target.id not in context_ids:
                raise ValueError(f"lifting rule '{rule.id}' has unknown target context")
        rule_ids = frozenset(rule.id for rule in rules)
        for exception in exceptions:
            if exception.rule_id not in rule_ids:
                raise ValueError(
                    f"lifting exception '{exception.id}' references unknown rule"
                )
            if exception.target.id not in context_ids:
                raise ValueError(
                    f"lifting exception '{exception.id}' has unknown target context"
                )
        unknown_assumptions = set(assumptions).difference(context_ids)
        if unknown_assumptions:
            raise ValueError("context assumptions reference unknown context")
        object.__setattr__(self, "contexts", contexts)
        object.__setattr__(self, "lifting_rules", rules)
        object.__setattr__(self, "lifting_exceptions", exceptions)
        object.__setattr__(self, "context_assumptions", assumptions)
        object.__setattr__(self, "_context_ids", context_ids)

    def effective_assumptions(self, target: ContextId | str) -> tuple[CelExpr, ...]:
        target_id = to_context_id(target)
        return tuple(dict.fromkeys(self.context_assumptions.get(target_id, ())))

    def materialize_lifted_assertions(
        self,
        assertions: tuple[IstProposition, ...],
        *,
        solver: ExceptionPatternSolver | None = None,
        bindings: Mapping[str, CelScalar] | None = None,
    ) -> tuple[LiftedAssertion, ...]:
        materialized: list[LiftedAssertion] = []
        for assertion in assertions:
            for decision in self.lift_decisions_for(
                assertion,
                solver=solver,
                bindings=bindings,
            ):
                target_assertion = IstProposition(
                    context=decision.target_context,
                    proposition_id=assertion.proposition_id,
                )
                if decision.status is LiftingDecisionStatus.LIFTED:
                    materialized.append(
                        LiftedAssertion(
                            assertion=target_assertion,
                            source_assertion=assertion,
                            rule_id=decision.rule_id,
                            mode=decision.mode,
                            status=decision.status,
                            decision=decision,
                            justification=decision.provenance.justification,
                        )
                    )
                    continue
                exception_id = None
                clashing_set: tuple[str, ...] = ()
                if decision.exception is not None:
                    exception_id = decision.provenance.exception_id
                    clashing_set = decision.exception.exception.justification_claims
                materialized.append(
                    LiftedAssertion(
                        assertion=target_assertion,
                        source_assertion=assertion,
                        rule_id=decision.rule_id,
                        mode=decision.mode,
                        status=decision.status,
                        decision=decision,
                        exception_id=exception_id,
                        justification=decision.provenance.justification,
                        clashing_set=clashing_set,
                    )
                )
        return tuple(materialized)

    def lift_decisions_for(
        self,
        assertion: IstProposition,
        *,
        solver: ExceptionPatternSolver | None = None,
        bindings: Mapping[str, CelScalar] | None = None,
    ) -> tuple[LiftingDecision, ...]:
        decisions: list[LiftingDecision] = []
        for rule in self.lifting_rules:
            if rule.source.id != assertion.context.id:
                continue
            exception = self._exception_for(rule, assertion)
            decisions.append(
                self._decision_for(
                    rule,
                    assertion,
                    exception,
                    solver=solver,
                    bindings=bindings or {},
                )
            )
        return tuple(decisions)

    def lift_decisions_between(
        self,
        source: ContextId | str,
        target: ContextId | str,
        proposition_id: str,
        *,
        solver: ExceptionPatternSolver | None = None,
        bindings: Mapping[str, CelScalar] | None = None,
    ) -> tuple[LiftingDecision, ...]:
        target_id = to_context_id(target)
        assertion = IstProposition(
            context=_assertions.ContextReference(to_context_id(source)),
            proposition_id=proposition_id,
        )
        return tuple(
            decision
            for decision in self.lift_decisions_for(
                assertion,
                solver=solver,
                bindings=bindings,
            )
            if decision.target_context.id == target_id
        )

    def _decision_for(
        self,
        rule: LiftingRule,
        assertion: IstProposition,
        exception: LiftingException | None,
        *,
        solver: ExceptionPatternSolver | None,
        bindings: Mapping[str, CelScalar],
    ) -> LiftingDecision:
        support = _support_for_source("lifting_rule", rule.id)
        rule_status, diagnostic, witness = _evaluate_rule_conditions(
            rule,
            solver=solver,
            bindings=bindings,
        )
        provenance = LiftingDecisionProvenance(
            rule_id=rule.id,
            source_context_id=to_context_id(rule.source.id),
            target_context_id=to_context_id(rule.target.id),
            source_proposition_id=assertion.proposition_id,
            status=rule_status,
            justification=rule.justification,
            diagnostic=diagnostic,
        )
        if rule_status is not LiftingDecisionStatus.LIFTED:
            return LiftingDecision(
                source_context=rule.source,
                target_context=rule.target,
                proposition_id=assertion.proposition_id,
                status=rule_status,
                mode=rule.mode,
                rule_id=rule.id,
                rule_conditions=rule.conditions,
                support=support,
                provenance=provenance,
                solver_witness=witness,
            )
        if exception is None:
            return LiftingDecision(
                source_context=rule.source,
                target_context=rule.target,
                proposition_id=assertion.proposition_id,
                status=LiftingDecisionStatus.LIFTED,
                mode=rule.mode,
                rule_id=rule.id,
                rule_conditions=rule.conditions,
                support=support,
                provenance=provenance,
                solver_witness=witness,
            )

        defeat = _lifting_exception_defeat(rule, assertion, exception)
        blocked_provenance = LiftingDecisionProvenance(
            rule_id=rule.id,
            source_context_id=to_context_id(rule.source.id),
            target_context_id=to_context_id(rule.target.id),
            source_proposition_id=assertion.proposition_id,
            status=LiftingDecisionStatus.BLOCKED,
            justification=exception.justification,
            exception_id=exception.id,
            clashing_set=exception.clashing_set,
        )
        return LiftingDecision(
            source_context=rule.source,
            target_context=rule.target,
            proposition_id=assertion.proposition_id,
            status=LiftingDecisionStatus.BLOCKED,
            mode=rule.mode,
            rule_id=rule.id,
            rule_conditions=rule.conditions,
            support=defeat.support,
            provenance=blocked_provenance,
            exception=defeat,
            solver_witness=defeat.solver_witness,
        )

    def _exception_for(
        self,
        rule: LiftingRule,
        assertion: IstProposition,
    ) -> LiftingException | None:
        for exception in self.lifting_exceptions:
            if exception.rule_id != rule.id:
                continue
            if exception.target.id != rule.target.id:
                continue
            if exception.proposition_id != assertion.proposition_id:
                continue
            return exception
        return None


def _support_for_source(kind: str, source_id: str) -> SupportEvidence:
    return SupportEvidence(
        ProvenancePolynomial.variable(SourceVariableId(f"ps:source:{kind}:{source_id}")),
        SupportQuality.EXACT,
    )


def _lifting_exception_defeat(
    rule: LiftingRule,
    assertion: IstProposition,
    exception: LiftingException,
) -> ExceptionDefeat:
    justifiable = JustifiableException(
        target_claim=exception.proposition_id,
        exception_pattern="true",
        justification_claims=exception.clashing_set,
        context=str(exception.target.id),
        support=_support_for_source("lifting_exception", exception.id),
        decidability_status=DecidabilityStatus.DECIDABLE,
    )
    return build_exception_defeat(
        defeated_use=f"ist({rule.target.id}, {assertion.proposition_id})",
        exception=justifiable,
        solver_support=_support_for_source("lifting_rule", rule.id),
    )


def _evaluate_rule_conditions(
    rule: LiftingRule,
    *,
    solver: ExceptionPatternSolver | None,
    bindings: Mapping[str, CelScalar],
) -> tuple[LiftingDecisionStatus, str | None, NogoodWitness | None]:
    if not rule.conditions:
        return LiftingDecisionStatus.LIFTED, None, None
    if solver is None:
        return (
            LiftingDecisionStatus.UNKNOWN,
            "lifting rule conditions require a solver",
            NogoodWitness("lifting-rule-condition", "solver unavailable"),
        )

    for condition in rule.conditions:
        try:
            result = solver.is_condition_satisfied_result(condition, bindings)
        except Z3TranslationError as exc:
            return (
                LiftingDecisionStatus.UNKNOWN,
                f"lifting rule condition is not translatable: {exc}",
                NogoodWitness("lifting-rule-condition", str(exc)),
            )
        if isinstance(result, SolverSat):
            continue
        if isinstance(result, SolverUnsat):
            return (
                LiftingDecisionStatus.BLOCKED,
                f"lifting rule condition is unsatisfied: {condition}",
                NogoodWitness("lifting-rule-condition", str(condition)),
            )
        if isinstance(result, SolverUnknown):
            return (
                LiftingDecisionStatus.UNKNOWN,
                f"lifting rule condition is unknown: {result.hint}",
                NogoodWitness("lifting-rule-condition", result.hint),
            )
    return LiftingDecisionStatus.LIFTED, None, None
