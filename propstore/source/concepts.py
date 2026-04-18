from __future__ import annotations

from pathlib import Path

from propstore.repository import Repository
from propstore.artifacts.refs import SourceRef
from quire.documents import decode_document_path

from .common import load_source_concepts_document
from propstore.artifacts.documents.sources import (
    SourceConceptEntryDocument,
    SourceConceptFormParametersDocument,
    SourceConceptRegistryMatchDocument,
    SourceConceptsDocument,
)
from .registry import primary_branch_concept_match


def get_valid_form_names(repo: Repository) -> list[str] | None:
    names = sorted(ref.name for ref in repo.families.forms.list())
    return names if names else None


def validate_form_name(form: str, repo: Repository) -> None:
    valid_forms = get_valid_form_names(repo)
    if valid_forms is None:
        return
    if form not in valid_forms:
        raise ValueError(f"Unknown form {form!r}. Valid forms: {', '.join(valid_forms)}")


def normalize_source_concepts_document(
    repo: Repository,
    data: SourceConceptsDocument,
) -> SourceConceptsDocument:
    normalized_concepts: list[SourceConceptEntryDocument] = []
    for index, entry in enumerate(data.concepts, start=1):
        local_name = (entry.local_name or entry.proposed_name or "").strip()
        proposed_name = (entry.proposed_name or entry.local_name or "").strip()
        definition = (entry.definition or "").strip()
        form = (entry.form or "").strip()
        if not all((local_name, proposed_name, definition, form)):
            raise ValueError(f"concept #{index} is missing local_name/proposed_name/definition/form")
        validate_form_name(form, repo)
        registry_match = primary_branch_concept_match(repo, local_name) or primary_branch_concept_match(
            repo,
            proposed_name,
        )
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
                registry_match=(
                    None
                    if registry_match is None
                    else SourceConceptRegistryMatchDocument(
                        artifact_id=registry_match["artifact_id"],
                        canonical_name=registry_match.get("canonical_name"),
                    )
                ),
                artifact_code=entry.artifact_code,
            )
        )
    return SourceConceptsDocument(concepts=tuple(normalized_concepts))


def commit_source_concepts_batch(repo: Repository, source_name: str, concepts_file: Path) -> str:
    loaded = decode_document_path(concepts_file, SourceConceptsDocument)
    normalized = normalize_source_concepts_document(repo, loaded)
    return repo.families.source_concepts.save(
        SourceRef(source_name),
        normalized,
        message=f"Write concepts for {source_name}",
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
    validate_form_name(form, repo)
    existing = load_source_concepts_document(repo, source_name) or SourceConceptsDocument(concepts=())
    concepts = [entry for entry in existing.concepts if entry.local_name != local_name]
    entry = SourceConceptEntryDocument(
        local_name=local_name,
        proposed_name=local_name,
        definition=definition,
        form=form,
        form_parameters=form_parameters,
    )
    concepts.append(entry)
    doc = normalize_source_concepts_document(repo, SourceConceptsDocument(concepts=tuple(concepts)))
    repo.families.source_concepts.save(
        SourceRef(source_name),
        doc,
        message=f"Propose concepts for {source_name}",
    )
    for normalized_entry in doc.concepts:
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
