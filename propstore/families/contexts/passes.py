"""Semantic passes for context artifacts."""

from __future__ import annotations

from propstore.cel_types import to_cel_exprs
from propstore.families.contexts.lifting import LiftingMode, LiftingRule, LiftingSystem
from propstore.core.assertions.refs import ContextReference
from propstore.core.id_types import ContextId
from propstore.families.contexts.declaration import ContextDocument
from propstore.families.contexts.stages import (
    ContextAuthoredSet,
    ContextBoundGraph,
    ContextCheckedGraph,
    ContextNormalizedSet,
    ContextStage,
)
from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import PassDiagnostic, PassResult, PipelineResult
from quire.documents import LoadedDocument


class ContextNormalizePass:
    family = PropstoreFamily.CONTEXTS
    name = "context.normalize"
    version = "1"
    input_stage = ContextStage.AUTHORED
    output_stage = ContextStage.NORMALIZED

    def run(
        self,
        value: ContextAuthoredSet,
        context: object,
    ) -> PassResult[ContextNormalizedSet]:
        return PassResult.ok(ContextNormalizedSet(contexts=tuple(value.contexts)))


class ContextIdentityPass:
    family = PropstoreFamily.CONTEXTS
    name = "context.identity"
    version = "1"
    input_stage = ContextStage.NORMALIZED
    output_stage = ContextStage.NORMALIZED

    def run(
        self,
        value: ContextNormalizedSet,
        context: object,
    ) -> PassResult[ContextNormalizedSet]:
        diagnostics: list[PassDiagnostic] = []
        seen_ids: dict[str, str] = {}

        for loaded_context in value.contexts:
            document = loaded_context.document
            context_id = str(document.id)

            if not document.name:
                diagnostics.append(
                    _error(
                        "context.name.missing",
                        f"context '{context_id}' missing 'name'",
                        loaded_context,
                        self.name,
                        artifact_id=context_id,
                    )
                )

            duplicate_filename = seen_ids.get(context_id)
            if duplicate_filename is not None:
                diagnostics.append(
                    _error(
                        "context.id.duplicate",
                        (
                            f"duplicate context ID '{context_id}' "
                            f"(also in {duplicate_filename})"
                        ),
                        loaded_context,
                        self.name,
                        artifact_id=context_id,
                    )
                )
            else:
                seen_ids[context_id] = loaded_context.filename

        return PassResult(output=value, diagnostics=tuple(diagnostics))


class ContextLiftingBindingPass:
    family = PropstoreFamily.CONTEXTS
    name = "context.lifting.binding"
    version = "1"
    input_stage = ContextStage.NORMALIZED
    output_stage = ContextStage.BOUND

    def run(
        self,
        value: ContextNormalizedSet,
        context: object,
    ) -> PassResult[ContextBoundGraph]:
        all_ids = {
            str(loaded_context.document.id) for loaded_context in value.contexts
        }
        diagnostics: list[PassDiagnostic] = []
        bound_rules = []

        for loaded_context in value.contexts:
            for rule in loaded_context.document.lifting_rules or ():
                source_id = rule.source
                target_id = rule.target
                valid_rule = True
                if source_id not in all_ids:
                    valid_rule = False
                    diagnostics.append(
                        _error(
                            "context.lifting.source_missing",
                            (
                                f"lifting rule '{rule.id}' references "
                                f"nonexistent source context '{rule.source}'"
                            ),
                            loaded_context,
                            self.name,
                        )
                    )
                if target_id not in all_ids:
                    valid_rule = False
                    diagnostics.append(
                        _error(
                            "context.lifting.target_missing",
                            (
                                f"lifting rule '{rule.id}' references "
                                f"nonexistent target context '{rule.target}'"
                            ),
                            loaded_context,
                            self.name,
                        )
                    )
                if valid_rule:
                    bound_rules.append(rule)

        lifting_system = LiftingSystem(
            contexts=tuple(
                ContextReference(id=ContextId(loaded_context.document.id))
                for loaded_context in value.contexts
            ),
            lifting_rules=tuple(
                LiftingRule(
                    id=rule.id,
                    source=ContextReference(id=ContextId(rule.source)),
                    target=ContextReference(id=ContextId(rule.target)),
                    conditions=rule.conditions or (),
                    mode=LiftingMode(rule.mode),
                    justification=rule.justification,
                )
                for rule in bound_rules
            ),
            context_assumptions={
                ContextId(loaded_context.document.id): to_cel_exprs(
                    loaded_context.document.assumptions or ()
                )
                for loaded_context in value.contexts
            },
        )
        return PassResult(
            output=ContextBoundGraph(
                contexts=value.contexts,
                lifting_system=lifting_system,
            ),
            diagnostics=tuple(diagnostics),
        )


class ContextLiftingGraphPass:
    family = PropstoreFamily.CONTEXTS
    name = "context.lifting.graph"
    version = "1"
    input_stage = ContextStage.BOUND
    output_stage = ContextStage.CHECKED

    def run(
        self,
        value: ContextBoundGraph,
        context: object,
    ) -> PassResult[ContextCheckedGraph]:
        return PassResult.ok(
            ContextCheckedGraph(
                contexts=value.contexts,
                lifting_system=value.lifting_system,
            )
        )


def register_context_pipeline(registry: PipelineRegistry) -> None:
    registry.register(ContextNormalizePass, family=PropstoreFamily.CONTEXTS)
    registry.register(ContextIdentityPass, family=PropstoreFamily.CONTEXTS)
    registry.register(ContextLiftingBindingPass, family=PropstoreFamily.CONTEXTS)
    registry.register(ContextLiftingGraphPass, family=PropstoreFamily.CONTEXTS)


def run_context_pipeline(
    contexts: tuple[LoadedDocument[ContextDocument], ...]
    | list[LoadedDocument[ContextDocument]],
    *,
    target_stage: ContextStage = ContextStage.CHECKED,
    context: object | None = None,
) -> PipelineResult[object]:
    registry = PipelineRegistry()
    register_context_pipeline(registry)
    return run_pipeline(
        ContextAuthoredSet(contexts=tuple(contexts)),
        family=PropstoreFamily.CONTEXTS,
        start_stage=ContextStage.AUTHORED,
        target_stage=target_stage,
        registry=registry,
        context=context,
    )


def _error(
    code: str,
    message: str,
    context: LoadedDocument[ContextDocument],
    pass_name: str,
    *,
    artifact_id: str | None = None,
) -> PassDiagnostic:
    return PassDiagnostic(
        level="error",
        code=code,
        message=message,
        family=PropstoreFamily.CONTEXTS,
        stage=ContextStage.CHECKED,
        filename=context.filename,
        artifact_id=artifact_id,
        pass_name=pass_name,
    )
