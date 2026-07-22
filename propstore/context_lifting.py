"""The lifting algebra over first-class ``ist(c, p)`` contexts.

McCarthy/Guha lifting (Phase 4): contexts are flat logical objects and a
proposition crosses from one context to another ONLY through an authored
:class:`~propstore.families.contexts.LiftingRule`. There is no ancestry-based
default visibility. Each authored rule, evaluated for a proposition, yields a
:class:`LiftingDecision` with a ``LIFTED`` / ``EXCEPTED`` / ``BLOCKED`` /
``UNKNOWN`` status:

* ``LIFTED`` — the rule's CEL gate holds (or is empty) and no exception targets it.
* ``EXCEPTED`` — the gate holds but an authored :class:`LiftingException`
  targets the lift. Per Bozzato 2018 (Def 12) an exception overrides only when
  its clashing set is established, so the decision layer does not block: the
  lift's defeasible rule is still projected into ASPIC+ and the exception
  contributes defeats only from arguments concluding the clashing-set claims
  (:func:`propstore.aspic_bridge.build.apply_lifting_exception_defeats`).
* ``BLOCKED`` — the gate is unsatisfiable.
* ``UNKNOWN`` — the gate cannot be decided (no solver, a solver ``UNKNOWN``, or an
  untranslatable condition). Honest ignorance, kept distinct from blocked.

Substrate boundary (CLAUDE.md): the CEL gate is evaluated by condition-ir
(``check_condition_ir`` + the package ``ConditionSolver``) — never reimplemented.
Support/provenance is provenance-semiring's ``SupportEvidence`` /
``ProvenancePolynomial``, used directly. The single ``LiftingRule`` charter is
both the stored document and the algebra's input; its conditions are RAW CEL
source lowered here at evaluation time (one spelling).

Non-commitment: this module computes decisions; it never drops a non-lifted one.
The decisions flow into the ``lifting_materialization`` sidecar
(:meth:`~propstore.families.contexts.ContextRepository.build_sidecar`) and the
render layer decides which are visible.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from condition_ir import (
    SolverSat,
    SolverUnsat,
    Z3TranslationError,
    check_condition_ir,
)
from provenance_semiring import (
    NogoodWitness,
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
)

from propstore.defeasibility import (
    DecidabilityStatus,
    ExceptionDefeat,
    ExceptionPatternSolver,
    JustifiableException,
    build_exception_defeat,
)
from propstore.core.scalars import ScalarValue
from propstore.families.contexts import (
    Context,
    LiftingDecisionStatus,
    LiftingMode,
    LiftingRule,
)


@dataclass(frozen=True)
class IstProposition:
    """A proposition asserted in a context: ``ist(context, proposition_id)``."""

    context: str
    proposition_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "context", str(self.context))
        object.__setattr__(self, "proposition_id", str(self.proposition_id))


@dataclass(frozen=True)
class LiftingException:
    """An authored exception that blocks a specific lift of a proposition."""

    id: str
    rule_id: str
    target: str
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
        object.__setattr__(self, "target", str(self.target))
        object.__setattr__(
            self, "clashing_set", tuple(str(item) for item in self.clashing_set)
        )


@dataclass(frozen=True)
class LiftingDecision:
    """The outcome of evaluating one lifting rule for one proposition.

    The flat provenance fields (``rule_id`` … ``diagnostic``) are exactly the
    ``lifting_materialization`` sidecar columns — the projection falls out of
    this object, with no payload method. ``support`` / ``exception`` /
    ``solver_witness`` carry the richer compute-time evidence.
    """

    rule_id: str
    proposition_id: str
    source_context: str
    target_context: str
    status: LiftingDecisionStatus
    mode: LiftingMode
    support: SupportEvidence
    justification: str | None = None
    exception_id: str | None = None
    clashing_set: tuple[str, ...] = ()
    diagnostic: str | None = None
    exception: ExceptionDefeat | None = None
    solver_witness: NogoodWitness | None = None


@dataclass(frozen=True)
class LiftedAssertion:
    """A proposition successfully lifted into a target context."""

    assertion: IstProposition
    source_assertion: IstProposition
    rule_id: str
    mode: LiftingMode
    status: LiftingDecisionStatus
    decision: LiftingDecision
    justification: str | None = None

    @property
    def source_context(self) -> str:
        return self.source_assertion.context

    @property
    def target_context(self) -> str:
        return self.assertion.context

    @property
    def proposition_id(self) -> str:
        return self.assertion.proposition_id


@dataclass(frozen=True)
class LiftingSystem:
    """An authored set of contexts, lifting rules, and exceptions.

    Cross-context visibility exists only through ``lifting_rules``; there is no
    ancestry. ``effective_assumptions`` returns a context's OWN assumptions only —
    assumptions never leak from a source context into a target.
    """

    contexts: tuple[Context, ...] = ()
    lifting_rules: tuple[LiftingRule, ...] = ()
    lifting_exceptions: tuple[LiftingException, ...] = ()
    _context_ids: frozenset[str] = field(init=False, repr=False)
    _assumptions: Mapping[str, tuple[str, ...]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        contexts = tuple(self.contexts)
        rules = tuple(self.lifting_rules)
        exceptions = tuple(self.lifting_exceptions)
        context_ids = frozenset(context.context_id for context in contexts)
        for rule in rules:
            if rule.source_context not in context_ids:
                raise ValueError(
                    f"lifting rule '{rule.rule_id}' has unknown source context"
                )
            if rule.target_context not in context_ids:
                raise ValueError(
                    f"lifting rule '{rule.rule_id}' has unknown target context"
                )
        rule_ids = frozenset(rule.rule_id for rule in rules)
        for exception in exceptions:
            if exception.rule_id not in rule_ids:
                raise ValueError(
                    f"lifting exception '{exception.id}' references unknown rule"
                )
            if exception.target not in context_ids:
                raise ValueError(
                    f"lifting exception '{exception.id}' has unknown target context"
                )
        object.__setattr__(self, "contexts", contexts)
        object.__setattr__(self, "lifting_rules", rules)
        object.__setattr__(self, "lifting_exceptions", exceptions)
        object.__setattr__(self, "_context_ids", context_ids)
        object.__setattr__(
            self,
            "_assumptions",
            {context.context_id: tuple(context.assumptions) for context in contexts},
        )

    def effective_assumptions(self, target: str) -> tuple[str, ...]:
        """The target context's OWN assumptions (no inheritance, no ancestry)."""

        return tuple(dict.fromkeys(self._assumptions.get(str(target), ())))

    def materialize_lifted_assertions(
        self,
        assertions: tuple[IstProposition, ...],
        *,
        solver: ExceptionPatternSolver | None = None,
        bindings: Mapping[str, ScalarValue] | None = None,
    ) -> tuple[LiftedAssertion, ...]:
        """Lift each assertion through every applicable rule (LIFTED only)."""

        materialized: list[LiftedAssertion] = []
        for assertion in assertions:
            for decision in self.lift_decisions_for(
                assertion, solver=solver, bindings=bindings
            ):
                if decision.status is not LiftingDecisionStatus.LIFTED:
                    continue
                materialized.append(
                    LiftedAssertion(
                        assertion=IstProposition(
                            context=decision.target_context,
                            proposition_id=assertion.proposition_id,
                        ),
                        source_assertion=assertion,
                        rule_id=decision.rule_id,
                        mode=decision.mode,
                        status=decision.status,
                        decision=decision,
                        justification=decision.justification,
                    )
                )
        return tuple(materialized)

    def lift_decisions_for(
        self,
        assertion: IstProposition,
        *,
        solver: ExceptionPatternSolver | None = None,
        bindings: Mapping[str, ScalarValue] | None = None,
    ) -> tuple[LiftingDecision, ...]:
        """Every lifting decision for an assertion (one per applicable rule)."""

        decisions: list[LiftingDecision] = []
        for rule in self.lifting_rules:
            if rule.source_context != assertion.context:
                continue
            exception = self._exception_for(rule, assertion)
            decisions.append(
                self._decision_for(
                    rule, assertion, exception, solver=solver, bindings=bindings or {}
                )
            )
        return tuple(decisions)

    def lift_decisions_between(
        self,
        source: str,
        target: str,
        proposition_id: str,
        *,
        solver: ExceptionPatternSolver | None = None,
        bindings: Mapping[str, ScalarValue] | None = None,
    ) -> tuple[LiftingDecision, ...]:
        """Lifting decisions from ``source`` to ``target`` for a proposition."""

        assertion = IstProposition(context=source, proposition_id=proposition_id)
        return tuple(
            decision
            for decision in self.lift_decisions_for(
                assertion, solver=solver, bindings=bindings
            )
            if decision.target_context == str(target)
        )

    def _decision_for(
        self,
        rule: LiftingRule,
        assertion: IstProposition,
        exception: LiftingException | None,
        *,
        solver: ExceptionPatternSolver | None,
        bindings: Mapping[str, ScalarValue],
    ) -> LiftingDecision:
        support = _support_for_source("lifting_rule", rule.rule_id)
        rule_status, diagnostic, witness = _evaluate_rule_conditions(
            rule, solver=solver, bindings=bindings
        )
        if rule_status is not LiftingDecisionStatus.LIFTED:
            return LiftingDecision(
                rule_id=rule.rule_id,
                proposition_id=assertion.proposition_id,
                source_context=rule.source_context,
                target_context=rule.target_context,
                status=rule_status,
                mode=rule.mode,
                support=support,
                justification=rule.justification,
                diagnostic=diagnostic,
                solver_witness=witness,
            )
        if exception is None:
            return LiftingDecision(
                rule_id=rule.rule_id,
                proposition_id=assertion.proposition_id,
                source_context=rule.source_context,
                target_context=rule.target_context,
                status=LiftingDecisionStatus.LIFTED,
                mode=rule.mode,
                support=support,
                justification=rule.justification,
                solver_witness=witness,
            )

        defeat = _lifting_exception_defeat(rule, assertion, exception)
        return LiftingDecision(
            rule_id=rule.rule_id,
            proposition_id=assertion.proposition_id,
            source_context=rule.source_context,
            target_context=rule.target_context,
            status=LiftingDecisionStatus.EXCEPTED,
            mode=rule.mode,
            support=defeat.support,
            justification=exception.justification,
            exception_id=exception.id,
            clashing_set=exception.clashing_set,
            exception=defeat,
            solver_witness=defeat.solver_witness,
        )

    def _exception_for(
        self, rule: LiftingRule, assertion: IstProposition
    ) -> LiftingException | None:
        for exception in self.lifting_exceptions:
            if exception.rule_id != rule.rule_id:
                continue
            if exception.target != rule.target_context:
                continue
            if exception.proposition_id != assertion.proposition_id:
                continue
            return exception
        return None


