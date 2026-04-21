"""Semantic passes for form artifacts."""

from __future__ import annotations

from propstore.families.forms.stages import (
    FormAuthoredSet,
    FormCheckedRegistry,
    FormNormalizedRegistry,
    FormStage,
    LoadedForm,
    parse_form,
)
from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import PassDiagnostic, PassResult, PipelineResult


class FormNormalizePass:
    family = PropstoreFamily.FORMS
    name = "form.normalize"
    input_stage = FormStage.AUTHORED
    output_stage = FormStage.NORMALIZED

    def run(
        self,
        value: FormAuthoredSet,
        context: object,
    ) -> PassResult[FormNormalizedRegistry]:
        registry = {
            form.document.name: parse_form(form.document.name, form.document)
            for form in value.forms
        }
        return PassResult.ok(
            FormNormalizedRegistry(forms=value.forms, registry=registry)
        )


class FormDimensionPolicyPass:
    family = PropstoreFamily.FORMS
    name = "form.dimension.policy"
    input_stage = FormStage.NORMALIZED
    output_stage = FormStage.NORMALIZED

    def run(
        self,
        value: FormNormalizedRegistry,
        context: object,
    ) -> PassResult[FormNormalizedRegistry]:
        diagnostics: list[PassDiagnostic] = []
        for form in value.forms:
            document = form.document
            dims = document.dimensions
            is_dimless = document.dimensionless
            has_unit = document.unit_symbol is not None
            if dims is not None:
                for dimension_key in dims:
                    if (
                        not dimension_key
                        or not dimension_key[0].isascii()
                        or not dimension_key[0].isalpha()
                        or not all(
                            character.isascii()
                            and (character.isalnum() or character == "_")
                            for character in dimension_key
                        )
                    ):
                        diagnostics.append(
                            _error(
                                "form.dimension_key.invalid",
                                (
                                    f"dimension key '{dimension_key}' "
                                    "must be an identifier"
                                ),
                                form,
                                self.name,
                            )
                        )
            if (
                dims is not None
                and any(exponent != 0 for exponent in dims.values())
                and is_dimless
            ):
                diagnostics.append(
                    _error(
                        "form.dimensionless.non_empty_dimensions",
                        "non-empty dimensions conflicts with dimensionless=true",
                        form,
                        self.name,
                    )
                )
            if dims is not None and len(dims) == 0 and not is_dimless and has_unit:
                diagnostics.append(
                    _error(
                        "form.dimensionless.empty_dimensions_with_unit",
                        (
                            "empty dimensions conflicts with "
                            "dimensionless=false for a quantity with unit_symbol"
                        ),
                        form,
                        self.name,
                    )
                )
            if document.name != form.filename:
                diagnostics.append(
                    _error(
                        "form.name.filename_mismatch",
                        (
                            f"'name' field ('{document.name}') does not match "
                            f"filename '{form.filename}'"
                        ),
                        form,
                        self.name,
                        artifact_id=document.name,
                    )
                )
        return PassResult(output=value, diagnostics=tuple(diagnostics))


class FormRegistryPass:
    family = PropstoreFamily.FORMS
    name = "form.registry"
    input_stage = FormStage.NORMALIZED
    output_stage = FormStage.CHECKED

    def run(
        self,
        value: FormNormalizedRegistry,
        context: object,
    ) -> PassResult[FormCheckedRegistry]:
        return PassResult.ok(
            FormCheckedRegistry(
                forms=value.forms,
                registry=value.registry,
            )
        )


def register_form_pipeline(registry: PipelineRegistry) -> None:
    registry.register(FormNormalizePass, family=PropstoreFamily.FORMS)
    registry.register(FormDimensionPolicyPass, family=PropstoreFamily.FORMS)
    registry.register(FormRegistryPass, family=PropstoreFamily.FORMS)


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
        family=PropstoreFamily.FORMS,
        start_stage=FormStage.AUTHORED,
        target_stage=target_stage,
        registry=registry,
        context=context,
    )


def _error(
    code: str,
    message: str,
    form: LoadedForm,
    pass_name: str,
    *,
    artifact_id: str | None = None,
) -> PassDiagnostic:
    return PassDiagnostic(
        level="error",
        code=code,
        message=message,
        family=PropstoreFamily.FORMS,
        stage=FormStage.CHECKED,
        filename=form.filename,
        artifact_id=artifact_id,
        pass_name=pass_name,
    )
