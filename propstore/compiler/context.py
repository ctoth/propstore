"""The canonical compilation context — shared symbol tables for the passes.

A :class:`CompilationContext` is the immutable bundle of registries the semantic
passes resolve against: the form registry, the set of known context ids, the
concepts keyed by id, a claim index, and the id-keyed CEL concept registry. It is
built once per workflow and threaded through the claim pipeline.

This is the flat-charter design: the concepts are the one ``Concept`` charter,
the claim index is a plain ``{claim_id: Claim}`` map, and the CEL registry is
condition-ir's own ``{concept_id: ConceptInfo}`` (built by
:mod:`propstore.cel_registry`). There is no ``ConceptRecord`` / ``ClaimFileEntry``
/ ``to_payload`` projection mass.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from condition_ir import ConceptInfo

from propstore.cel_registry import build_canonical_cel_registry
from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.families.concepts_passes import LoadedConcept
from propstore.families.forms import FormDefinition

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class CompilationContext:
    """Immutable symbol tables and registries for canonical semantic compilation."""

    form_registry: Mapping[str, FormDefinition]
    context_ids: frozenset[str]
    concepts_by_id: Mapping[str, Concept]
    claim_index: Mapping[str, Claim]
    cel_registry: Mapping[str, ConceptInfo]


def build_compiler_claim_index(claims: Sequence[Claim]) -> dict[str, Claim]:
    """Index claims by ``claim_id`` (the flat analog of the reference index)."""

    return {claim.claim_id: claim for claim in claims}


def build_authored_concept_registry(
    concepts: Iterable[Concept],
    *,
    form_registry: Mapping[str, FormDefinition] | None = None,
) -> dict[str, Concept]:
    """Build the canonical id-keyed authored-concept lookup."""

    return {concept.concept_id: concept for concept in concepts}


def _build_context(
    concepts: Sequence[Concept],
    form_registry: Mapping[str, FormDefinition],
    *,
    claims: Sequence[Claim],
    context_ids: Iterable[str] | None,
) -> CompilationContext:
    concepts_by_id = build_authored_concept_registry(
        concepts, form_registry=form_registry
    )
    return CompilationContext(
        form_registry=MappingProxyType(dict(form_registry)),
        context_ids=frozenset(context_ids or ()),
        concepts_by_id=MappingProxyType(concepts_by_id),
        claim_index=MappingProxyType(build_compiler_claim_index(claims)),
        cel_registry=MappingProxyType(
            build_canonical_cel_registry(concepts, form_registry)
        ),
    )


def build_compilation_context_from_loaded(
    concepts: Sequence[LoadedConcept],
    *,
    form_registry: Mapping[str, FormDefinition] | None = None,
    claims: Sequence[Claim] = (),
    context_ids: Iterable[str] | None = None,
) -> CompilationContext:
    """Build a compilation context from already-loaded concepts + a form registry."""

    return _build_context(
        [loaded.concept for loaded in concepts],
        form_registry if form_registry is not None else {},
        claims=claims,
        context_ids=context_ids,
    )


def build_compilation_context_from_repo(
    repo: Repository | None,
    *,
    claims: Sequence[Claim] = (),
    context_ids: Iterable[str] | None = None,
    commit: str | None = None,
) -> CompilationContext:
    """Build a compilation context by reading concepts + forms from a repository."""

    if repo is None:
        return _build_context([], {}, claims=claims, context_ids=context_ids)
    concepts: list[Concept] = [
        handle.document
        for handle in repo.families.by_name("concept").iter_handles(commit=commit)
    ]
    form_registry: dict[str, FormDefinition] = {
        handle.document.name: handle.document
        for handle in repo.families.by_name("form").iter_handles(commit=commit)
    }
    return _build_context(
        concepts, form_registry, claims=claims, context_ids=context_ids
    )
