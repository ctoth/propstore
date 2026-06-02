"""Context semantic stage objects."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.cel_types import to_cel_exprs
from propstore.core.assertions.refs import ContextReference
from propstore.families.contexts.lifting import (
    LiftingSystem,
    LiftingMode,
    LiftingRule,
)
from propstore.core.id_types import ContextId
from quire.documents import LoadedDocument
from enum import StrEnum

if TYPE_CHECKING:
    from propstore.families.contexts.declaration import ContextDocument


class ContextStage(StrEnum):
    AUTHORED = "context.authored"
    NORMALIZED = "context.normalized"
    BOUND = "context.bound"
    CHECKED = "context.checked"


@dataclass(frozen=True)
class ContextAuthoredSet:
    contexts: tuple[LoadedDocument[ContextDocument], ...]


@dataclass(frozen=True)
class ContextNormalizedSet:
    contexts: tuple[LoadedDocument[ContextDocument], ...]


@dataclass(frozen=True)
class ContextBoundGraph:
    contexts: tuple[LoadedDocument[ContextDocument], ...]
    lifting_system: LiftingSystem


@dataclass(frozen=True)
class ContextCheckedGraph:
    contexts: tuple[LoadedDocument[ContextDocument], ...]
    lifting_system: LiftingSystem

def loaded_contexts_to_lifting_system(
    contexts: Sequence[LoadedDocument[ContextDocument]],
) -> LiftingSystem:
    return LiftingSystem(
        contexts=tuple(
            ContextReference(id=ContextId(context.document.id))
            for context in contexts
        ),
        lifting_rules=tuple(
            rule
            for context in contexts
            for rule in _lifting_rules(context.document)
        ),
        context_assumptions={
            ContextId(context.document.id): to_cel_exprs(
                context.document.assumptions or ()
            )
            for context in contexts
        },
    )


def _lifting_rules(document: ContextDocument) -> tuple[LiftingRule, ...]:
    return tuple(
        LiftingRule(
            id=rule.id,
            source=ContextReference(id=ContextId(rule.source)),
            target=ContextReference(id=ContextId(rule.target)),
            conditions=rule.conditions or (),
            mode=LiftingMode(rule.mode),
            justification=rule.justification,
        )
        for rule in (document.lifting_rules or ())
    )
