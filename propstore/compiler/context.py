"""The canonical compilation context — shared symbol tables for the passes.

A :class:`CompilationContext` is the immutable bundle of registries the semantic
passes resolve against: the form registry, the set of known context ids, the
concepts keyed by id, a claim index, and the canonical-name-keyed condition
registry produced by the checked concept pass. It is built once per workflow and
threaded through the claim pipeline.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from condition_ir import ConceptInfo

from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.families.concepts_passes import (
    ConceptCheckedRegistry,
    ConceptPipelineContext,
    LoadedConcept,
    run_concept_pipeline,
)
from propstore.families.forms import FormDefinition
from propstore.families.forms_passes import FormCheckedRegistry, LoadedForm, run_form_pipeline

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class CompilationContext:
    """Immutable symbol tables and registries for canonical semantic compilation."""

    form_registry: FormCheckedRegistry
    context_ids: frozenset[str]
    concepts_by_id: Mapping[str, Concept]
    claim_index: Mapping[str, Claim]
    condition_registry: Mapping[str, ConceptInfo]

    def __post_init__(self) -> None:
        if type(self.form_registry) is not FormCheckedRegistry:
            raise TypeError("compilation context requires a FormCheckedRegistry")


def build_compiler_claim_index(claims: Sequence[Claim]) -> dict[str, Claim]:
    """Index claims by ``claim_id`` (the flat analog of the reference index)."""

    return {claim.claim_id: claim for claim in claims}


def build_compilation_context(
    checked_concepts: ConceptCheckedRegistry,
    *,
    form_registry: FormCheckedRegistry | None = None,
    claims: Sequence[Claim] = (),
    context_ids: Iterable[str] | None = None,
) -> CompilationContext:
    """Build compiler symbol tables from the checked concept owner output."""

    return CompilationContext(
        form_registry=form_registry if form_registry is not None else FormCheckedRegistry(forms=(), registry={}),
        context_ids=frozenset(context_ids or ()),
        concepts_by_id=MappingProxyType(dict(checked_concepts.by_id)),
        claim_index=MappingProxyType(build_compiler_claim_index(claims)),
        condition_registry=MappingProxyType(dict(checked_concepts.condition_registry)),
    )


def build_compilation_context_from_repo(
    repo: Repository | None,
    *,
    claims: Sequence[Claim] = (),
    context_ids: Iterable[str] | None = None,
    commit: str | None = None,
) -> CompilationContext:
    """Build a compilation context by reading concepts + forms from a repository."""

    concepts: list[Concept] = []
    form_registry: dict[str, FormDefinition] = {}
    if repo is not None:
        concepts = [
            handle.document
            for handle in repo.families.by_name("concept").iter_handles(commit=commit)
        ]
        form_registry = {
            handle.document.name: handle.document
            for handle in repo.families.by_name("form").iter_handles(commit=commit)
        }
    form_result = run_form_pipeline([
        LoadedForm(form=form) for form in form_registry.values()
    ])
    if not isinstance(form_result.output, FormCheckedRegistry):
        detail = "; ".join(diagnostic.message for diagnostic in form_result.diagnostics)
        raise ValueError(f"form validation failed: {detail}")
    result = run_concept_pipeline(
        [LoadedConcept(concept=concept) for concept in concepts],
        context=ConceptPipelineContext(form_registry=form_registry),
    )
    if not isinstance(result.output, ConceptCheckedRegistry):
        detail = "; ".join(diagnostic.message for diagnostic in result.diagnostics)
        raise ValueError(f"concept validation failed: {detail}")
    return build_compilation_context(
        result.output,
        form_registry=form_result.output,
        claims=claims,
        context_ids=context_ids,
    )
