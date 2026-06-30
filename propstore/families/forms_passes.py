"""Semantic passes and stages for the ``form`` family (flat charter).

A form's AUTHORED -> CHECKED pipeline normalises the authored
:class:`~propstore.families.forms.FormDefinition` charters into an id-keyed
registry and validates each form's dimensional consistency (via
:func:`~propstore.families.forms.validate_form_definition`, which composes
bridgman). A duplicate form name or an inconsistent form is a form *validation
failure*: the pass returns no checked output, so the runner short-circuits and
:func:`propstore.compiler.workflows.build_repository` aborts (the Z1 abort class
— forms are infrastructure that concepts depend on). ``validate_repository``
runs the same passes but only reports the diagnostics.

The stage types are designed for the flat tree: :class:`LoadedForm` wraps the one
``FormDefinition`` charter directly (the charter is the document) — there is no
``FormDocument`` / ``FormRow`` second spelling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from propstore.families.forms import FormDefinition, validate_form_definition
from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import (
    PassDiagnostic,
    PassResult,
    PipelineResult,
)

_FAMILY = PropstoreFamily.FORM


class FormStage(StrEnum):
    AUTHORED = "form.authored"
    NORMALIZED = "form.normalized"
    CHECKED = "form.checked"


@dataclass(frozen=True)
class LoadedForm:
    """One authored form charter, with the filename it was loaded from."""

    form: FormDefinition
    filename: str | None = None

    @property
    def name(self) -> str:
        return self.form.name


@dataclass(frozen=True)
class FormAuthoredSet:
    forms: tuple[LoadedForm, ...]


@dataclass(frozen=True)
class FormNormalizedRegistry:
    forms: tuple[LoadedForm, ...]
    registry: dict[str, FormDefinition]


@dataclass(frozen=True)
class FormCheckedRegistry:
    forms: tuple[LoadedForm, ...]
    registry: dict[str, FormDefinition]


def _error(
    code: str,
    message: str,
    loaded: LoadedForm,
    pass_name: str,
    stage: FormStage,
) -> PassDiagnostic:
    return PassDiagnostic(
        level="error",
        code=code,
        message=message,
        family=_FAMILY,
        stage=stage,
        filename=loaded.filename,
        artifact_id=loaded.name,
        pass_name=pass_name,
    )


class FormNormalizePass:
    family = _FAMILY
    name = "form.normalize"
    version = "1"
    input_stage = FormStage.AUTHORED
    output_stage = FormStage.NORMALIZED

    def run(
        self, value: FormAuthoredSet, context: object
    ) -> PassResult[FormNormalizedRegistry]:
        registry: dict[str, FormDefinition] = {}
        diagnostics: list[PassDiagnostic] = []
        for loaded in value.forms:
            if loaded.name in registry:
                diagnostics.append(
                    _error(
                        "form.id.duplicate",
                        f"duplicate form name '{loaded.name}'",
                        loaded,
                        self.name,
                        FormStage.NORMALIZED,
                    )
                )
                continue
            registry[loaded.name] = loaded.form
        if diagnostics:
            return PassResult(output=None, diagnostics=tuple(diagnostics))
        return PassResult(
            output=FormNormalizedRegistry(forms=value.forms, registry=registry)
        )


class FormDimensionPass:
    family = _FAMILY
    name = "form.dimension"
    version = "1"
    input_stage = FormStage.NORMALIZED
    output_stage = FormStage.CHECKED

    def run(
        self, value: FormNormalizedRegistry, context: object
    ) -> PassResult[FormCheckedRegistry]:
        diagnostics: list[PassDiagnostic] = []
        for loaded in value.forms:
            for problem in validate_form_definition(loaded.form):
                diagnostics.append(
                    _error(
                        "form.dimension.invalid",
                        problem,
                        loaded,
                        self.name,
                        FormStage.CHECKED,
                    )
                )
        if diagnostics:
            return PassResult(output=None, diagnostics=tuple(diagnostics))
        return PassResult(
            output=FormCheckedRegistry(forms=value.forms, registry=value.registry)
        )


def register_form_pipeline(registry: PipelineRegistry) -> None:
    registry.register(FormNormalizePass, family=_FAMILY)
    registry.register(FormDimensionPass, family=_FAMILY)


def run_form_pipeline(
    forms: tuple[LoadedForm, ...] | list[LoadedForm],
    *,
    target_stage: FormStage = FormStage.CHECKED,
    context: object | None = None,
) -> PipelineResult[object]:
    registry = PipelineRegistry()
    register_form_pipeline(registry)
    return run_pipeline(
        FormAuthoredSet(forms=tuple(forms)),
        family=_FAMILY,
        start_stage=FormStage.AUTHORED,
        target_stage=target_stage,
        registry=registry,
        context=context,
    )
