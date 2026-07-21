"""Sidecar embedding stores over quire's SQLAlchemy vector adapter.

The embedding index lives in the world-sidecar sqlite file but *outside* the
charter schema: its tables are created on demand by :func:`ensure_embedding_tables`
and the ``sqlite_vec`` extension is loaded lazily through :func:`_require_sqlite_vec`
/ :func:`embedding_connection`, so the core package and ``pks`` import and run
without the ``[embeddings]`` extra. The vector storage itself is quire's
:class:`~quire.sqlite_vec_store.SqlAlchemyVecEntityStore` (consumed directly, not
re-implemented); the propstore stores here only supply the entity text projection
(over the ``Claim`` / ``Concept`` charters) and the id/seq bridge the generic
:mod:`propstore.heuristic.embed` layer drives.

Similarity is a heuristic signal: every hit carries its vector distance as a
score, and a query with no registered model or no embedding returns ``[]`` — never
a fabricated distance.
"""

from __future__ import annotations

import hashlib
import importlib
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any

from quire.schema_ir import SchemaVectorCache
from quire.sqlite_vec_store import (
    EMBEDDING_MODEL_TABLE,
    SqlAlchemyVecEntityStore,
    SqlAlchemyVecRegistry,
)
from sqlalchemy import Connection, Engine, create_engine, event, text

from propstore.core.embeddings import (
    EmbeddingEntity,
    claim_embedding_text,
    concept_aliases,
    concept_embedding_text,
)
from propstore.core.store_results import ClaimSimilarityHit, ConceptSimilarityHit
from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.heuristic.embed import (
    embed_entities,
    find_similar_agree_generic,
    find_similar_disagree_generic,
    find_similar_entities,
)
from propstore.heuristic.embedding_identity import EmbeddingModelIdentity

CLAIM_VEC_CACHE = SchemaVectorCache(
    name="claim",
    family_name="claim",
    table="claim_embedding_vec_{model_identity_hash}_{dimensions}",
    entity_id_field="claim_id",
    source_seq_field="rowid",
    source_content_hash_field="claim_id",
    status_table="claim_embedding_status",
)

CONCEPT_VEC_CACHE = SchemaVectorCache(
    name="concept",
    family_name="concept",
    table="concept_embedding_vec_{model_identity_hash}_{dimensions}",
    entity_id_field="concept_id",
    source_seq_field="rowid",
    source_content_hash_field="concept_id",
    status_table="concept_embedding_status",
)

EMBEDDING_CACHES = (CLAIM_VEC_CACHE, CONCEPT_VEC_CACHE)


def _require_sqlite_vec() -> ModuleType:
    try:
        return importlib.import_module("sqlite_vec")
    except ImportError as exc:
        raise ImportError(
            "sqlite-vec is required for embedding commands. "
            "Install with: uv pip install 'propstore[embeddings]'"
        ) from exc


def _content_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


@contextmanager
def embedding_connection(path: Path, *, readonly: bool) -> Iterator[Connection]:
    """Yield a sqlite-vec-enabled SQLAlchemy connection to a sidecar file."""

    _require_sqlite_vec()
    engine = _embedding_engine(path, readonly=readonly)
    conn = engine.connect()
    try:
        yield conn
        if not readonly:
            conn.commit()
    finally:
        conn.close()
        engine.dispose()


def _embedding_engine(path: Path, *, readonly: bool) -> Engine:
    from quire.sqlite_vec_store import load_sqlite_vec_extension

    engine = create_engine(f"sqlite:///{path}", future=True)

    def configure(dbapi_connection: Any, _record: object) -> None:
        load_sqlite_vec_extension(dbapi_connection)
        if readonly:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA query_only = ON")
            finally:
                cursor.close()

    event.listen(engine, "connect", configure)
    return engine


