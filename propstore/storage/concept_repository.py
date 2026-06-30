"""Concept authoring + sidecar projection (Phase 1 walking skeleton).

This composes quire directly: ``DocumentFamilyStore`` over a ``GitStore`` backend
for the canonical concept document, and ``build_sqlalchemy_schema`` + the
sqlalchemy store for the content-addressed SQL sidecar. There is no propstore
mirror of any quire type and no coercion across the boundary — we author and read
the one ``Concept`` charter document, and the sidecar columns are exactly the
charter's fields.

This is the *sidecar build* surface for concepts (``build_sidecar``); the
canonical multi-family source-of-truth storage surface is
:class:`propstore.repository.Repository` (``repo.families.concepts``). The two
share the same charter and store; ``ConceptRepository`` exists for the
content-addressed sidecar projection that the render layer queries.

NON-COMMITMENT (PLAN.md §12): :meth:`build_sidecar` NEVER filters, aborts, or
drops. EVERY authored concept becomes a sidecar row, regardless of status.
Deciding which concepts are *visible* is the render layer's job, applied at
render time over the full row set — never baked into the build. Storage holds the
RAW authored form; no normalization is applied on write.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from quire.charters import charter_catalog
from quire.family_store import DocumentFamilyStore
from quire.git_store import GitStore
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.sqlalchemy_store import create_sqlalchemy_store, writable_session

from propstore.families.concepts import Concept


@dataclass(frozen=True)
class _StoreOwner:
    """Placement owner for the document store.

    ``FlatYamlPlacement`` keys file paths off this object's ``branch``; the
    concept placement does not otherwise consult it.
    """

    branch: str = "master"


class ConceptRepository:
    """Author concepts to git and project them into a SQL sidecar.

    Construct over an in-memory ``GitStore`` by default (tests, ephemeral work);
    pass an on-disk backend for a persistent repository.
    """

    def __init__(self, backend: GitStore | None = None) -> None:
        self._store = DocumentFamilyStore(
            owner=_StoreOwner(),
            backend=backend if backend is not None else GitStore.init_memory(),
            # The charter's own document codec encodes/decodes the canonical
            # ``Concept`` document (its ``generated_document()`` IS the class). We
            # use it directly — no propstore-side encode/decode and no second
            # spelling of the concept.
            codec=Concept.__charter__.document_codec(),
        )
        # The artifact family is owned by the charter; we use it directly rather
        # than re-declaring family metadata on the propstore side.
        self._family = Concept.__charter__.family.artifact_family

    def author(self, concept: Concept, *, message: str) -> str:
        """Store the RAW authored concept; return the commit sha.

        No normalization is applied — the concept is committed exactly as
        authored, keyed by its ``concept_id`` identity.
        """

        return self._store.save(
            self._family, concept.concept_id, concept, message=message
        )

    def get(self, concept_id: str) -> Concept | None:
        """Load a concept by identity from the git store, or ``None``."""

        return self._store.load(self._family, concept_id)

    def iter_concepts(self) -> Iterator[Concept]:
        """Iterate every authored concept document in the git store."""

        for handle in self._store.iter_handles(self._family):
            yield handle.document

    def build_sidecar(self, path: Path) -> SqlAlchemySchema:
        """Project EVERY authored concept into a fresh sqlite sidecar.

        Returns the built :class:`SqlAlchemySchema` so the render layer can query
        the same schema instance. (``build_sqlalchemy_schema`` resets the global
        SQLAlchemy mapper registry, so a process holds one live schema at a time;
        callers reuse the returned object rather than rebuilding.)

        This never filters: a ``DRAFT`` or ``BLOCKED`` concept lands as a row
        just like an ``AUTHORED`` one. Visibility is decided later, at render.
        """

        schema = build_sqlalchemy_schema(charter_catalog(Concept.__charter__))
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema) as session:
            for concept in self.iter_concepts():
                session.add_family(
                    "concept",
                    {
                        "concept_id": concept.concept_id,
                        "canonical_name": concept.canonical_name,
                        "status": concept.status,
                        "definition": concept.definition,
                        "ontology_reference": concept.ontology_reference,
                        "lexical_entry": concept.lexical_entry,
                    },
                )
            session.commit()
        return schema
