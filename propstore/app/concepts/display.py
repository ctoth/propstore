"""Application-layer concept list / search summary rows.

Both builders take an already-open :class:`~propstore.world.WorldQuery` and a
:class:`~propstore.world.RenderPolicy`; concepts hidden by the policy
(:meth:`RenderPolicy.admits`) are filtered at render time, never dropped from
storage. The rewrite's concept search is a case-insensitive substring match
(:meth:`WorldQuery.search`); :class:`ConceptSearchSyntaxError` is defined for the
adapter contract (a future FTS backend raises it for malformed queries), but the
substring matcher accepts every query.
"""

from __future__ import annotations

from dataclasses import dataclass

from propstore.families.concepts import Concept
from propstore.reporting import JsonReportMixin
from propstore.world import RenderPolicy, WorldQuery


class ConceptDisplayError(Exception):
    """Base class for expected concept-display failures."""


class ConceptSearchSyntaxError(ConceptDisplayError):
    """Raised when a search query is not valid search syntax."""

    def __init__(self, query: str) -> None:
        super().__init__("Search query is not valid search syntax.")
        self.query = query


@dataclass(frozen=True)
class ConceptListEntry:
    concept_id: str
    canonical_name: str
    status: str
    definition: str | None


@dataclass(frozen=True)
class ConceptListReport(JsonReportMixin):
    concepts_found: bool
    entries: tuple[ConceptListEntry, ...]


@dataclass(frozen=True)
class ConceptSearchEntry:
    concept_id: str
    canonical_name: str
    status: str
    definition: str | None


@dataclass(frozen=True)
class ConceptSearchReport(JsonReportMixin):
    hits: tuple[ConceptSearchEntry, ...]


def list_concepts(
    world: WorldQuery, *, policy: RenderPolicy, limit: int = 50
) -> ConceptListReport:
    """Summary rows for every policy-visible concept."""

    concepts = sorted(world.all_concepts(), key=lambda concept: str(concept.concept_id))
    visible = [concept for concept in concepts if policy.admits(concept.status)]
    entries = tuple(_list_entry(concept) for concept in visible[:limit])
    return ConceptListReport(concepts_found=bool(concepts), entries=entries)


def search_concepts(
    world: WorldQuery, query: str, *, policy: RenderPolicy, limit: int = 20
) -> ConceptSearchReport:
    """Summary rows for policy-visible concepts whose name matches ``query``."""

    hits: list[ConceptSearchEntry] = []
    for hit in world.search(query):
        concept = world.get_concept(str(hit.concept_id))
        if concept is None or not policy.admits(concept.status):
            continue
        hits.append(_search_entry(concept))
        if len(hits) >= limit:
            break
    return ConceptSearchReport(hits=tuple(hits))


def _list_entry(concept: Concept) -> ConceptListEntry:
    return ConceptListEntry(
        concept_id=str(concept.concept_id),
        canonical_name=concept.canonical_name,
        status=concept.status.value,
        definition=concept.definition,
    )


def _search_entry(concept: Concept) -> ConceptSearchEntry:
    return ConceptSearchEntry(
        concept_id=str(concept.concept_id),
        canonical_name=concept.canonical_name,
        status=concept.status.value,
        definition=concept.definition,
    )