def ensure_embedding_tables(conn: Connection) -> None:
    """Create the embedding registry + per-cache status tables (idempotent).

    Mirrors quire's ``create_vector_cache_schema`` DDL for the registry and status
    tables; the per-model ``vec0`` virtual tables are created lazily by the quire
    entity store on first ``prepare_model``.
    """

    conn.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS "{EMBEDDING_MODEL_TABLE}" (
                model_identity_hash TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL DEFAULT '',
                content_digest TEXT NOT NULL,
                dimensions INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    )
    for cache in EMBEDDING_CACHES:
        status_table = cache.status_table_name
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS "{status_table}" (
                    model_identity_hash TEXT NOT NULL,
                    "{cache.entity_id_field}" TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    embedded_at TEXT NOT NULL,
                    PRIMARY KEY (model_identity_hash, "{cache.entity_id_field}")
                )
                """
            )
        )
        conn.execute(
            text(
                f"""
                CREATE INDEX IF NOT EXISTS "ix_{status_table}_model"
                ON "{status_table}" (model_identity_hash)
                """
            )
        )


def get_registered_models(conn: Connection) -> list[dict[str, Any]]:
    """Return every registered embedding model row."""

    return list(SqlAlchemyVecRegistry(conn).iter_registered_models())


def _rowids(conn: Connection, family: str, id_field: str) -> dict[str, int]:
    rows = conn.execute(
        text(f'SELECT "{id_field}" AS entity_id, rowid AS row_id FROM "{family}"')
    ).mappings()
    return {str(row["entity_id"]): int(row["row_id"]) for row in rows}


class _SidecarEntityStore:
    """Shared id/seq + vector bridge between the heuristic layer and quire."""

    cache: SchemaVectorCache

    def __init__(self, conn: Connection, rowids: Mapping[str, int]) -> None:
        self._conn = conn
        self._rowids = dict(rowids)
        self._vectors = SqlAlchemyVecEntityStore(conn, self.cache)

    def ensure_storage(self) -> None:
        ensure_embedding_tables(self._conn)

    def existing_content_hashes(
        self, model_identity: EmbeddingModelIdentity
    ) -> dict[str, str]:
        return self._vectors.existing_content_hashes(model_identity)

    def prepare_model(
        self,
        model_identity: EmbeddingModelIdentity,
        dimensions: int,
        created_at: str,
    ) -> None:
        self._vectors.prepare_model(model_identity, created_at, dimensions)

    def save_embedding(
        self,
        model_identity: EmbeddingModelIdentity,
        entity: EmbeddingEntity,
        vector_blob: bytes,
        embedded_at: str,
    ) -> None:
        self._vectors.save_embedding(
            model_identity=model_identity,
            entity_id=entity.entity_id,
            seq=entity.seq,
            content_hash=entity.content_hash,
            vector_blob=vector_blob,
            embedded_at=embedded_at,
        )

    def vector_for(
        self, model_identity: EmbeddingModelIdentity, seq: int
    ) -> bytes | None:
        return self._vectors.vector_for(model_identity, seq)

    def resolve_entity(self, entity_id: str) -> tuple[str, int]:
        seq = self._rowids.get(str(entity_id))
        if seq is None:
            raise ValueError(f"{entity_id} is not a known {self.cache.name}")
        return str(entity_id), seq

    def _similar_rows(
        self, model_identity: EmbeddingModelIdentity, query_vector: bytes, k: int
    ) -> list[dict[str, Any]]:
        return list(
            self._vectors.iter_similar_entities(
                model_identity=model_identity, query_vector=query_vector, k=k
            )
        )


class SidecarClaimEmbeddingStore(_SidecarEntityStore):
    cache = CLAIM_VEC_CACHE

    def __init__(
        self,
        conn: Connection,
        claims: Sequence[Claim],
        rowids: Mapping[str, int],
    ) -> None:
        super().__init__(conn, rowids)
        self._claims = {str(claim.claim_id): claim for claim in claims}

    def load_entities(
        self, entity_ids: Sequence[str] | None = None
    ) -> list[EmbeddingEntity]:
        ids = list(entity_ids) if entity_ids is not None else list(self._claims)
        entities: list[EmbeddingEntity] = []
        for entity_id in ids:
            claim = self._claims.get(str(entity_id))
            seq = self._rowids.get(str(entity_id))
            if claim is None or seq is None:
                continue
            body = claim_embedding_text(claim)
            entities.append(
                EmbeddingEntity(str(entity_id), seq, _content_hash(body), body)
            )
        return entities

    def similar_entities(
        self, model_identity: EmbeddingModelIdentity, query_vector: bytes, k: int
    ) -> list[dict[str, Any]]:
        hits: list[dict[str, Any]] = []
        for row in self._similar_rows(model_identity, query_vector, k):
            entity_id = str(row["entity_id"])
            claim = self._claims.get(entity_id)
            concept_id = None if claim is None else _claim_concept_id(claim)
            hits.append(
                {
                    "id": entity_id,
                    "distance": float(row["distance"]),
                    "statement": None if claim is None else claim.statement,
                    "source_paper": None,
                    "concept_id": concept_id,
                }
            )
        return hits


class SidecarConceptEmbeddingStore(_SidecarEntityStore):
    cache = CONCEPT_VEC_CACHE

    def __init__(
        self,
        conn: Connection,
        concepts: Sequence[Concept],
        rowids: Mapping[str, int],
    ) -> None:
        super().__init__(conn, rowids)
        self._concepts = {str(concept.concept_id): concept for concept in concepts}

    def load_entities(
        self, entity_ids: Sequence[str] | None = None
    ) -> list[EmbeddingEntity]:
        ids = list(entity_ids) if entity_ids is not None else list(self._concepts)
        entities: list[EmbeddingEntity] = []
        for entity_id in ids:
            concept = self._concepts.get(str(entity_id))
            seq = self._rowids.get(str(entity_id))
            if concept is None or seq is None:
                continue
            body = concept_embedding_text(concept, concept_aliases(concept))
            entities.append(
                EmbeddingEntity(str(entity_id), seq, _content_hash(body), body)
            )
        return entities

    def similar_entities(
        self, model_identity: EmbeddingModelIdentity, query_vector: bytes, k: int
    ) -> list[dict[str, Any]]:
        hits: list[dict[str, Any]] = []
        for row in self._similar_rows(model_identity, query_vector, k):
            entity_id = str(row["entity_id"])
            concept = self._concepts.get(entity_id)
            hits.append(
                {
                    "id": entity_id,
                    "distance": float(row["distance"]),
                    "primary_logical_id": None,
                    "canonical_name": None
                    if concept is None
                    else concept.canonical_name,
                    "definition": None if concept is None else concept.definition,
                }
            )
        return hits


def _claim_concept_id(claim: Claim) -> str | None:
    for candidate in (claim.output_concept, claim.target_concept, *claim.concepts):
        if candidate:
            return str(candidate)
    return None


def _claim_store(
    conn: Connection, claims: Sequence[Claim]
) -> SidecarClaimEmbeddingStore:
    return SidecarClaimEmbeddingStore(conn, claims, _rowids(conn, "claim", "claim_id"))


def _concept_store(
    conn: Connection, concepts: Sequence[Concept]
) -> SidecarConceptEmbeddingStore:
    return SidecarConceptEmbeddingStore(
        conn, concepts, _rowids(conn, "concept", "concept_id")
    )


def embed_claims(
    conn: Connection,
    claims: Sequence[Claim],
    model_name: str,
    claim_ids: Sequence[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, int]:
    """Generate and store claim embeddings via the generic heuristic layer."""

    return embed_entities(
        _claim_store(conn, claims), model_name, claim_ids, batch_size, on_progress
    )


def embed_concepts(
    conn: Connection,
    concepts: Sequence[Concept],
    model_name: str,
    concept_ids: Sequence[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, int]:
    """Generate and store concept embeddings via the generic heuristic layer."""

    return embed_entities(
        _concept_store(conn, concepts), model_name, concept_ids, batch_size, on_progress
    )


def find_similar_claims(
    conn: Connection,
    claims: Sequence[Claim],
    claim_id: str,
    model_name: str,
    top_k: int = 10,
) -> list[ClaimSimilarityHit]:
    """Top-k claims nearest ``claim_id`` under ``model_name`` (honest-empty)."""

    try:
        rows = find_similar_entities(
            _claim_store(conn, claims), claim_id, model_name, top_k
        )
    except ValueError:
        return []
    return [ClaimSimilarityHit.from_mapping(row) for row in rows]


def find_similar_concepts(
    conn: Connection,
    concepts: Sequence[Concept],
    concept_id: str,
    model_name: str,
    top_k: int = 10,
) -> list[ConceptSimilarityHit]:
    """Top-k concepts nearest ``concept_id`` under ``model_name`` (honest-empty)."""

    try:
        rows = find_similar_entities(
            _concept_store(conn, concepts), concept_id, model_name, top_k
        )
    except ValueError:
        return []
    return [ConceptSimilarityHit.from_mapping(row) for row in rows]


def find_similar_claims_agree(
    conn: Connection,
    claims: Sequence[Claim],
    claim_id: str,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Claims near ``claim_id`` under *every* registered model (multi-model agree)."""

    return find_similar_agree_generic(
        _claim_store(conn, claims), claim_id, get_registered_models(conn), top_k
    )


