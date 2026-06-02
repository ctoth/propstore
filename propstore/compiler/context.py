"""Shared canonical compilation context."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from quire.documents import LoadedDocument
from quire.references import FamilyReferenceIndex
from quire.tree_path import (
    TreePath as KnowledgePath,
    coerce_tree_path as coerce_knowledge_path,
)
from propstore.cel_registry import build_canonical_cel_registry
from propstore.core.conditions.registry import (
    ConditionRegistry,
)
from propstore.conflict_detector.models import (
    ConflictConcept,
    ConflictConceptRegistry,
    ConflictParameterization,
)
from propstore.families.claims.declaration import ClaimDocument
from propstore.families.claims.references import (
    ClaimReferenceRecord,
    build_claim_reference_index,
)
from propstore.families.claims.declaration import claim_logical_id_formatted
from propstore.families.concepts.declaration import (
    AUTHORED_CONCEPT_CHARTER,
    ConceptDocument,
)
from propstore.families.forms.stages import (
    FormDefinition,
    load_all_forms_path,
    parse_form,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class CompilationContext:
    """Immutable symbol tables and registries for canonical semantic compilation."""

    form_registry: Mapping[str, FormDefinition]
    context_ids: frozenset[str]
    concepts_by_id: Mapping[str, ConceptDocument]
    concept_index: FamilyReferenceIndex[ConceptDocument]
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord]
    cel_registry: ConditionRegistry


def _freeze_mapping(data: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(data))


def build_compiler_claim_index(
    claims: Sequence[LoadedDocument[ClaimDocument]],
) -> FamilyReferenceIndex[ClaimReferenceRecord]:
    return build_claim_reference_index(claims)


def concept_form_definition(
    concept_ref: object,
    context: CompilationContext,
) -> FormDefinition | None:
    concept_id = context.concept_index.resolve_id(concept_ref)
    if concept_id is None:
        return None
    document = context.concepts_by_id.get(concept_id)
    if document is None:
        return None
    form_definition = context.form_registry.get(
        document.lexical_entry.physical_dimension_form
    )
    return form_definition if isinstance(form_definition, FormDefinition) else None


def compiler_concept_match_kind(
    raw_text: str,
    resolved_id: str,
    document: ConceptDocument | None,
) -> tuple[str | None, str | None]:
    if raw_text == resolved_id:
        return "artifact_id", raw_text
    if document is None:
        return None, None
    if document.lexical_entry.canonical_form.written_rep == raw_text:
        return "canonical_name", raw_text
    for logical_id in document.logical_ids:
        if f"{logical_id.namespace}:{logical_id.value}" == raw_text:
            return "logical_id", raw_text
        if logical_id.value == raw_text:
            return "logical_value", raw_text
    for alias in document.aliases:
        if alias.name == raw_text:
            return "alias", raw_text
    return None, None


def compiler_claim_match_kind(
    raw_text: str,
    resolved_id: str,
    record: ClaimReferenceRecord | None,
) -> tuple[str | None, str | None]:
    if raw_text == resolved_id:
        return "artifact_id", raw_text
    if record is None:
        return None, None
    for logical_id in record.claim.logical_ids:
        if claim_logical_id_formatted(logical_id) == raw_text:
            return "logical_id", raw_text
        if logical_id.value == raw_text:
            return "logical_value", raw_text
    return None, None


def _concept_reference_index(
    documents: Iterable[ConceptDocument],
) -> FamilyReferenceIndex[ConceptDocument]:
    return FamilyReferenceIndex.from_records(
        documents,
        family="concept",
        artifact_id=lambda document: document.artifact_id,
        keys=AUTHORED_CONCEPT_CHARTER.family.reference_keys,
    )


def _build_context_from_concepts(
    concepts: list[LoadedDocument[ConceptDocument]],
    form_registry: dict[str, FormDefinition],
    *,
    claim_files: Sequence[LoadedDocument[ClaimDocument]] | None,
    context_ids: set[str] | None,
) -> CompilationContext:
    concepts_by_id: dict[str, ConceptDocument] = {}

    for concept in concepts:
        document = concept.document
        artifact_id = str(document.artifact_id)
        concepts_by_id[artifact_id] = document

    concept_index = _concept_reference_index(concepts_by_id.values())
    return CompilationContext(
        form_registry=_freeze_mapping(form_registry),
        context_ids=frozenset(context_ids or set()),
        concepts_by_id=MappingProxyType(dict(concepts_by_id)),
        concept_index=concept_index,
        claim_index=(
            build_compiler_claim_index(())
            if claim_files is None
            else build_compiler_claim_index(claim_files)
        ),
        cel_registry=build_canonical_cel_registry(
            concept.document for concept in concepts
        ).with_standard_synthetic_bindings(),
    )


def build_compilation_context_from_loaded(
    concepts: list[LoadedDocument[ConceptDocument]],
    *,
    forms_dir: Path | KnowledgePath | None = None,
    form_registry: dict[str, FormDefinition] | None = None,
    claim_files: Sequence[LoadedDocument[ClaimDocument]] | None = None,
    context_ids: set[str] | None = None,
) -> CompilationContext:
    resolved_form_registry = (
        dict(form_registry)
        if form_registry is not None
        else (
            {}
            if forms_dir is None
            else load_all_forms_path(coerce_knowledge_path(forms_dir))
        )
    )
    return _build_context_from_concepts(
        concepts,
        resolved_form_registry,
        claim_files=claim_files,
        context_ids=context_ids,
    )


def build_compilation_context_from_repo(
    repo: Repository | None,
    *,
    claim_files: Sequence[LoadedDocument[ClaimDocument]] | None = None,
    context_ids: set[str] | None = None,
    commit: str | None = None,
) -> CompilationContext:
    if repo is None:
        return _build_context_from_concepts(
            [],
            {},
            claim_files=claim_files,
            context_ids=context_ids,
        )
    tree = repo.tree(commit=commit)
    concepts: list[LoadedDocument[ConceptDocument]] = []
    for handle in repo.families.concepts.iter_handles(commit=commit):
        concepts.append(
            LoadedDocument(
                filename=handle.ref.name,
                artifact_path=tree / handle.address.require_path(),
                store_root=tree,
                document=handle.document,
            )
        )

    form_registry: dict[str, FormDefinition] = {}
    for handle in repo.families.forms.iter_handles(commit=commit):
        document = handle.document
        form_registry[document.name] = parse_form(document.name, document)

    return _build_context_from_concepts(
        concepts,
        form_registry,
        claim_files=claim_files,
        context_ids=context_ids,
    )


def concept_registry_for_context(
    context: CompilationContext,
) -> ConflictConceptRegistry:
    unique_reference_keys: dict[str, list[str]] = {
        artifact_id: [artifact_id] for artifact_id in context.concepts_by_id
    }
    for key, candidates in context.concept_index.lookup.items():
        if len(candidates) != 1:
            continue
        unique_reference_keys.setdefault(candidates[0], []).append(key)
    entries: list[ConflictConcept] = []
    for artifact_id, document in context.concepts_by_id.items():
        form_name = document.lexical_entry.physical_dimension_form
        form_definition = context.form_registry.get(form_name)
        entries.append(
            ConflictConcept(
                concept_id=artifact_id,
                canonical_name=document.lexical_entry.canonical_form.written_rep,
                form_name=form_name,
                reference_keys=tuple(
                    unique_reference_keys.get(artifact_id, (artifact_id,))
                ),
                form_definition=form_definition,
                parameterizations=tuple(
                    ConflictParameterization(
                        inputs=tuple(
                            str(input_id) for input_id in parameterization.inputs
                        ),
                        sympy=parameterization.sympy,
                        exactness=(
                            None
                            if parameterization.exactness is None
                            else parameterization.exactness.value
                        ),
                        conditions=parameterization.conditions,
                    )
                    for parameterization in document.parameterization_relationships
                ),
            )
        )
    return ConflictConceptRegistry(tuple(entries))
