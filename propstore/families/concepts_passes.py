"""Semantic passes and stages for the ``concept`` family (flat charter).

The concept AUTHORED -> CHECKED pipeline builds the id-keyed concept registry and
checks concept identity and form references. A duplicate ``concept_id`` or an
empty ``canonical_name`` is a concept *validation failure* (the Z1 abort class —
identity is structural): the pass returns no checked output, the runner
short-circuits, and ``build_repository`` aborts. A *dangling* form reference (a
``lexical_entry.physical_dimension_form`` naming a form not in the registry) is
reported as a warning and the concept is kept — a referential gap quarantines at
materialize time, it does not abort the build.

``LoadedConcept`` wraps the one :class:`~propstore.families.concepts.Concept`
charter directly; there is no ``ConceptRecord`` / ``ConceptRow`` second spelling.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from cel_parser import Ident, ParseError, parse
from condition_ir import ConceptInfo, KindType

from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition
from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import (
    PassDiagnostic,
    PassResult,
    PipelineResult,
)

_FAMILY = PropstoreFamily.CONCEPT


class ConceptStage(StrEnum):
    AUTHORED = "concept.authored"
    CHECKED = "concept.checked"


@dataclass(frozen=True)
class LoadedConcept:
    """One authored concept charter, with the filename it was loaded from."""

    concept: Concept
    filename: str | None = None

    @property
    def concept_id(self) -> str:
        return self.concept.concept_id


@dataclass(frozen=True)
class ConceptAuthoredSet:
    concepts: tuple[LoadedConcept, ...]


def _empty_form_registry() -> dict[str, FormDefinition]:
    return {}


@dataclass(frozen=True)
class ConceptPipelineContext:
    """Inputs the concept pass needs beyond the concepts themselves."""

    form_registry: Mapping[str, FormDefinition] = field(
        default_factory=_empty_form_registry
    )


@dataclass(frozen=True)
class ConceptCheckedRegistry:
    concepts: tuple[LoadedConcept, ...]
    by_id: dict[str, Concept]
    condition_registry: Mapping[str, ConceptInfo]


def _diagnostic(
    level: str,
    code: str,
    message: str,
    loaded: LoadedConcept,
    pass_name: str,
) -> PassDiagnostic:
    return PassDiagnostic(
        level="error" if level == "error" else "warning",
        code=code,
        message=message,
        family=_FAMILY,
        stage=ConceptStage.CHECKED,
        filename=loaded.filename,
        artifact_id=loaded.concept_id,
        pass_name=pass_name,
    )


class ConceptCheckPass:
    family = _FAMILY
    name = "concept.check"
    version = "1"
    input_stage = ConceptStage.AUTHORED
    output_stage = ConceptStage.CHECKED

    def run(
        self, value: ConceptAuthoredSet, context: object
    ) -> PassResult[ConceptCheckedRegistry]:
        form_registry: Mapping[str, FormDefinition] = (
            context.form_registry
            if isinstance(context, ConceptPipelineContext)
            else {}
        )
        errors: list[PassDiagnostic] = []
        warnings: list[PassDiagnostic] = []
        by_id: dict[str, Concept] = {}
        by_canonical_name: dict[str, Concept] = {}
        condition_registry: dict[str, ConceptInfo] = {}

        for loaded in value.concepts:
            concept = loaded.concept
            if not concept.concept_id:
                errors.append(
                    _diagnostic(
                        "error", "concept.id.missing", "concept missing 'concept_id'",
                        loaded, self.name,
                    )
                )
                continue
            if concept.concept_id in by_id:
                errors.append(
                    _diagnostic(
                        "error",
                        "concept.id.duplicate",
                        f"duplicate concept id '{concept.concept_id}'",
                        loaded,
                        self.name,
                    )
                )
                continue
            if not concept.canonical_name:
                errors.append(
                    _diagnostic(
                        "error",
                        "concept.canonical_name.missing",
                        f"concept '{concept.concept_id}' missing 'canonical_name'",
                        loaded,
                        self.name,
                    )
                )
                continue
            try:
                parsed_name = parse(concept.canonical_name)
            except ParseError:
                parsed_name = None
            if (
                not isinstance(parsed_name, Ident)
                or parsed_name.name != concept.canonical_name
            ):
                errors.append(
                    _diagnostic(
                        "error",
                        "concept.canonical_name.invalid",
                        (
                            f"concept '{concept.concept_id}' canonical name "
                            f"'{concept.canonical_name}' is not a CEL identifier"
                        ),
                        loaded,
                        self.name,
                    )
                )
                continue
            if concept.canonical_name in by_canonical_name:
                errors.append(
                    _diagnostic(
                        "error",
                        "concept.canonical_name.duplicate",
                        f"duplicate concept canonical name '{concept.canonical_name}'",
                        loaded,
                        self.name,
                    )
                )
                continue
            entry = concept.lexical_entry
            form_name = (
                None if entry is None else entry.physical_dimension_form
            )
            form = None if not form_name else form_registry.get(form_name)
            if form_name and form is None:
                warnings.append(
                    _diagnostic(
                        "warning",
                        "concept.form.dangling",
                        (
                            f"concept '{concept.concept_id}' references missing form "
                            f"'{form_name}'"
                        ),
                        loaded,
                        self.name,
                    )
                )
            if form is not None:
                has_category_metadata = bool(concept.category_values) or not (
                    concept.category_extensible
                )
                if form.kind is not KindType.CATEGORY and has_category_metadata:
                    errors.append(
                        _diagnostic(
                            "error",
                            "concept.category_metadata.invalid_kind",
                            (
                                f"concept '{concept.concept_id}' has category metadata "
                                f"but form '{form.name}' has kind '{form.kind.value}'"
                            ),
                            loaded,
                            self.name,
                        )
                    )
                    continue
                condition_registry[concept.canonical_name] = ConceptInfo(
                    id=concept.concept_id,
                    canonical_name=concept.canonical_name,
                    kind=form.kind,
                    category_values=(
                        list(concept.category_values)
                        if form.kind is KindType.CATEGORY
                        else []
                    ),
                    category_extensible=(
                        concept.category_extensible
                        if form.kind is KindType.CATEGORY
                        else True
                    ),
                )
            by_id[concept.concept_id] = concept
            by_canonical_name[concept.canonical_name] = concept

        diagnostics = tuple(errors) + tuple(warnings)
        if errors:
            return PassResult(output=None, diagnostics=diagnostics)
        return PassResult(
            output=ConceptCheckedRegistry(
                concepts=value.concepts,
                by_id=by_id,
                condition_registry=condition_registry,
            ),
            diagnostics=diagnostics,
        )


def register_concept_pipeline(registry: PipelineRegistry) -> None:
    registry.register(ConceptCheckPass, family=_FAMILY)


def run_concept_pipeline(
    concepts: tuple[LoadedConcept, ...] | list[LoadedConcept],
    *,
    context: ConceptPipelineContext | None = None,
    target_stage: ConceptStage = ConceptStage.CHECKED,
) -> PipelineResult[object]:
    registry = PipelineRegistry()
    register_concept_pipeline(registry)
    return run_pipeline(
        ConceptAuthoredSet(concepts=tuple(concepts)),
        family=_FAMILY,
        start_stage=ConceptStage.AUTHORED,
        target_stage=target_stage,
        registry=registry,
        context=context if context is not None else ConceptPipelineContext(),
    )
