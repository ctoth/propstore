"""Author concept proposals onto a source branch.

A source branch proposes concepts in its own local vocabulary. Each proposal
records a ``local_name``/``proposed_name``, a definition, and a ``form``; if a
matching canonical concept already exists on the primary branch the proposal is
marked ``linked`` (carrying the canonical ``registry_match``), otherwise
``proposed``. Linking is a non-committal annotation — it never rewrites the
source-local handle or collapses the proposal into the canonical concept.
"""

from __future__ import annotations

from pathlib import Path

from cel_parser import Ident, ParseError, parse
from quire.documents import decode_document_path

from propstore.families.concepts import Concept
from propstore.families.registry import SourceRef
from propstore.families.sources import (
    SourceConceptEntryDocument,
    SourceConceptFormParametersDocument,
    SourceConceptRegistryMatchDocument,
    SourceConceptsDocument,
)
from propstore.repository import Repository

from .common import (
    current_source_branch_head,
    is_stale_branch_error,
    load_source_concepts_document,
    normalize_source_slug,
)


def get_valid_form_names(repo: Repository) -> list[str] | None:
    """Return the sorted master-branch form names, or ``None`` if none exist."""

    names = sorted(str(ref) for ref in repo.families.form.iter_refs())
    return names if names else None


def validate_form_name(form: str, repo: Repository) -> None:
    """Reject *form* unless it is a known master-branch form (or none exist yet)."""

    valid_forms = get_valid_form_names(repo)
    if valid_forms is None:
        return
    if form not in valid_forms:
        raise ValueError(
            f"Unknown form {form!r}. Valid forms: {', '.join(valid_forms)}"
        )


def primary_branch_concept_match(
    repo: Repository, name: str
) -> SourceConceptRegistryMatchDocument | None:
    """Return the canonical concept matching *name* by canonical name, or ``None``.

    Matches against the primary-branch concept family by normalised canonical
    name. This is the minimal concept-registry lookup the source-authoring path
    needs; the full primary-branch projection (parameterization-group previews,
    etc.) lands with the promote subsystem.
    """

    target = normalize_source_slug(name).casefold()
    for handle in repo.families.concept.iter_handles():
        concept = handle.document
        if not isinstance(concept, Concept):
            continue
        if normalize_source_slug(concept.canonical_name).casefold() == target:
            return SourceConceptRegistryMatchDocument(
                artifact_id=concept.concept_id,
                canonical_name=concept.canonical_name,
            )
    return None


def normalize_source_concepts_document(
    repo: Repository,
    data: SourceConceptsDocument,
) -> SourceConceptsDocument:
    """Validate + enrich every concept proposal (required fields, form, linking)."""

    normalized_concepts: list[SourceConceptEntryDocument] = []
    for index, entry in enumerate(data.concepts, start=1):
        local_name = (entry.local_name or entry.proposed_name or "").strip()
        proposed_name = (entry.proposed_name or entry.local_name or "").strip()
        definition = (entry.definition or "").strip()
        form = (entry.form or "").strip()
        if not all((local_name, proposed_name, definition, form)):
            raise ValueError(
                f"concept #{index} is missing local_name/proposed_name/definition/form"
            )
        try:
            parsed_name = parse(proposed_name)
        except ParseError:
            parsed_name = None
        if not isinstance(parsed_name, Ident) or parsed_name.name != proposed_name:
            raise ValueError(
                f"concept #{index} proposed_name {proposed_name!r} is not a CEL identifier"
            )
        validate_form_name(form, repo)
        registry_match = primary_branch_concept_match(
            repo, local_name
        ) or primary_branch_concept_match(repo, proposed_name)
        normalized_concepts.append(
            SourceConceptEntryDocument(
                local_name=local_name,
                proposed_name=proposed_name,
                definition=definition,
                form=form,
                aliases=entry.aliases,
                form_parameters=entry.form_parameters,
                parameterization_relationships=entry.parameterization_relationships,
                status="linked" if registry_match is not None else "proposed",
                registry_match=registry_match,
                artifact_code=entry.artifact_code,
            )
        )
    return SourceConceptsDocument(concepts=tuple(normalized_concepts))


def commit_source_concepts_batch(
    repo: Repository, source_name: str, concepts_file: Path
) -> str:
    """Ingest a concepts-batch YAML onto a source branch; return commit sha."""

    loaded = decode_document_path(concepts_file, SourceConceptsDocument)
    normalized = normalize_source_concepts_document(repo, loaded)
    return repo.families.source_concepts.save(
        SourceRef(source_name),
        normalized,
        message=f"Write concepts for {normalize_source_slug(source_name)}",
    )


def commit_source_concept_proposal(
    repo: Repository,
    source_name: str,
    *,
    local_name: str,
    definition: str,
    form: str,
    form_parameters: SourceConceptFormParametersDocument | None = None,
) -> SourceConceptEntryDocument:
    """Propose one concept onto a source branch (compare-and-swap retry).

    Replaces any existing proposal with the same ``local_name``. Returns the
    normalised entry as stored.
    """

    validate_form_name(form, repo)
    last_doc: SourceConceptsDocument | None = None
    for attempt in range(8):
        expected_head = current_source_branch_head(repo, source_name)
        existing = load_source_concepts_document(
            repo, source_name
        ) or SourceConceptsDocument(concepts=())
        concepts = [
            entry for entry in existing.concepts if entry.local_name != local_name
        ]
        concepts.append(
            SourceConceptEntryDocument(
                local_name=local_name,
                proposed_name=local_name,
                definition=definition,
                form=form,
                form_parameters=form_parameters,
            )
        )
        doc = normalize_source_concepts_document(
            repo, SourceConceptsDocument(concepts=tuple(concepts))
        )
        try:
            repo.families.source_concepts.save(
                SourceRef(source_name),
                doc,
                message=f"Propose concepts for {normalize_source_slug(source_name)}",
                expected_head=expected_head,
            )
        except ValueError as exc:
            if attempt == 7 or not is_stale_branch_error(exc):
                raise
            continue
        last_doc = doc
        break
    if last_doc is not None:
        for normalized_entry in last_doc.concepts:
            if normalized_entry.local_name == local_name:
                return normalized_entry
    return SourceConceptEntryDocument(
        local_name=local_name,
        proposed_name=local_name,
        definition=definition,
        form=form,
        form_parameters=form_parameters,
        status="proposed",
    )
