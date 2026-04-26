"""First-class context references and explicit lifting rules.

This is the McCarthy/Guha Phase 4 context surface: contexts are logical
objects, and cross-context visibility exists only through authored lifting
rules. There is no ancestry-based default visibility.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.core import assertions as _assertions
from propstore.core.id_types import ContextId, to_context_id


@dataclass(frozen=True)
class IstProposition:
    context: _assertions.ContextReference
    proposition_id: str


class LiftingMode(StrEnum):
    BRIDGE = "bridge"
    SPECIALIZATION = "specialization"
    DECONTEXTUALIZATION = "decontextualization"


class LiftingMaterializationStatus(StrEnum):
    LIFTED = "lifted"
    BLOCKED = "blocked"


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
class LiftedAssertion:
    assertion: IstProposition
    source_assertion: IstProposition
    rule_id: str
    mode: LiftingMode
    status: LiftingMaterializationStatus
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
    def provenance(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "rule_id": self.rule_id,
            "source_context_id": str(self.source_context.id),
            "target_context_id": str(self.target_context.id),
            "source_proposition_id": self.source_assertion.proposition_id,
            "status": self.status.value,
        }
        if self.exception_id is not None:
            payload["exception_id"] = self.exception_id
        if self.justification is not None:
            payload["justification"] = self.justification
        if self.clashing_set:
            payload["clashing_set"] = list(self.clashing_set)
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

    def can_lift(self, source: ContextId | str, target: ContextId | str) -> bool:
        source_id = to_context_id(source)
        target_id = to_context_id(target)
        if source_id == target_id:
            return True
        return any(
            rule.source.id == source_id and rule.target.id == target_id
            for rule in self.lifting_rules
        )

    def effective_assumptions(self, target: ContextId | str) -> tuple[CelExpr, ...]:
        target_id = to_context_id(target)
        assumptions: list[CelExpr] = list(self.context_assumptions.get(target_id, ()))
        for rule in self.lifting_rules:
            if rule.target.id != target_id:
                continue
            assumptions.extend(rule.conditions)
        return tuple(dict.fromkeys(assumptions))

    def materialize_lifted_assertions(
        self,
        assertions: tuple[IstProposition, ...],
    ) -> tuple[LiftedAssertion, ...]:
        materialized: list[LiftedAssertion] = []
        for assertion in assertions:
            for rule in self.lifting_rules:
                if rule.source.id != assertion.context.id:
                    continue
                exception = self._exception_for(rule, assertion)
                target_assertion = IstProposition(
                    context=rule.target,
                    proposition_id=assertion.proposition_id,
                )
                if exception is None:
                    materialized.append(
                        LiftedAssertion(
                            assertion=target_assertion,
                            source_assertion=assertion,
                            rule_id=rule.id,
                            mode=rule.mode,
                            status=LiftingMaterializationStatus.LIFTED,
                            justification=rule.justification,
                        )
                    )
                    continue
                materialized.append(
                    LiftedAssertion(
                        assertion=target_assertion,
                        source_assertion=assertion,
                        rule_id=rule.id,
                        mode=rule.mode,
                        status=LiftingMaterializationStatus.BLOCKED,
                        exception_id=exception.id,
                        justification=exception.justification,
                        clashing_set=exception.clashing_set,
                    )
                )
        return tuple(materialized)

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