def _support_for_source(kind: str, source_id: str) -> SupportEvidence:
    return SupportEvidence(
        ProvenancePolynomial.variable(
            SourceVariableId(f"ps:source:{kind}:{source_id}")
        ),
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
        context=exception.target,
        support=_support_for_source("lifting_exception", exception.id),
        decidability_status=DecidabilityStatus.DECIDABLE,
    )
    return build_exception_defeat(
        defeated_use=f"ist({rule.target_context}, {assertion.proposition_id})",
        exception=justifiable,
        solver_support=_support_for_source("lifting_rule", rule.rule_id),
    )


def _evaluate_rule_conditions(
    rule: LiftingRule,
    *,
    solver: ExceptionPatternSolver | None,
    bindings: Mapping[str, ScalarValue],
) -> tuple[LiftingDecisionStatus, str | None, NogoodWitness | None]:
    if not rule.conditions:
        return LiftingDecisionStatus.LIFTED, None, None
    if solver is None:
        return (
            LiftingDecisionStatus.UNKNOWN,
            "lifting rule conditions require a solver",
            NogoodWitness("lifting-rule-condition", "solver unavailable"),
        )
    registry = solver.registry

    for condition in rule.conditions:
        try:
            result = solver.is_condition_satisfied_result(
                check_condition_ir(str(condition), registry), bindings
            )
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
        # SolverUnknown — honest ignorance; the lift cannot be decided.
        return (
            LiftingDecisionStatus.UNKNOWN,
            f"lifting rule condition is unknown: {result.hint}",
            NogoodWitness("lifting-rule-condition", result.hint),
        )
    return LiftingDecisionStatus.LIFTED, None, None


__all__ = [
    "IstProposition",
    "LiftedAssertion",
    "LiftingDecision",
    "LiftingException",
    "LiftingSystem",
]
