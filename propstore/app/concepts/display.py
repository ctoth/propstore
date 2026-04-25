from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

from .mutation import (
    ConceptCategoriesReport,
    ConceptCategoryEntry,
    ConceptDisplayError,
    ConceptListEntry,
    ConceptListReport,
    ConceptListRequest,
    ConceptSearchHit,
    ConceptSearchReport,
    ConceptSearchRequest,
    ConceptShowReport,
    ConceptShowRequest,
    UnknownConceptError,
    _concept_display_handle,
    _concept_document,
    _concept_ref,
    _find_concept_entry,
    _loaded_concepts,
    _require_sidecar,
)
from propstore.app.repository_views import repository_view_label
from propstore.sidecar.sqlite import connect_sidecar

if TYPE_CHECKING:
    from propstore.repository import Repository


def search_concepts(
    repo: Repository,
    request: ConceptSearchRequest,
) -> ConceptSearchReport:
    _ = repository_view_label(request.repository_view)
    sidecar = _require_sidecar(repo)
    conn = connect_sidecar(sidecar)
    try:
        rows = conn.execute(
            "SELECT "
            "COALESCE(NULLIF(concept.primary_logical_id, ''), concept.id), "
            "concept.primary_logical_id, "
            "concept_fts.canonical_name, "
            "concept.status, "
            "concept_fts.definition "
            "FROM concept_fts JOIN concept ON concept.id = concept_fts.concept_id "
            "WHERE concept_fts MATCH ? LIMIT ?",
            (request.query, request.limit),
        ).fetchall()
    finally:
        conn.close()
    return ConceptSearchReport(
        hits=tuple(
            ConceptSearchHit(
                handle=str(row[0]),
                logical_id=None if row[1] is None else str(row[1]),
                canonical_name=str(row[2]),
                status=None if row[3] is None else str(row[3]),
                definition=str(row[4] or ""),
            )
            for row in rows
        )
    )


def list_concepts(
    repo: Repository,
    request: ConceptListRequest,
) -> ConceptListReport:
    _ = repository_view_label(request.repository_view)
    loaded_concepts = _loaded_concepts(repo)
    if not loaded_concepts:
        return ConceptListReport(concepts_found=False, entries=())

    entries: list[ConceptListEntry] = []
    for concept_entry in loaded_concepts:
        data = concept_entry.record.to_payload()
        concept_domain = str(data.get("domain", ""))
        concept_status = str(data.get("status", ""))
        if request.domain and concept_domain != request.domain:
            continue
        if request.status and concept_status != request.status:
            continue
        entries.append(
            ConceptListEntry(
                handle=_concept_display_handle(data),
                canonical_name=str(data.get("canonical_name", "?")),
                status=concept_status,
            )
        )
    return ConceptListReport(
        concepts_found=True,
        entries=tuple(entries[: request.limit]),
    )


def list_concept_categories(repo: Repository) -> ConceptCategoriesReport:
    entries: list[ConceptCategoryEntry] = []
    for concept_entry in _loaded_concepts(repo):
        data = concept_entry.record.to_payload()
        if data.get("form") != "category":
            continue
        raw_form_parameters = data.get("form_parameters")
        if raw_form_parameters is None:
            form_parameters: Mapping[str, object] = {}
        elif isinstance(raw_form_parameters, Mapping):
            form_parameters = raw_form_parameters
        else:
            raise ConceptDisplayError(
                f"'{data.get('canonical_name')}' form_parameters must be a mapping"
            )
        raw_values = form_parameters.get("values", [])
        values = (
            tuple(str(value) for value in raw_values)
            if isinstance(raw_values, list)
            else ()
        )
        entries.append(
            ConceptCategoryEntry(
                canonical_name=str(data["canonical_name"]),
                values=values,
                extensible=bool(form_parameters.get("extensible", True)),
            )
        )
    return ConceptCategoriesReport(entries=tuple(entries))


def show_concept(
    repo: Repository,
    request: ConceptShowRequest,
) -> ConceptShowReport:
    from propstore.source import load_alignment_artifact

    handle = request.concept_id_or_name
    if handle.startswith("align:"):
        try:
            _, artifact = load_alignment_artifact(repo, handle)
        except FileNotFoundError as exc:
            raise UnknownConceptError(handle) from exc
        return ConceptShowReport(
            rendered=repo.families.concept_alignments.render(artifact)
        )

    concept_entry = _find_concept_entry(repo, handle)
    if concept_entry is None:
        raise UnknownConceptError(handle)
    ref = _concept_ref(concept_entry)
    document = _concept_document(repo, ref, concept_entry.record.to_payload())
    return ConceptShowReport(rendered=repo.families.concepts.render(document))
