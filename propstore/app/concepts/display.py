from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from quire.sqlalchemy_store import FtsQuerySyntaxError, search_fts_index

from .mutation import (
    ConceptDisplayError,
    ConceptSearchHit,
    ConceptSearchReport,
    ConceptSearchRequest,
    ConceptSidecarMissingError,
)
from propstore.app.repository_views import repository_view_label
from propstore.compiler.workflows import build_repository_world_store
from propstore.families.concepts.declaration import CONCEPT_CHARTER
from propstore.families.registry import world_schema

if TYPE_CHECKING:
    from propstore.repository import Repository


class ConceptSearchSyntaxError(ConceptDisplayError):
    def __init__(self, query: str) -> None:
        super().__init__("Search query is not valid FTS syntax.")
        self.query = query


def search_concepts(
    repo: Repository,
    request: ConceptSearchRequest,
) -> ConceptSearchReport:
    _ = repository_view_label(request.repository_view)
    derived_store, _rebuilt = build_repository_world_store(repo)
    if not derived_store.path.exists():
        raise ConceptSidecarMissingError("sidecar not found. Run 'pks build' first.")
    schema = world_schema()
    concept = schema.model(CONCEPT_CHARTER.family.name)
    try:
        with derived_store.readonly_session(schema) as derived:
            hits = search_fts_index(
                derived,
                "concept_fts",
                request.query,
                limit=request.limit,
            )
            concept_ids = tuple(hit.entity_id for hit in hits)
            if not concept_ids:
                return ConceptSearchReport(hits=())
            concepts = derived.execute(
                select(concept).where(concept.id.in_(concept_ids))
            ).scalars()
            concepts_by_id = {row.id: row for row in concepts}
    except FtsQuerySyntaxError as exc:
        raise ConceptSearchSyntaxError(request.query) from exc
    return ConceptSearchReport(
        hits=tuple(
            ConceptSearchHit(
                handle=str(row.primary_logical_id or row.id),
                logical_id=(
                    None
                    if row.primary_logical_id is None
                    else str(row.primary_logical_id)
                ),
                canonical_name=str(row.canonical_name),
                status=None if row.status is None else str(row.status),
                definition=str(row.definition or ""),
            )
            for concept_id in concept_ids
            for row in (concepts_by_id.get(concept_id),)
            if row is not None
        )
    )
