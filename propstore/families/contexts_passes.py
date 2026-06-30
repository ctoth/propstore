"""Semantic passes and stages for the ``context`` family (flat charter).

The context AUTHORED -> CHECKED pipeline checks context identity and binds the
authored lifting rules into a :class:`~propstore.context_lifting.LiftingSystem`.
A duplicate ``context_id``, or a lifting rule naming a source/target context that
does not exist, is a context *validation failure* (the Z1 abort class): the pass
returns no checked output and ``build_repository`` aborts. CEL assumption
validity is enforced separately and uniformly by the compiler's structural
invariant pre-pass (:mod:`propstore.cel_validation`), shared by build and
validate.

``LoadedContext`` / ``LoadedLiftingRule`` wrap the one ``Context`` /
``LiftingRule`` charters directly — no record/row second spelling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from propstore.context_lifting import LiftingSystem
from propstore.families.contexts import Context, LiftingRule
from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import (
    PassDiagnostic,
    PassResult,
    PipelineResult,
)

_FAMILY = PropstoreFamily.CONTEXT


class ContextStage(StrEnum):
    AUTHORED = "context.authored"
    NORMALIZED = "context.normalized"
    CHECKED = "context.checked"


@dataclass(frozen=True)
class LoadedContext:
    context: Context
    filename: str | None = None

    @property
    def context_id(self) -> str:
        return self.context.context_id


@dataclass(frozen=True)
class LoadedLiftingRule:
    rule: LiftingRule
    filename: str | None = None

    @property
    def rule_id(self) -> str:
        return self.rule.rule_id


@dataclass(frozen=True)
class ContextAuthoredSet:
    contexts: tuple[LoadedContext, ...]
    lifting_rules: tuple[LoadedLiftingRule, ...] = ()


@dataclass(frozen=True)
class ContextNormalizedSet:
    contexts: tuple[LoadedContext, ...]
    lifting_rules: tuple[LoadedLiftingRule, ...]


@dataclass(frozen=True)
class ContextCheckedGraph:
    contexts: tuple[LoadedContext, ...]
    lifting_rules: tuple[LoadedLiftingRule, ...]
    lifting_system: LiftingSystem
    context_ids: frozenset[str]


def _error(
    code: str,
    message: str,
    filename: str | None,
    artifact_id: str | None,
    pass_name: str,
    stage: ContextStage,
) -> PassDiagnostic:
    return PassDiagnostic(
        level="error",
        code=code,
        message=message,
        family=_FAMILY,
        stage=stage,
        filename=filename,
        artifact_id=artifact_id,
        pass_name=pass_name,
    )


class ContextIdentityPass:
    family = _FAMILY
    name = "context.identity"
    version = "1"
    input_stage = ContextStage.AUTHORED
    output_stage = ContextStage.NORMALIZED

    def run(
        self, value: ContextAuthoredSet, context: object
    ) -> PassResult[ContextNormalizedSet]:
        diagnostics: list[PassDiagnostic] = []
        seen: set[str] = set()
        for loaded in value.contexts:
            context_id = loaded.context_id
            if not context_id:
                diagnostics.append(
                    _error(
                        "context.id.missing",
                        "context missing 'context_id'",
                        loaded.filename,
                        None,
                        self.name,
                        ContextStage.NORMALIZED,
                    )
                )
                continue
            if context_id in seen:
                diagnostics.append(
                    _error(
                        "context.id.duplicate",
                        f"duplicate context id '{context_id}'",
                        loaded.filename,
                        context_id,
                        self.name,
                        ContextStage.NORMALIZED,
                    )
                )
                continue
            seen.add(context_id)
        if diagnostics:
            return PassResult(output=None, diagnostics=tuple(diagnostics))
        return PassResult(
            output=ContextNormalizedSet(
                contexts=value.contexts, lifting_rules=value.lifting_rules
            )
        )


class ContextLiftingPass:
    family = _FAMILY
    name = "context.lifting"
    version = "1"
    input_stage = ContextStage.NORMALIZED
    output_stage = ContextStage.CHECKED

    def run(
        self, value: ContextNormalizedSet, context: object
    ) -> PassResult[ContextCheckedGraph]:
        context_ids = frozenset(loaded.context_id for loaded in value.contexts)
        diagnostics: list[PassDiagnostic] = []
        bound_rules: list[LiftingRule] = []
        for loaded in value.lifting_rules:
            rule = loaded.rule
            valid = True
            if rule.source_context not in context_ids:
                valid = False
                diagnostics.append(
                    _error(
                        "context.lifting.source_missing",
                        (
                            f"lifting rule '{rule.rule_id}' references nonexistent "
                            f"source context '{rule.source_context}'"
                        ),
                        loaded.filename,
                        rule.rule_id,
                        self.name,
                        ContextStage.CHECKED,
                    )
                )
            if rule.target_context not in context_ids:
                valid = False
                diagnostics.append(
                    _error(
                        "context.lifting.target_missing",
                        (
                            f"lifting rule '{rule.rule_id}' references nonexistent "
                            f"target context '{rule.target_context}'"
                        ),
                        loaded.filename,
                        rule.rule_id,
                        self.name,
                        ContextStage.CHECKED,
                    )
                )
            if valid:
                bound_rules.append(rule)
        if diagnostics:
            return PassResult(output=None, diagnostics=tuple(diagnostics))
        lifting_system = LiftingSystem(
            contexts=tuple(loaded.context for loaded in value.contexts),
            lifting_rules=tuple(bound_rules),
        )
        return PassResult(
            output=ContextCheckedGraph(
                contexts=value.contexts,
                lifting_rules=value.lifting_rules,
                lifting_system=lifting_system,
                context_ids=context_ids,
            )
        )


def register_context_pipeline(registry: PipelineRegistry) -> None:
    registry.register(ContextIdentityPass, family=_FAMILY)
    registry.register(ContextLiftingPass, family=_FAMILY)


def run_context_pipeline(
    contexts: tuple[LoadedContext, ...] | list[LoadedContext],
    *,
    lifting_rules: tuple[LoadedLiftingRule, ...] | list[LoadedLiftingRule] = (),
    target_stage: ContextStage = ContextStage.CHECKED,
    context: object | None = None,
) -> PipelineResult[object]:
    registry = PipelineRegistry()
    register_context_pipeline(registry)
    return run_pipeline(
        ContextAuthoredSet(
            contexts=tuple(contexts), lifting_rules=tuple(lifting_rules)
        ),
        family=_FAMILY,
        start_stage=ContextStage.AUTHORED,
        target_stage=target_stage,
        registry=registry,
        context=context,
    )