def find_similar_claims_disagree(
    conn: Connection,
    claims: Sequence[Claim],
    claim_id: str,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Claims near ``claim_id`` under some models but not others (model disagree)."""

    return find_similar_disagree_generic(
        _claim_store(conn, claims), claim_id, get_registered_models(conn), top_k
    )


def embed_claims_at(
    path: Path,
    claims: Sequence[Claim],
    model_name: str,
    claim_ids: Sequence[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, int]:
    """Open a writable vec connection to ``path`` and embed claims into it."""

    with embedding_connection(path, readonly=False) as conn:
        ensure_embedding_tables(conn)
        return embed_claims(
            conn, claims, model_name, claim_ids, batch_size, on_progress
        )


def embed_concepts_at(
    path: Path,
    concepts: Sequence[Concept],
    model_name: str,
    concept_ids: Sequence[str] | None = None,
    batch_size: int = 64,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, int]:
    """Open a writable vec connection to ``path`` and embed concepts into it."""

    with embedding_connection(path, readonly=False) as conn:
        ensure_embedding_tables(conn)
        return embed_concepts(
            conn, concepts, model_name, concept_ids, batch_size, on_progress
        )


def _resolve_model_name(conn: Connection, model_name: str | None) -> str | None:
    if model_name is not None:
        return model_name
    models = get_registered_models(conn)
    if not models:
        return None
    return str(models[0]["model_name"])


def world_similar_claims(
    path: Path,
    claims: Sequence[Claim],
    claim_id: str,
    model_name: str | None = None,
    top_k: int = 10,
) -> list[ClaimSimilarityHit]:
    """Embedding-nearest claims, or ``[]`` when no index/model/extra is present."""

    try:
        with embedding_connection(path, readonly=True) as conn:
            resolved = _resolve_model_name(conn, model_name)
            if resolved is None:
                return []
            return find_similar_claims(conn, claims, claim_id, resolved, top_k)
    except ImportError:
        return []


def world_similar_concepts(
    path: Path,
    concepts: Sequence[Concept],
    concept_id: str,
    model_name: str | None = None,
    top_k: int = 10,
) -> list[ConceptSimilarityHit]:
    """Embedding-nearest concepts, or ``[]`` when no index/model/extra is present."""

    try:
        with embedding_connection(path, readonly=True) as conn:
            resolved = _resolve_model_name(conn, model_name)
            if resolved is None:
                return []
            return find_similar_concepts(conn, concepts, concept_id, resolved, top_k)
    except ImportError:
        return []


__all__ = [
    "CLAIM_VEC_CACHE",
    "CONCEPT_VEC_CACHE",
    "EMBEDDING_CACHES",
    "SidecarClaimEmbeddingStore",
    "SidecarConceptEmbeddingStore",
    "embed_claims",
    "embed_claims_at",
    "embed_concepts",
    "embed_concepts_at",
    "embedding_connection",
    "ensure_embedding_tables",
    "find_similar_claims",
    "find_similar_claims_agree",
    "find_similar_claims_disagree",
    "find_similar_concepts",
    "get_registered_models",
    "world_similar_claims",
    "world_similar_concepts",
]
