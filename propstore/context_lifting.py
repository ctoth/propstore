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
from propstore.core.id_types import ContextId, to_context_id


@dataclass(frozen=True, order=True)
class ContextReference:
    id: ContextId | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", to_context_id(self.id))


@dataclass(frozen=True)
class IstProposition:
    context: ContextReference
    proposition_id: str


class LiftingMode(StrEnum):
    BRIDGE = "bridge"
    SPECIALIZATION = "specialization"
    DECONTEXTUALIZATION = "decontextualization"


@dataclass(frozen=True)
class LiftingRule:
    id: str
    source: ContextReference
    target: ContextReference
    conditions: tuple[CelExpr, ...] = ()
    mode: LiftingMode = LiftingMode.BRIDGE
    justification: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "conditions", to_cel_exprs(self.conditions))


@dataclass(frozen=True)
class LiftingSystem:
    contexts: tuple[ContextReference, ...] = ()
    lifting_rules: tuple[LiftingRule, ...] = ()
    context_assumptions: Mapping[ContextId, tuple[CelExpr, ...]] = field(
        default_factory=dict
    )
    _context_ids: frozenset[ContextId] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        contexts = tuple(self.contexts)
        rules = tuple(self.lifting_rules)
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
        unknown_assumptions = set(assumptions).difference(context_ids)
        if unknown_assumptions:
            raise ValueError("context assumptions reference unknown context")
        object.__setattr__(self, "contexts", contexts)
        object.__setattr__(self, "lifting_rules", rules)
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

    def contexts_visible_from(self, target: ContextId | str) -> frozenset[ContextId]:
        target_id = to_context_id(target)
        visible: set[ContextId] = {target_id}
        visible.update(
            to_context_id(rule.source.id)
            for rule in self.lifting_rules
            if rule.target.id == target_id
        )
        return frozenset(visible)
